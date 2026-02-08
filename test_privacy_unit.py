import unittest
from privacy_middleware import PrivacyPreservingMAE

class TestPrivacyMiddleware(unittest.TestCase):
    def setUp(self):
        self.middleware = PrivacyPreservingMAE()

    def test_middleware_masking(self):
        # Test Phone
        text = "Contact: 13812345678"
        masked = self.middleware.mask_sensitive_data(text)
        self.assertEqual(masked, "Contact: 138****5678")
        
        # Test ID Card
        # The expected regex output might vary based on internal logic of mask_sensitive_data
        # If the input is "ID: 110101199001011234" (length 18), expected is "ID: 110101********1234"
        # However, due to repeated regex adjustments, let's verify what we actually produce
        # Based on last edit: if len=18, return val[:6] + "********" + val[-4:]
        text = "ID: 110101199001011234"
        masked = self.middleware.mask_sensitive_data(text)
        self.assertEqual(masked, "ID: 110101********1234")
        
        # Test Account
        text = "Account: 6222021001112223333"
        masked = self.middleware.mask_sensitive_data(text)
        self.assertEqual(masked, "Account: **** 3333")

        # Test Email
        text = "Email: alice@example.com"
        masked = self.middleware.mask_sensitive_data(text)
        self.assertEqual(masked, "Email: a***@example.com")
        
    def test_elicitation_check(self):
        # Safe args
        args = {"contract_text": "Normal contract"}
        self.assertIsNone(self.middleware.check_elicitation_requirement(args))
        
        # Sensitive args
        args = {"medical_record": "Patient info"}
        result = self.middleware.check_elicitation_requirement(args)
        self.assertIsNotNone(result)
        self.assertIn("medical_record", result)

    def test_metadata_injection(self):
        data = {"result": "ok"}
        processed = self.middleware.inject_compliance_metadata(data)
        
        self.assertIn("metadata", processed)
        self.assertIn("gb_45438_compliance", processed["metadata"])
        self.assertEqual(processed["metadata"]["gb_45438_compliance"]["model_version"], "Legal-CN-v0.2.0")

if __name__ == '__main__':
    unittest.main()
