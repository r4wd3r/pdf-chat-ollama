"""PDF text extraction and chunking module."""

import logging
from pathlib import Path
from typing import Dict, List, Tuple

import pdfplumber
import tiktoken

from config import CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Handles PDF text extraction and intelligent chunking."""

    def __init__(self) -> None:
        """Initialize the PDF processor with tokenizer."""
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"Failed to load tiktoken: {e}")
            self.tokenizer = None

    def extract_text_from_pdf(self, pdf_path: Path) -> List[Dict[str, str]]:
        """Extract text from PDF with page-level metadata.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            List of dictionaries containing text and metadata for each page.

        Raises:
            FileNotFoundError: If the PDF file doesn't exist.
            Exception: If PDF processing fails.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        pages = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text and text.strip():
                        pages.append({
                            "text": text.strip(),
                            "page_number": page_num,
                            "filename": pdf_path.name,
                            "filepath": str(pdf_path)
                        })
        except Exception as e:
            raise Exception(f"Failed to process PDF {pdf_path}: {e}")

        logger.info(f"Extracted {len(pages)} pages from {pdf_path.name}")
        return pages

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken or fallback to word count.

        Args:
            text: Text to count tokens for.

        Returns:
            Number of tokens in the text.
        """
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        # Fallback: approximate 1 token = 0.75 words
        return int(len(text.split()) * 1.33)

    def chunk_text(
        self, 
        text: str, 
        metadata: Dict[str, str],
        chunk_size: int = CHUNK_SIZE,
        overlap: int = CHUNK_OVERLAP
    ) -> List[Dict[str, str]]:
        """Split text into overlapping chunks.

        Args:
            text: Text to chunk.
            metadata: Metadata to include with each chunk.
            chunk_size: Maximum tokens per chunk.
            overlap: Number of tokens to overlap between chunks.

        Returns:
            List of text chunks with metadata.
        """
        if not text.strip():
            return []

        # Split by sentences first for better chunking
        sentences = self._split_into_sentences(text)
        chunks = []
        current_chunk = ""
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            
            # If adding this sentence would exceed chunk size
            if current_tokens + sentence_tokens > chunk_size and current_chunk:
                # Save current chunk
                chunks.append({
                    "text": current_chunk.strip(),
                    "tokens": current_tokens,
                    **metadata
                })
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk, overlap)
                current_chunk = overlap_text + " " + sentence
                current_tokens = self.count_tokens(current_chunk)
            else:
                current_chunk += " " + sentence if current_chunk else sentence
                current_tokens += sentence_tokens

        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                "text": current_chunk.strip(),
                "tokens": current_tokens,
                **metadata
            })

        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using simple heuristics.

        Args:
            text: Text to split.

        Returns:
            List of sentences.
        """
        import re
        
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _get_overlap_text(self, text: str, overlap_tokens: int) -> str:
        """Get the last N tokens from text for overlap.

        Args:
            text: Text to extract overlap from.
            overlap_tokens: Number of tokens to extract.

        Returns:
            Overlap text.
        """
        if not text or overlap_tokens <= 0:
            return ""

        words = text.split()
        if not words:
            return ""

        # Approximate tokens (fallback if no tokenizer)
        if self.tokenizer:
            tokens = self.tokenizer.encode(text)
            if len(tokens) <= overlap_tokens:
                return text
            
            # Find word boundary for overlap
            overlap_text = ""
            for word in reversed(words):
                test_text = word + " " + overlap_text
                if self.count_tokens(test_text) > overlap_tokens:
                    break
                overlap_text = test_text
            return overlap_text.strip()
        else:
            # Fallback: use word count
            overlap_words = int(overlap_tokens * 0.75)  # Approximate
            return " ".join(words[-overlap_words:])

    def process_pdf(self, pdf_path: Path) -> List[Dict[str, str]]:
        """Process a PDF file and return chunked text.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            List of text chunks with metadata.
        """
        pages = self.extract_text_from_pdf(pdf_path)
        all_chunks = []

        for page in pages:
            chunks = self.chunk_text(
                page["text"], 
                {
                    "page_number": page["page_number"],
                    "filename": page["filename"],
                    "filepath": page["filepath"]
                }
            )
            all_chunks.extend(chunks)

        logger.info(f"Created {len(all_chunks)} chunks from {pdf_path.name}")
        return all_chunks
