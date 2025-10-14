"""Basic usage example for PDF Chat with Ollama."""

from pdf_chat_ollama import PDFProcessor, VectorStore, ChatEngine, HistoryManager


def main():
    """Demonstrate basic usage of the PDF Chat library."""
    # Initialize components
    pdf_processor = PDFProcessor()
    vector_store = VectorStore()
    history_manager = HistoryManager()
    chat_engine = ChatEngine(vector_store, history_manager)
    
    # Process a PDF file
    print("Processing PDF...")
    chunks = pdf_processor.process_pdf("example.pdf")
    
    if chunks:
        # Add to vector store
        vector_store.add_documents(chunks)
        print(f"Added {len(chunks)} chunks to vector store")
        
        # Start a chat session
        session_id = chat_engine.start_session()
        print(f"Started session: {session_id}")
        
        # Chat with the document
        response = chat_engine.chat("What is this document about?")
        print(f"Response: {response['response']}")
        
        if response.get('sources'):
            print("Sources:")
            for source in response['sources']:
                print(f"  - {source['filename']} (Page {source['page_number']})")
    else:
        print("No text found in PDF")


if __name__ == "__main__":
    main()
