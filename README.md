> ⚠️ **Warning: This project is under development.**

# biolink-mcp

MCP (Model Context Protocol) server for Monarch Biolink API.

This server implements the Model Context Protocol (MCP) for the Monarch Initiative's Biolink API, providing a standardized interface for accessing a comprehensive biomedical knowledge graph. MCP enables AI assistants and agents to query this data through structured interfaces.

## About MCP (Model Context Protocol)

MCP is a protocol that bridges the gap between AI systems and specialized domain knowledge. It enables:

- **Structured Access**: Direct connection to authoritative biomedical data.
- **Natural Language Queries**: Simplified interaction with specialized databases.
- **AI Integration**: Seamless integration with AI assistants and agents.

## Quick Start

### Installing uv

If you don't have `uv` installed, you can install it with:

```bash
# Download and install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

### Running the server

To run the server, you can use `uvx`, which will handle the installation of the package and its dependencies.

```bash
# Run the server in stdio mode
uvx biolink-mcp-stdio
```

Or if you have cloned the repository:

```bash
# Install dependencies
uv sync

# Run the server
uv run biolink-mcp-stdio
```

## Development

### Setup

1.  Clone the repository.
2.  Install dependencies: `uv sync`

### Running Tests

```bash
uv run pytest
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

