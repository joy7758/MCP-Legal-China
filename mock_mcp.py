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
            # In a real scenario, this would register the handler.
            # Since we are mocking and the handler is async, we shouldn't execute it here
            # if we can't await it. However, the original mock implementation tried to execute it.
            # Let's just store the function itself or a dummy list if needed for inspection.
            # But the original code did `self.tools = func()`, which caused the warning because func is async.
            # We'll just store the function for now or do nothing, as the tests don't seem to rely on self.tools being populated immediately.
            # If tests rely on self.tools, we'd need to await it, but we can't await in synchronous __init__.
            # So we'll just return the function.
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
