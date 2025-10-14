"""Main CLI interface for PDF Chat with Ollama."""

import logging
import sys
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from pdf_chat_ollama import APP_NAME, ChatEngine, HistoryManager, PDFProcessor, VectorStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

console = Console()


class PDFChatCLI:
    """Main CLI application for PDF Chat."""

    def __init__(self) -> None:
        """Initialize the CLI application."""
        self.console = console
        self.pdf_processor = PDFProcessor()
        self.vector_store = VectorStore()
        self.history_manager = HistoryManager()
        self.chat_engine = ChatEngine(self.vector_store, self.history_manager)

    def _check_ollama_connection(self) -> bool:
        """Check if Ollama is running and accessible.

        Returns:
            True if Ollama is accessible, False otherwise.
        """
        try:
            import ollama
            models = ollama.list()
            return True
        except Exception as e:
            self.console.print(f"[red]Error connecting to Ollama: {e}[/red]")
            self.console.print("[yellow]Please ensure Ollama is running and accessible.[/yellow]")
            return False

    def _display_welcome(self) -> None:
        """Display welcome message."""
        welcome_text = f"""
[bold blue]Welcome to {APP_NAME}![/bold blue]

This application allows you to:
• Upload and process PDF documents
• Chat with your documents using Ollama
• Search across multiple PDFs intelligently
• Maintain persistent chat history

Type 'help' for available commands or 'quit' to exit.
        """
        self.console.print(Panel(welcome_text, title="PDF Chat with Ollama"))

    def _display_help(self) -> None:
        """Display help information."""
        help_text = """
[bold]Available Commands:[/bold]

[bold green]upload <pdf_files>[/bold green]     Upload one or more PDF files
[bold green]chat[/bold green]                  Start interactive chat session
[bold green]sessions[/bold green]              List all chat sessions
[bold green]load <session_id>[/bold green]     Load a specific chat session
[bold green]stats[/bold green]                 Show document statistics
[bold green]clear[/bold green]                 Clear all documents and history
[bold green]help[/bold green]                  Show this help message
[bold green]quit[/bold green]                  Exit the application

[bold]Examples:[/bold]
• upload document1.pdf document2.pdf
• chat
• load 20241201_143022
• stats
        """
        self.console.print(Panel(help_text, title="Help"))

    def upload_pdfs(self, pdf_paths: List[str]) -> None:
        """Upload and process PDF files.

        Args:
            pdf_paths: List of PDF file paths.
        """
        if not pdf_paths:
            self.console.print("[red]No PDF files specified.[/red]")
            return

        valid_paths = []
        for path_str in pdf_paths:
            path = Path(path_str)
            if not path.exists():
                self.console.print(f"[red]File not found: {path}[/red]")
            elif not path.suffix.lower() == '.pdf':
                self.console.print(f"[red]Not a PDF file: {path}[/red]")
            else:
                valid_paths.append(path)

        if not valid_paths:
            self.console.print("[red]No valid PDF files to process.[/red]")
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            for pdf_path in valid_paths:
                task = progress.add_task(f"Processing {pdf_path.name}...", total=None)
                
                try:
                    # Process PDF
                    chunks = self.pdf_processor.process_pdf(pdf_path)
                    
                    if chunks:
                        # Add to vector store
                        self.vector_store.add_documents(chunks)
                        progress.update(task, description=f"✅ Processed {pdf_path.name} ({len(chunks)} chunks)")
                    else:
                        progress.update(task, description=f"⚠️  No text found in {pdf_path.name}")
                        
                except Exception as e:
                    progress.update(task, description=f"❌ Failed to process {pdf_path.name}: {e}")
                    logger.error(f"Failed to process {pdf_path}: {e}")

        self.console.print("[green]PDF upload completed![/green]")

    def start_chat(self) -> None:
        """Start interactive chat session."""
        if not self._check_ollama_connection():
            return

        # Check if we have any documents
        stats = self.vector_store.get_collection_stats()
        if stats["total_chunks"] == 0:
            self.console.print("[yellow]No documents uploaded. Please upload PDFs first.[/yellow]")
            return

        # Start new session
        session_id = self.chat_engine.start_session()
        self.console.print(f"[green]Started new chat session: {session_id}[/green]")
        self.console.print("[dim]Type 'exit' to end the chat session.[/dim]\n")

        while True:
            try:
                user_input = self.console.input("[bold blue]You: [/bold blue]")
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    break
                
                if not user_input.strip():
                    continue

                # Process the query
                with self.console.status("[bold green]Thinking...", spinner="dots"):
                    response = self.chat_engine.chat(user_input)

                # Display response
                self.console.print(f"\n[bold green]Assistant:[/bold green] {response['response']}")
                
                # Display sources if available
                if response.get('sources'):
                    self.console.print("\n[dim]Sources:[/dim]")
                    for i, source in enumerate(response['sources'], 1):
                        self.console.print(f"  {i}. {source['filename']} (Page {source['page_number']})")
                
                self.console.print()  # Empty line for readability

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Chat session interrupted.[/yellow]")
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
                logger.error(f"Chat error: {e}")

    def list_sessions(self) -> None:
        """List all chat sessions."""
        sessions = self.history_manager.get_recent_sessions(20)
        
        if not sessions:
            self.console.print("[yellow]No chat sessions found.[/yellow]")
            return

        table = Table(title="Chat Sessions")
        table.add_column("Session ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Created", style="green")
        table.add_column("Messages", style="yellow")

        for session in sessions:
            summary = self.history_manager.get_session_summary(session["id"])
            if summary:
                table.add_row(
                    summary["id"],
                    summary["name"],
                    summary["created_at"][:19],  # Remove microseconds
                    str(summary["total_messages"])
                )

        self.console.print(table)

    def load_session(self, session_id: str) -> None:
        """Load and display a specific chat session.

        Args:
            session_id: ID of the session to load.
        """
        if self.chat_engine.load_session(session_id):
            self.console.print(f"[green]Loaded session: {session_id}[/green]")
            
            # Display session history
            messages = self.chat_engine.get_session_history()
            if messages:
                self.console.print("\n[bold]Session History:[/bold]")
                for msg in messages[-10:]:  # Show last 10 messages
                    role_color = "blue" if msg["role"] == "user" else "green"
                    self.console.print(f"[{role_color}]{msg['role'].title()}:[/{role_color}] {msg['content'][:200]}...")
            else:
                self.console.print("[yellow]No messages in this session.[/yellow]")
        else:
            self.console.print(f"[red]Session not found: {session_id}[/red]")

    def show_stats(self) -> None:
        """Show document and system statistics."""
        stats = self.vector_store.get_collection_stats()
        sessions = self.history_manager.get_all_sessions()
        
        table = Table(title="System Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Document Chunks", str(stats["total_chunks"]))
        table.add_row("Total Chat Sessions", str(len(sessions)))
        table.add_row("Vector Database", str(self.vector_store.collection_name))
        
        if sessions:
            total_messages = sum(
                len(s.get("messages", [])) for s in sessions
            )
            table.add_row("Total Messages", str(total_messages))
        
        self.console.print(table)

    def clear_data(self) -> None:
        """Clear all documents and chat history."""
        if click.confirm("Are you sure you want to clear all data? This cannot be undone."):
            try:
                self.vector_store.clear_collection()
                self.history_manager.clear_all_history()
                self.console.print("[green]All data cleared successfully.[/green]")
            except Exception as e:
                self.console.print(f"[red]Error clearing data: {e}[/red]")
                logger.error(f"Error clearing data: {e}")

    def run(self) -> None:
        """Run the main CLI loop."""
        self._display_welcome()
        
        while True:
            try:
                command = self.console.input(f"\n[bold cyan]{APP_NAME}[/bold cyan]> ").strip()
                
                if not command:
                    continue
                
                parts = command.split()
                cmd = parts[0].lower()
                args = parts[1:]
                
                if cmd == 'help':
                    self._display_help()
                elif cmd == 'upload':
                    self.upload_pdfs(args)
                elif cmd == 'chat':
                    self.start_chat()
                elif cmd == 'sessions':
                    self.list_sessions()
                elif cmd == 'load' and args:
                    self.load_session(args[0])
                elif cmd == 'stats':
                    self.show_stats()
                elif cmd == 'clear':
                    self.clear_data()
                elif cmd in ['quit', 'exit', 'q']:
                    self.console.print("[yellow]Goodbye![/yellow]")
                    break
                else:
                    self.console.print(f"[red]Unknown command: {cmd}[/red]")
                    self.console.print("Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Goodbye![/yellow]")
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
                logger.error(f"CLI error: {e}")


@click.command()
@click.option('--upload', multiple=True, help='PDF files to upload')
@click.option('--chat', is_flag=True, help='Start chat session immediately')
@click.option('--session', help='Load specific session ID')
def main(upload: tuple, chat: bool, session: Optional[str]) -> None:
    """PDF Chat with Ollama - Chat with your PDF documents using local AI."""
    
    cli = PDFChatCLI()
    
    # Handle command line arguments
    if upload:
        cli.upload_pdfs(list(upload))
    
    if session:
        cli.load_session(session)
    
    if chat:
        cli.start_chat()
    else:
        cli.run()


if __name__ == "__main__":
    main()
