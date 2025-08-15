# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kiro2API is an OpenAI-compatible API service that provides access to Claude Sonnet 4 via AWS CodeWhisperer. The service acts as a translation layer between OpenAI's API format and AWS CodeWhisperer's event stream protocol.

## Architecture

### Core Components

- **Main Application** (`src/app.py`): FastAPI-based web service with comprehensive request/response handling
- **Authentication**: Automatic token reading from `~/.aws/sso/cache/kiro-auth-token.json` with refresh capability
- **Stream Processing**: Dual parser system for AWS event streams and bracket-format tool calls
- **Tool Call Support**: Advanced parsing for both XML and bracket-format tool calls with deduplication

### Key Features

- OpenAI-compatible `/v1/chat/completions` and `/v1/models` endpoints
- Streaming and non-streaming response modes
- Image support via base64 data URIs
- Automatic token refresh when expired
- Tool call parsing and conversion between formats
- Comprehensive error handling and logging

## Development Commands

### Installation and Setup
```bash
# Install in development mode
uv pip install -e .

# Run the service
ki2

# Alternative: Direct uvicorn
uvicorn src.app:app --host 0.0.0.0 --port 8989 --reload
```

### Testing the API
```bash
# Health check
curl http://localhost:8989/health

# List models
curl -H "Authorization: Bearer ki2api-key-2024" http://localhost:8989/v1/models

# Chat completion
curl -X POST http://localhost:8989/v1/chat/completions \n  -H "Authorization: Bearer ki2api-key-2024" \n  -H "Content-Type: application/json" \n  -d '{"model": "claude-sonnet-4-20250514", "messages": [{"role": "user", "content": "Hello"}