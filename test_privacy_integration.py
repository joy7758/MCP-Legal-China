import unittest
import json
import asyncio
from unittest.mock import MagicMock
from privacy_middleware import PrivacyPreservingMAE

# Mocking mcp modules to allow testing without installation
import sys

# Create a mock object for the mcp module and submodules
mock_mcp = MagicMock()
mock_mcp.server.Server = MagicMock
mock_mcp.types.Tool = MagicMock
mock_mcp.types.TextContent = MagicMock
mock_mcp.types.ImageContent = MagicMock
mock_mcp.types.EmbeddedResource = MagicMock
mock_mcp.types.Resource = MagicMock
mock_mcp.types.Prompt = MagicMock
mock_mcp.types.PromptMessage = MagicMock
mock_mcp.types.GetPromptResult = MagicMock
mock_mcp.server.stdio.stdio_server = MagicMock

# Define a mock decorator generator that returns a decorator
def mock_decorator_generator(*args, **kwargs):
    def decorator(func):
        return func
    return decorator

# Configure the mock server instance to return the mock decorator generator
mock_server_instance = MagicMock()
mock_server_instance.list_tools = MagicMock(side_effect=mock_decorator_generator)
mock_server_instance.call_tool = MagicMock(side_effect=mock_decorator_generator)
mock_server_instance.list_resources = MagicMock(side_effect=mock_decorator_generator)
mock_server_instance.read_resource = MagicMock(side_effect=mock_decorator_generator)
mock_server_instance.list_prompts = MagicMock(side_effect=mock_decorator_generator)
mock_server_instance.get_prompt = MagicMock(side_effect=mock_decorator_generator)

# Make Server() return our configured mock instance
mock_mcp.server.Server.return_value = mock_server_instance

sys.modules['mcp'] = mock_mcp
sys.modules['mcp.server'] = mock_mcp.server
sys.modules['mcp.server.stdio'] = mock_mcp.server.stdio
sys.modules['mcp.types'] = mock_mcp.types

# Now we can safely import server
from server import LegalCNServer

class TestPrivacyIntegration(unittest.TestCase):
    def setUp(self):
        # Patch Server before instantiating LegalCNServer
        patcher = unittest.mock.patch('server.Server')
        self.MockServer = patcher.start()
        self.addCleanup(patcher.stop)

        # Patch load_dotenv to avoid errors
        with unittest.mock.patch('server.load_dotenv'):
            self.server = LegalCNServer()

    def test_middleware_masking(self):
        middleware = PrivacyPreservingMAE()
        
        # Test Phone
        text = "Contact: 13812345678"
        masked = middleware.mask_sensitive_data(text)
        self.assertEqual(masked, "Contact: 138****5678")
        
        # Test ID Card
        text = "ID: 110101199001011234"
        masked = middleware.mask_sensitive_data(text)
        self.assertEqual(masked, "ID: 110101********1234")
        
        # Test Account
        text = "Account: 6222021001112223333"
        masked = middleware.mask_sensitive_data(text)
        self.assertEqual(masked, "Account: **** 3333")

        # Test Email
        text = "Email: alice@example.com"
        masked = middleware.mask_sensitive_data(text)
        self.assertEqual(masked, "Email: a***@example.com")
        
    def test_elicitation_check(self):
        middleware = PrivacyPreservingMAE()
        
        # Safe args
        args = {"contract_text": "Normal contract"}
        self.assertIsNone(middleware.check_elicitation_requirement(args))
        
        # Sensitive args
        args = {"medical_record": "Patient info"}
        result = middleware.check_elicitation_requirement(args)
        self.assertIsNotNone(result)
        self.assertIn("medical_record", result)

    def test_metadata_injection(self):
        middleware = PrivacyPreservingMAE()
        data = {"result": "ok"}
        processed = middleware.inject_compliance_metadata(data)
        
        self.assertIn("metadata", processed)
        self.assertIn("gb_45438_compliance", processed["metadata"])
        self.assertEqual(processed["metadata"]["gb_45438_compliance"]["model_version"], "Legal-CN-v0.2.0")

    def test_server_has_middleware(self):
        self.assertTrue(hasattr(self.server, 'privacy_middleware'))
        self.assertIsInstance(self.server.privacy_middleware, PrivacyPreservingMAE)

if __name__ == '__main__':
    unittest.main()
