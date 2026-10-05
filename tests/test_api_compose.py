"""Smoke test de API; requer `docker compose up --build -d`."""
import json, os, unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
BASE_URL=os.getenv("BASE_URL","http://localhost:8080")
def request(path,method="GET",body=None):
    data=json.dumps(body).encode() if body else None
    req=Request(BASE_URL+path,data=data,method=method,headers={"Content-Type":"application/json"})
    with urlopen(req,timeout=60) as response: return response.status,json.load(response)
class ComposeApiTest(unittest.TestCase):
    def test_health_and_help(self):
        self.assertEqual(request("/health")[0],200)
        self.assertIn("status",request("/v1/help")[1]["commands"])
    def test_results_and_inference(self):
        self.assertEqual({m["model"] for m in request("/v1/models/results")[1]["models"]},{"prophet","sarima"})
        self.assertEqual(len(request("/v1/inferences","POST",{"dataset":"janela_2026_05_19.csv"})[1]["models"]),2)
    def test_invalid_window(self):
        with self.assertRaises(HTTPError) as raised: request("/v1/inferences","POST",{"dataset":"../raw/usd_brl_daily.csv"})
        self.assertEqual(raised.exception.code,422)
