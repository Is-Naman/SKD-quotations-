import unittest
from unittest.mock import patch, MagicMock
import json
from app import get_search_candidates, call_gemini_rag

class TestGeminiRAG(unittest.TestCase):
    def setUp(self):
        self.catalog = [
            {"product_id": "LGT1", "product_name": "Wipro T1 28W LED Recessed Grid Light", "latest_price": 1250.0, "unit": "Nos"},
            {"product_id": "LGT3", "product_name": "Wipro T3 15W LED Recess Downlight", "latest_price": 450.0, "unit": "Nos"},
            {"product_id": "SIM001", "product_name": "Siemens MCB 16A Single Pole", "latest_price": 115.0, "unit": "pcs"},
        ]

    def test_get_search_candidates(self):
        # Match downlight keywords
        candidates = get_search_candidates("15W LED Downlight recess", self.catalog)
        # Should rank LGT3 first due to token overlap on "recess", "downlight", "led"
        self.assertEqual(candidates[0]["product_id"], "LGT3")
        
        # Match MCB keywords
        candidates_mcb = get_search_candidates("Siemens MCB 16A", self.catalog)
        self.assertEqual(candidates_mcb[0]["product_id"], "SIM001")

    @patch("urllib.request.urlopen")
    def test_call_gemini_rag_success(self, mock_urlopen):
        # Mock Gemini response
        mock_response = MagicMock()
        mock_json = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "quantity": 5,
                            "matches": [
                                {
                                    "product_id": "LGT3",
                                    "product_name": "Wipro T3 15W LED Recess Downlight",
                                    "note": "Matched by Gemini AI"
                                }
                            ]
                        })
                    }]
                }
            }]
        }
        mock_response.read.return_value = json.dumps(mock_json).encode("utf-8")
        # Support entering the context manager
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        res = call_gemini_rag("15W LED recess downlight - 5 Nos", self.catalog, "dummy_key")
        self.assertIsNotNone(res)
        self.assertEqual(res["quantity"], 5)
        self.assertEqual(res["matches"][0]["product_id"], "LGT3")

    @patch("app.call_gemini_rag")
    def test_generate_quotation_route(self, mock_call_gemini_rag):
        from app import app
        client = app.test_client()
        
        # Test 1: Route without API Key (falls back to local parser)
        payload = {
            "enquiry": "Please supply 6 NOS of MCB 32A 3 Pole Make: LEGRAND.",
            "catalog": "master_product_catalog_clean.csv",
            "gemini_api_key": ""
        }
        res = client.post("/api/generate-quotation", json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["quotation"][0]["product_id"], "LEGR003")
        self.assertEqual(data["quotation"][0]["requested_quantity"], 6)

        # Test 2: Route with API Key (uses Gemini RAG)
        mock_call_gemini_rag.return_value = {
            "quantity": 6,
            "matches": [
                {
                    "product_id": "LEGR003",
                    "product_name": "Legrand 3 Pole MCB 32A",
                    "note": "AI Matched"
                }
            ]
        }
        payload_key = {
            "enquiry": "Please supply 6 NOS of MCB 32A 3 Pole Make: LEGRAND.",
            "catalog": "master_product_catalog_clean.csv",
            "gemini_api_key": "some_valid_key"
        }
        res_key = client.post("/api/generate-quotation", json=payload_key)
        self.assertEqual(res_key.status_code, 200)
        data_key = json.loads(res_key.data)
        self.assertEqual(data_key["quotation"][0]["product_id"], "LEGR003")
        self.assertEqual(data_key["quotation"][0]["requested_quantity"], 6)
        self.assertEqual(data_key["quotation"][0]["note"], "AI Matched")

if __name__ == "__main__":
    unittest.main()
