<div align="center">

# Golf

**Easiest framework for building MCP servers.**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/golf-mcp/golf/pulls)
[![Support](https://img.shields.io/badge/support-contact%20author-purple.svg)](https://github.com/golf-mcp/golf/issues)
[![PyPI Downloads](https://img.shields.io/pypi/dm/golf-mcp)](https://pypi.org/project/golf-mcp/)

Golf | [Docs](https://docs.golf.dev)
</div>

## Overview

Golf is a **framework** designed to streamline the creation of MCP server applications. It allows developers to define server's capabilities—*tools*, *prompts*, and *resources*—as simple Python files within a conventional directory structure. Golf then automatically discovers, parses, and compiles these components into a runnable FastMCP server, minimizing boilerplate and accelerating development.

With Golf, you can focus on implementing your agent's logic rather than wrestling with server setup and integration complexities. It's built for developers who want a quick, organized way to build powerful MCP servers.

## Quick Start

Get your Golf project up and running in a few simple steps:

### 1. Install Golf

Ensure you have Python (3.10+ recommended) installed. Then, install Golf using pip:

```bash
pip install golf-mcp
```

### 2. Initialize Your Project

Use the Golf CLI to scaffold a new project:

```bash
golf init your-project-name
```
This command creates a new directory (`your-project-name`) with a basic project structure, including example tools, resources, and a `golf.json` configuration file.

### 3. Run the Development Server

Navigate into your new project directory and start the development server:

```bash
cd your-project-name
golf build dev
golf run
```
This will start the FastMCP server, typically on `http://127.0.0.1:3000` (configurable in `golf.json`). The `dev` command includes hot reloading, so changes to your component files will automatically restart the server.

That's it! Your Golf server is running and ready for integration.

## Basic Project Structure

A Golf project initialized with `golf init` will have a structure similar to this:

```
<your-project-name>/
│
├─ golf.json          # Main project configuration
│
├─ tools/             # Directory for tool implementations
│   └─ hello.py       # Example tool
│
├─ resources/         # Directory for resource implementations
│   └─ info.py        # Example resource
│
├─ prompts/           # Directory for prompt templates
│   └─ welcome.py     # Example prompt
│
├─ .env               # Environment variables (e.g., API keys, server port)
└─ pre_build.py       # (Optional) Script for pre-build hooks (e.g., auth setup)
```

-   **`golf.json`**: Configures server name, port, transport, telemetry, and other build settings.
-   **`tools/`**, **`resources/`**, **`prompts/`**: Contain your Python files, each defining a single component. The module docstring of each file serves as the component's description.
-   **`common.py`** (not shown, but can be placed in subdirectories like `tools/payments/common.py`): Used to share code (clients, models, etc.) among components in the same subdirectory.

## Example: Defining a Tool

Creating a new tool is as simple as adding a Python file to the `tools/` directory. For example, `tools/greeter.py`:

```python
# tools/greeter.py
"""A simple tool that greets a user."""
from pydantic import BaseModel

class Input(BaseModel):
    name: str

class Output(BaseModel):
    message: str

async def run(input: Input) -> Output:
    """Generates a personalized greeting."""
    return Output(message=f"Hello, {input.name}!")

# Designate the entry point function (optional if named 'run')
export = run
```
Golf will automatically discover this file, parse the `Input` and `Output` Pydantic models for the schema, and register `greeter.run` as a tool named `greeter`.

## Configuration (`golf.json`)

Key aspects of your Golf server are configured in `golf.json`:

```jsonc
{
  "name": "MyAgentServer",      // FastMCP instance name
  "description": "An awesome agent built with Golf",
  "output_dir": "dist",         // Directory for build artifacts
  "host": "127.0.0.1",           // Server host address
  "port": 3000,                  // Server port
  "transport": "sse",            // 'sse', 'streamable-http', or 'stdio'
  "opentelemetry_enabled": true, // Enable OpenTelemetry
  "opentelemetry_default_exporter": "console"
}
```

## Roadmap

We are actively developing Golf. Here's what's on our current roadmap:


## Documentation

For more information, please visit our official documentation:

[https://docs.golf.dev](https://docs.golf.dev)

<div align="center">
Made with ❤️ in Warsaw, Poland and SF
</div>