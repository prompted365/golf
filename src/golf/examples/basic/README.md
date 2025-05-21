# {{project_name}}

A GolfMCP project that provides MCP-compatible tools, resources, and prompts.

## Getting Started

This project is built with [GolfMCP](https://github.com/yourusername/golfmcp), a Python framework for building MCP servers with zero boilerplate.

To start the development server with hot reload:

```bash
golf dev
```

This will watch for file changes and automatically reload the server.

## Project Structure

- `tools/` - Tool implementations (functions an LLM can call)
- `resources/` - Resource implementations (data an LLM can read)
- `prompts/` - Prompt templates (conversations an LLM can use)
- `golf.json` - Configuration file with settings like telemetry and transport

## Adding New Components

### Tools

To add a new tool, create a Python file in the `tools/` directory:

```python
# tools/my_tool.py
from pydantic import BaseModel
from fastmcp import Context

class Input(BaseModel):
    param1: str
    param2: int = 42

class Output(BaseModel):
    result: str

async def run(input: Input, ctx: Context) -> Output:
    """Description of what my tool does."""
    await ctx.info(f"Processing {input.param1}...")
    return MyOutput(result=f"Processed {input.param1} with {input.param2}")
```

### Resources

To add a new resource, create a Python file in the `resources/` directory:

```python
# resources/my_data.py
resource_uri = "data://my-data"

async def run() -> dict:
    """Description of the resource."""
    return {
        "title": "My Data",
        "content": "Some valuable information"
    }
```

### Sharing Functionality with common.py

For directories with multiple related components (like `tools/payments/` or `resources/weather/`), 
use a `common.py` file to share functionality:

```python
# tools/payments/common.py
class PaymentClient:
    """Shared payment client implementation."""
    # Implementation details...

# Create a shared client instance
payment_client = PaymentClient()
```

Then import and use the shared functionality in your components:

```python
# tools/payments/charge.py
from .common import payment_client

async def run(input):
    result = await payment_client.create_charge(...)
    # Rest of implementation...
```

This pattern helps organize shared code and makes it easier to build and maintain your project.

## Telemetry

This project includes OpenTelemetry integration for tracing server requests:

```json
// golf.json
{
  "telemetry": true,
  "telemetry_exporter": "console"  // or "otlp_http"
}
```

You can configure it with environment variables:
- `OTEL_SERVICE_NAME`: Set service name (defaults to app name)
- `OTEL_TRACES_EXPORTER`: Exporter type ("console" or "otlp_http")
- `OTEL_EXPORTER_OTLP_ENDPOINT`: OTLP exporter endpoint URL

## Deployment

To build the project for deployment:

```bash
golf build
```

This creates a standalone FastMCP application in the `dist/` directory. 