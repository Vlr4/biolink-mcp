#!/usr/bin/env python3
"""Biolink MCP Server - An interface for the Biolink API."""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import typer
from fastmcp import FastMCP

# Import Biolink tools
from biolink_mcp.biolink_wrapper import BiolinkTools

# Configuration
DEFAULT_HOST = os.getenv("MCP_HOST", "0.0.0.0")
DEFAULT_PORT = int(os.getenv("MCP_PORT", "3001"))
DEFAULT_TRANSPORT = os.getenv("MCP_TRANSPORT", "streamable-http")
DEFAULT_OUTPUT_DIR = os.getenv("MCP_OUTPUT_DIR", "biothings_output")

class BiolinkMCP(FastMCP):
    """Biolink MCP Server with Biolink API tools."""
    
    def __init__(
        self, 
        name: str = "Biolink MCP Server",
        prefix: str = "biolink_",
        output_dir: Optional[str] = None,
        **kwargs
    ):
        """Initialize the Biolink tools with FastMCP functionality."""
        super().__init__(name=name, **kwargs)
        
        self.prefix = prefix
        self.output_dir = output_dir or DEFAULT_OUTPUT_DIR
        self._register_biolink_tools()
    
    def _register_biolink_tools(self):
        """Register Biolink-specific tools."""
        self.biolink_tools = BiolinkTools(self, self.prefix)
        self.biolink_tools.register_tools()
    
    def run(self, transport: str = "streamable-http", **kwargs):
        """Run the MCP server."""
                
        super().run(transport=transport, **kwargs)
        
        
# Create typer app
app = typer.Typer(help="Biolink MCP Server - An interface for the Biolink API.")

@app.command("run")
def cli_app(
    host: str = typer.Option(DEFAULT_HOST, "--host", help="Host to bind to"),
    port: int = typer.Option(DEFAULT_PORT, "--port", help="Port to bind to"),
    transport: str = typer.Option("streamable-http", "--transport", help="Transport type"),
    output_dir: str = typer.Option(DEFAULT_OUTPUT_DIR, "--output-dir", help="Output directory for local files")
) -> None:
    """Run the MCP server with specified transport."""
    mcp = BiolinkMCP(output_dir=output_dir)
    mcp.run(transport=transport, host=host, port=port)

@app.command("stdio")
def cli_app_stdio(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    output_dir: str = typer.Option(DEFAULT_OUTPUT_DIR, "--output-dir", help="Output directory for local files")
) -> None:
    """Run the MCP server with stdio transport."""
    mcp = BiolinkMCP(output_dir=output_dir)
    mcp.run(transport="stdio")

@app.command("sse")
def cli_app_sse(
    host: str = typer.Option(DEFAULT_HOST, "--host", help="Host to bind to"),
    port: int = typer.Option(DEFAULT_PORT, "--port", help="Port to bind to"),
    output_dir: str = typer.Option(DEFAULT_OUTPUT_DIR, "--output-dir", help="Output directory for local files")
) -> None:
    """Run the MCP server with SSE transport."""
    mcp = BiolinkMCP(output_dir=output_dir)
    mcp.run(transport="sse", host=host, port=port)

if __name__ == "__main__":
    from pycomfort.logging import to_nice_stdout, to_nice_file
    
    to_nice_stdout()
    project_root = Path(__file__).resolve().parents[2]
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    json_log_path = log_dir / "mcp_server.log.json"
    rendered_log_path = log_dir / "mcp_server.log"
    
    to_nice_file(output_file=json_log_path, rendered_file=rendered_log_path)
    app()