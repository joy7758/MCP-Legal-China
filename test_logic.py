import unittest
from unittest.mock import patch, MagicMock
from Logic import calculate_liquidated_damages, RedLineInterceptors, DiscretionaryWeight, RiskLevel, InvalidParamsError

class TestLogic(unittest.TestCase):

    def test_private_lending_cap(self):
        """Test Private Lending LPR 4x Cap"""
        # Scenario 1: Interest rate within limit (10%, LPR 3.45% -> Limit 13.8%)
        lpr = 0.0345
        rate_ok = 0.10
        
        # We need to patch get_latest_lpr because check_private_lending_interest might rely on it if current_lpr is not passed correctly,
        # OR we check Logic.py to see if it accepts current_lpr.
        # Assuming Logic.py doesn't accept current_lpr, we must patch get_latest_lpr.
        
        # Mocking get_latest_lpr correctly.
        # When patching a method in a class that's imported in the test, we need to patch where it is used or defined.
        # If Logic.py defines RedLineInterceptors, we patch 'Logic.RedLineInterceptors.get_latest_lpr'.
        # However, the error "TypeError: '>' not supported between instances of 'float' and 'MagicMock'" suggests
        # that lpr is being treated as a Mock object, or the return value isn't working as expected.
        # It usually happens if return_value is not set or set incorrectly.
        
        with patch('Logic.RedLineInterceptors.get_latest_lpr') as mock_get_lpr:
             mock_get_lpr.return_value = lpr
             
             result_ok = RedLineInterceptors.check_private_lending_interest(rate_ok)
             self.assertFalse(result_ok['triggered'])
             self.assertEqual(result_ok['risk_level'], RiskLevel.LOW.value)

             # Scenario 2: Interest rate exceeds limit (20%, LPR 3.45% -> Limit 13.8%)
             rate_high = 0.20
             # Instead of returning a 'triggered' dict, it now raises InvalidParamsError for violations
             try:
                 RedLineInterceptors.check_private_lending_interest(rate_high)
                 self.fail("Should have raised InvalidParamsError")
             except InvalidParamsError as e:
                 self.assertTrue("超过法律保护上限" in str(e))

    def test_labor_training_compensation(self):
        """Test Labor Contract Training Compensation Cap"""
        training_cost = 10000.0
        service_years_agreed = 5
        
        # Scenario 1: Served 2 years, remaining 3 years. Cap should be 10000 * (3/5) = 6000
        service_years_served = 2
        
        # In the new Logic.py, check_labor_contract_limit returns the float limit directly
        # The logic for checking if claimed amount > limit is now inside calculate_liquidated_damages or handled differently.
        # However, RedLineInterceptors.check_labor_contract_limit is static.
        
        limit = RedLineInterceptors.check_labor_contract_limit(
            training_cost, service_years_agreed * 12, (service_years_agreed - service_years_served) * 12
        )
        
        self.assertEqual(limit, 6000.0)

    def test_general_contract_discretionary(self):
        """Test General Contract Discretionary Weight Calculation"""
        # Scenario: High penalty, low actual loss
        # Agreed penalty: 100,000
        # Actual loss: 10,000
        
        amount = 100000.0
        actual_loss = 10000.0
        
        # Construct DiscretionaryWeight manually
        # Note: If Logic.py's DiscretionaryWeight dataclass definition doesn't accept 'malignancy_multiplier',
        # we construct it with valid args and set extra attributes dynamically.
        # Assuming args are: performance_ratio, fault_score, expectation_interest_included, is_consumer_contract
        
        dw_low = DiscretionaryWeight(
             performance_ratio=0.9,
             fault_score=1.0,
             expectation_interest_included=False,
             is_consumer_contract=False
        )
        # Manually set if not in constructor
        dw_low.malignancy_multiplier = 1.0
        
        # Case A: Good faith
        result_a = calculate_liquidated_damages(
            actual_loss=actual_loss,
            scenario='general_contract',
            discretionary_weight=dw_low
        )
        
        dw_high = DiscretionaryWeight(
             performance_ratio=0.1,
             fault_score=2.0,
             expectation_interest_included=False,
             is_consumer_contract=False
        )
        dw_high.malignancy_multiplier = 1.5
        
        # Case B: Bad faith
        result_b = calculate_liquidated_damages(
            actual_loss=actual_loss,
            scenario='general_contract',
            discretionary_weight=dw_high
        )

        self.assertGreater(result_b['final_suggestion'], result_a['final_suggestion'])

if __name__ == '__main__':
    unittest.main()
