import unittest
import os
import json
from unittest.mock import MagicMock, patch
from legal_resources import LegalResourceProvider, PID_PREFIX, MCP_LEGAL_PREFIX

class TestLegalResourceProvider(unittest.TestCase):
    def setUp(self):
        # Use a temporary file for testing
        self.test_pid_file = "test_pids.json"
        self.provider = LegalResourceProvider(pid_file_path=self.test_pid_file)

    def tearDown(self):
        # Clean up temporary file
        if os.path.exists(self.test_pid_file):
            os.remove(self.test_pid_file)

    def test_list_resources(self):
        resources = self.provider.list_resources()
        self.assertTrue(len(resources) > 0)
        
        # Check for specific known resources
        uris = [r['uri'] for r in resources]
        self.assertIn("legal://civil-code/contract", uris)
        self.assertIn("legal://templates/contract-checklist", uris)
        self.assertIn("legal://rules/penalty-assessment", uris)

    def test_get_resource_content_static(self):
        uri = "legal://civil-code/contract"
        content_json = self.provider.get_resource_content(uri)
        
        # Should be a JSON-LD string
        data = json.loads(content_json)
        self.assertEqual(data["@context"], "https://schema.org")
        self.assertEqual(data["@id"], uri)
        self.assertIn("mainEntity", data)
        self.assertIn("articles", data["mainEntity"])

    def test_pid_generation_and_retrieval(self):
        content = {"test": "data", "value": 123}
        metadata = {"name": "Test Resource", "type": "Test"}
        
        # Generate PID
        pid_uri = self.provider.generate_pid(content, metadata)
        self.assertTrue(pid_uri.startswith(PID_PREFIX))
        
        # Retrieve by PID
        retrieved_content_json = self.provider.get_resource_content(pid_uri)
        data = json.loads(retrieved_content_json)
        
        self.assertEqual(data["@id"], pid_uri)
        self.assertEqual(data["mainEntity"], content)
        
        # Verify persistence
        # Re-initialize provider to simulate server restart
        new_provider = LegalResourceProvider(pid_file_path=self.test_pid_file)
        retrieved_again = new_provider.get_resource_content(pid_uri)
        data_again = json.loads(retrieved_again)
        self.assertEqual(data_again["mainEntity"], content)

    def test_pid_chaining(self):
        # Create parent resource
        parent_content = {"id": 1, "name": "Parent Contract"}
        parent_metadata = {"type": "Contract"}
        parent_pid = self.provider.generate_pid(parent_content, parent_metadata)
        
        # Create child resource (e.g. compliance report)
        child_content = {"id": 2, "report": "Passed"}
        child_metadata = {"type": "Report"}
        child_pid = self.provider.generate_pid(child_content, child_metadata, parent_pid=parent_pid)
        
        # Retrieve child and check lineage
        child_json = self.provider.get_resource_content(child_pid)
        child_data = json.loads(child_json)
        
        self.assertIn("isPartOf", child_data)
        self.assertEqual(child_data["isPartOf"]["@id"], parent_pid)

    def test_invalid_resource(self):
        with self.assertRaises(Exception): # InvalidParamsError
            self.provider.get_resource_content("legal://unknown/resource")

    def test_invalid_pid(self):
        with self.assertRaises(Exception): # InvalidParamsError
            self.provider.get_resource_content("legal://pid/invalid-handle")

if __name__ == '__main__':
    unittest.main()
