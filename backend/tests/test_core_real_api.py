import os
import sys
import unittest
from unittest import mock


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROJECT_DIR = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


class ProviderClientContractTests(unittest.TestCase):
    def test_deepseek_and_zhipu_clients_use_configured_provider_urls(self):
        import services.llm_client as llm_client

        calls = []

        def fake_post(url, headers=None, json=None, timeout=None, stream=False):
            calls.append(url)

            class Response:
                status_code = 200

                def raise_for_status(self):
                    return None

                def json(self):
                    return {"choices": [{"message": {"content": "ok"}}]}

            return Response()

        with mock.patch.object(llm_client.requests, "post", fake_post):
            os.environ["DEEPSEEK_API_KEY"] = "test-deepseek"
            os.environ["ZHIPU_API_KEY"] = "test-zhipu"
            self.assertEqual(
                llm_client.LLMClient(provider="deepseek").chat([{"role": "user", "content": "hi"}]),
                "ok",
            )
            self.assertEqual(
                llm_client.LLMClient(provider="zhipu").chat([{"role": "user", "content": "hi"}]),
                "ok",
            )

        self.assertIn("deepseek", calls[0].lower())
        self.assertIn("bigmodel", calls[1].lower())


if __name__ == "__main__":
    unittest.main()
