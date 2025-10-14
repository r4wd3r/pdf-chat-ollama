# PDF Chat with Ollama

A Python CLI application that allows you to upload PDF documents and chat with them using Ollama's local AI models. The application uses ChromaDB for vector storage and semantic search to provide intelligent answers based on your documents.

## Features

- **PDF Processing**: Upload and process multiple PDF documents with accurate text extraction
- **Semantic Search**: Intelligent search across all documents using vector embeddings
- **Local AI**: Chat with your documents using Ollama's Mixtral model (no data leaves your machine)
- **Persistent History**: Chat sessions are saved and can be resumed later
- **Source Citations**: Answers include references to the source documents and page numbers
- **Beautiful CLI**: Rich terminal interface with progress indicators and formatted output

## Prerequisites

1. **Ollama**: Install and run Ollama on your system
   ```bash
   # Install Ollama (macOS/Linux)
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Or download from https://ollama.ai
   ```

2. **Python 3.8+**: Ensure you have Python 3.8 or higher installed

3. **Required Models**: Pull the required Ollama models
   ```bash
   # Pull Mixtral for chat
   ollama pull mixtral
   
   # Pull embedding model
   ollama pull nomic-embed-text
   ```

## Installation

1. **Clone or download** this repository
   ```bash
   git clone <repository-url>
   cd pdf-chat-ollama
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify Ollama is running**
   ```bash
   ollama list
   ```

## Usage

### Basic Usage

Start the application:
```bash
python main.py
```

### Command Line Options

You can also use command line options for quick access:

```bash
# Upload PDFs and start chat immediately
python main.py --upload document1.pdf document2.pdf --chat

# Load a specific session
python main.py --session 20241201_143022

# Upload PDFs only
python main.py --upload document1.pdf document2.pdf
```

### Interactive Commands

Once in the application, you can use these commands:

- **`upload <pdf_files>`** - Upload one or more PDF files
  ```
  upload document1.pdf document2.pdf
  ```

- **`chat`** - Start an interactive chat session
  ```
  chat
  ```

- **`sessions`** - List all chat sessions
  ```
  sessions
  ```

- **`load <session_id>`** - Load a specific chat session
  ```
  load 20241201_143022
  ```

- **`stats`** - Show document and system statistics
  ```
  stats
  ```

- **`clear`** - Clear all documents and chat history
  ```
  clear
  ```

- **`help`** - Show help information
  ```
  help
  ```

- **`quit`** - Exit the application
  ```
  quit
  ```

## Example Workflow

1. **Start the application**
   ```bash
   python main.py
   ```

2. **Upload PDF documents**
   ```
   pdf-chat-ollama> upload research_paper.pdf manual.pdf
   ```

3. **Start chatting**
   ```
   pdf-chat-ollama> chat
   Started new chat session: 20241201_143022
   Type 'exit' to end the chat session.

   You: What are the main findings in the research paper?
   Assistant: Based on the research paper, the main findings include...
   
   Sources:
     1. research_paper.pdf (Page 15)
     2. research_paper.pdf (Page 23)
   ```

4. **Exit chat and continue later**
   ```
   You: exit
   pdf-chat-ollama> sessions
   ```

## Configuration

The application uses a configuration file (`config.py`) with the following settings:

- **Models**: Chat model (Mixtral) and embedding model (nomic-embed-text)
- **Chunking**: Text chunk size (1000 tokens) and overlap (128 tokens)
- **Context**: Maximum number of context chunks (5)
- **Storage**: Data directory location (`~/.pdf-chat-ollama/`)

You can modify these settings by editing `config.py`.

## Data Storage

The application stores data in your home directory:

- **Vector Database**: `~/.pdf-chat-ollama/chroma_db/`
- **Chat History**: `~/.pdf-chat-ollama/chat_history.json`

## Troubleshooting

### Common Issues

1. **"Error connecting to Ollama"**
   - Ensure Ollama is running: `ollama serve`
   - Check if models are installed: `ollama list`

2. **"No text found in PDF"**
   - Some PDFs may be image-based or have text extraction issues
   - Try a different PDF or check if the PDF contains selectable text

3. **"Embedding generation failed"**
   - Ensure the embedding model is installed: `ollama pull nomic-embed-text`
   - Check Ollama service status

4. **Import errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version (3.8+ required)

### Performance Tips

- **Large PDFs**: The application processes PDFs in chunks for better performance
- **Memory Usage**: Vector embeddings are stored locally and may use significant memory for large document collections
- **First Run**: Initial setup may take longer as models are downloaded and initialized

## Development

### Project Structure

```
pdf-chat-ollama/
├── main.py              # CLI interface
├── config.py            # Configuration settings
├── pdf_processor.py     # PDF text extraction and chunking
├── vector_store.py      # ChromaDB operations
├── chat_engine.py       # Ollama chat logic
├── history_manager.py   # Conversation persistence
├── requirements.txt     # Dependencies
└── README.md           # This file
```

### Adding New Features

The application is modular and can be extended:

- **New Models**: Modify `config.py` to use different Ollama models
- **Custom Chunking**: Extend `PDFProcessor` for different text processing strategies
- **Additional Storage**: Implement new storage backends in `VectorStore`
- **UI Enhancements**: Extend the CLI interface in `main.py`

## License

This project is open source. Feel free to modify and distribute according to your needs.

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## Support

If you encounter issues or have questions:

1. Check the troubleshooting section above
2. Review the logs for error messages
3. Ensure all prerequisites are properly installed
4. Verify Ollama models are available and accessible
