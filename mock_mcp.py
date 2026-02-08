from typing import Any, List, Optional, Dict
from dataclasses import dataclass

# Mock MCP types
@dataclass
class Tool:
    name: str
    description: str
    inputSchema: Dict[str, Any]

@dataclass
class TextContent:
    type: str
    text: str

@dataclass
class ImageContent:
    type: str
    data: str
    mimeType: str

@dataclass
class EmbeddedResource:
    type: str
    resource: Any

@dataclass
class Resource:
    uri: str
    name: str
    description: str
    mimeType: str

@dataclass
class Prompt:
    name: str
    description: str
    arguments: List[Dict[str, Any]]

@dataclass
class PromptMessage:
    role: str
    content: Any

@dataclass
class GetPromptResult:
    description: str
    messages: List[PromptMessage]

# Mock MCP Server
class Server:
    def __init__(self, name: str):
        self.name = name
        self.tools = []

    def list_tools(self):
        def decorator(func):
            self.tools = func()
            return func
        return decorator

    def call_tool(self):
        def decorator(func):
            return func
        return decorator

    def list_resources(self):
        def decorator(func):
            return func
        return decorator
    
    def read_resource(self):
        def decorator(func):
            return func
        return decorator

    def list_prompts(self):
        def decorator(func):
            return func
        return decorator

    def get_prompt(self):
        def decorator(func):
            return func
        return decorator
    
    def create_initialization_options(self):
        return {}

    async def run(self, read_stream, write_stream, options):
        pass

# Mock stdio_server
class stdio_server:
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def __aenter__(self):
        return (None, None)
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
