import unittest
import asyncio
import json
from unittest.mock import MagicMock, patch
from server import LegalCNServer
from errors import ErrorCode
# from mcp.types import TextContent # Use mock types from server import if mcp not available

class TestRefactorVerification(unittest.TestCase):
    def setUp(self):
        # Patch Server before instantiating LegalCNServer
        patcher = patch('server.Server')
        self.MockServer = patcher.start()
        self.addCleanup(patcher.stop)
        
        # Patch load_dotenv to avoid errors
        patcher_env = patch('server.load_dotenv')
        patcher_env.start()
        self.addCleanup(patcher_env.stop)
        
        self.server = LegalCNServer()
        # Mock privacy middleware to avoid side effects
        # IMPORTANT: We must mock the instance attached to the server, not the class or a new instance,
        # unless we are sure where it comes from.
        # server.py: self.privacy_middleware = PrivacyPreservingMAE()
        # So mocking self.server.privacy_middleware is correct.
        
        # However, the failure suggests: [Elicitation Required] <MagicMock id='4385939216'>
        # This implies check_elicitation_requirement returned a MagicMock instead of None.
        # Ah! default MagicMock return value is a new MagicMock.
        # But we set return_value=None.
        # Maybe the server re-initializes it or something?
        # Or maybe I am mocking it AFTER it's used? No, setUp happens before test.
        
        # Wait, in _handle_call_tool (server.py):
        # elicitation = self.privacy_middleware.check_elicitation_requirement(arguments)
        # if elicitation: raise ElicitationRequiredError(...)
        
        # If mock returns None, if elicitation: is False.
        # Why did it fail?
        # Maybe I mocked it incorrectly in previous attempts or imports are messing up.
        
        # Let's be very explicit.
        self.server.privacy_middleware = MagicMock()
        self.server.privacy_middleware.check_elicitation_requirement.return_value = None
        self.server.privacy_middleware.inject_compliance_metadata.side_effect = lambda x: x
        self.server.privacy_middleware.mask_sensitive_data.side_effect = lambda x: x

    def test_health_check_structure(self):
        """验证 /health 探针返回结构是否包含成熟度和一致性校验"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            self.server._handle_call_tool("health_check", {})
        )
        loop.close()
        
        content = json.loads(result[0].text)
        
        self.assertIn("status", content)
        self.assertIn("checks", content)
        self.assertIn("transcription_maturity", content["checks"])
        self.assertIn("legal_db_consistency", content["checks"])
        self.assertEqual(content["checks"]["transcription_maturity"]["status"], "ok")

    def test_invalid_params_mapping_private_lending(self):
        """验证参数超出法律红线时映射为 -32602 (Invalid params)"""
        arguments = {
            "scenario": "private_lending",
            "rate": 0.20 # 20% > 3.45% * 4 = 13.8%
        }
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Expecting InvalidParamsError which is caught in _handle_call_tool and returned as JSON
        result = loop.run_until_complete(
            self.server._handle_call_tool("calculate_damages", arguments)
        )
        loop.close()
        
        content = json.loads(result[0].text)
        
        self.assertEqual(content["code"], -32602) # ErrorCode.INVALID_PARAMS.value
        self.assertIn("details", content)
        self.assertEqual(content["details"]["risk_level"], "Critical")
        self.assertIn("legal_basis", content["details"])

    def test_db_sync_failure_mapping(self):
        """验证法律数据库同步失败时映射为 -32001 (Internal error)"""
        arguments = {
            "scenario": "private_lending",
            "rate": 0.05,
            "simulate_db_failure": True
        }
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Expecting InternalError
        result = loop.run_until_complete(
            self.server._handle_call_tool("calculate_damages", arguments)
        )
        loop.close()
        
        content = json.loads(result[0].text)
        
        self.assertEqual(content["code"], -32001) # ErrorCode.INTERNAL_ERROR.value
        self.assertIn("数据库同步失败", content["message"])

    def test_causal_trace_id_injection(self):
        """验证 causal_trace_id 被正确注入并记录"""
        arguments = {
            "scenario": "general_contract",
            "actual_loss": 1000
        }
        
        with patch('server.logger') as mock_logger:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            loop.run_until_complete(
                self.server._handle_call_tool("calculate_damages", arguments)
            )
            loop.close()
            
            # Check if logger was called with trace_id
            # 找到包含 "Tool called: calculate_damages" 的调用
            found_call = False
            for call in mock_logger.info.call_args_list:
                args, kwargs = call
                if "Tool called: calculate_damages" in args[0]:
                    if "extra" in kwargs and "trace_id" in kwargs["extra"]:
                        found_call = True
                        break
            
            self.assertTrue(found_call, "trace_id should be logged when tool is called")

if __name__ == '__main__':
    unittest.main()
