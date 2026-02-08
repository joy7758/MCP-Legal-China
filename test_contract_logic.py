import unittest
import json
from unittest.mock import MagicMock
from contract_logic import evaluate_judicial_discretion, resolve_pid_or_value
from legal_resources import LegalResourceProvider
from Logic import calculate_liquidated_damages

class TestContractLogic(unittest.TestCase):

    def setUp(self):
        self.provider = MagicMock(spec=LegalResourceProvider)

    def test_resolve_pid_or_value_raw(self):
        """Test resolving raw values (not PIDs)."""
        self.assertEqual(resolve_pid_or_value(100.0, self.provider), 100.0)
        self.assertEqual(resolve_pid_or_value("some string", self.provider), "some string")
        self.provider.get_resource_by_pid.assert_not_called()

    def test_resolve_pid_or_value_pid_found(self):
        """Test resolving a PID that exists."""
        pid = "legal://pid/12345"
        expected_content = {"amount": 5000.0}
        self.provider.get_resource_by_pid.return_value = expected_content
        
        result = resolve_pid_or_value(pid, self.provider)
        self.assertEqual(result, expected_content)
        self.provider.get_resource_by_pid.assert_called_with(pid)

    def test_resolve_pid_or_value_pid_not_found(self):
        """Test resolving a PID that does not exist."""
        pid = "legal://pid/unknown"
        self.provider.get_resource_by_pid.return_value = None
        
        result = resolve_pid_or_value(pid, self.provider)
        self.assertIsNone(result)

    def test_evaluate_judicial_discretion_raw_inputs(self):
        """Test evaluation with raw numeric inputs."""
        # Loss=10000, Performance=0.5 (w1=0.5), Fault=1.5 (w2=1.5)
        # Gamma = 0.3 * 0.5 * 1.5 = 0.225
        # Penalty = 10000 * (1 + 0.225) = 12250
        
        result = evaluate_judicial_discretion(
            loss_param=10000.0,
            performance_param=0.5,
            fault_param=1.5,
            contract_pid="legal://pid/contract-001",
            resource_provider=self.provider
        )
        
        self.assertIn("evaluation_id", result)
        self.assertEqual(result["contract_pid"], "legal://pid/contract-001")
        self.assertAlmostEqual(result["result"]["suggested_penalty"], 12250.0)
        self.assertAlmostEqual(result["formula"]["components"]["gamma"], 0.225)

    def test_evaluate_judicial_discretion_pid_inputs(self):
        """Test evaluation with PID inputs."""
        loss_pid = "legal://pid/loss-001"
        perf_pid = "legal://pid/perf-001"
        fault_pid = "legal://pid/fault-001"
        
        # Mock provider returns
        def get_resource_side_effect(pid):
            if pid == loss_pid: return {"amount": 10000.0}
            if pid == perf_pid: return {"ratio": 0.5}
            if pid == fault_pid: return {"score": 1.5}
            return None
            
        self.provider.get_resource_by_pid.side_effect = get_resource_side_effect
        
        result = evaluate_judicial_discretion(
            loss_param=loss_pid,
            performance_param=perf_pid,
            fault_param=fault_pid,
            contract_pid="legal://pid/contract-001",
            resource_provider=self.provider
        )
        
        self.assertEqual(result["inputs"]["loss"]["value"], 10000.0)
        self.assertEqual(result["inputs"]["loss"]["source_pid"], loss_pid)
        self.assertAlmostEqual(result["result"]["suggested_penalty"], 12250.0)

    def test_evaluate_judicial_discretion_clamping(self):
        """Test input clamping logic."""
        # Performance 1.5 -> clamped to 1.0 (w1 = 0)
        # Fault 0.5 -> clamped to 1.0 (w2 = 1.0)
        # Gamma = 0.3 * 0 * 1.0 = 0
        # Penalty = 10000 * 1 = 10000
        
        result = evaluate_judicial_discretion(
            loss_param=10000.0,
            performance_param=1.5,
            fault_param=0.5,
            resource_provider=self.provider
        )
        
        self.assertEqual(result["inputs"]["performance"]["value"], 1.0)
        self.assertEqual(result["inputs"]["fault"]["value"], 1.0)
        self.assertEqual(result["result"]["suggested_penalty"], 10000.0)
        self.assertEqual(result["formula"]["components"]["gamma"], 0.0)

if __name__ == '__main__':
    unittest.main()
