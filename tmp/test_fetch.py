import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# Tokens to test
TOKEN_A = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJndXJ1dGVqYTIzM0BnbWFpbC5jb20iLCJ0ZWFtIjpudWxsLCJyb2xlIjoiYWRtaW4iLCJpc19hZG1pbiI6dHJ1ZSwiaXNfZW1wbG95ZWUiOnRydWUsImV4cCI6MTc3NTU2NTQ0MX0.OOY4KjSUWMC91w1tVR3wWHTC9ZQmYb9hi7fRz_KIqw0" # guruteja
TOKEN_B = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJyYXZpa3VtYXJyYXlhcGFsbGlAZ21haWwuY29tIiwidGVhbSI6bnVsbCwicm9sZSI6ImFkbWluIiwiaXNfYWRtaW4iOnRydWUsImlzX2VtcGxveWVlIjp0cnVlLCJleHAiOjE3NzU2MTY3NDh9.g0oL5JTomuTzdic9HVNXPlsc7HVrbmV0B9Vz6eFTwrQ" # ravikumar

endpoints = [
    "https://api.whitebox-learning.com/api/email-positions/paginated",
    "https://api.whitebox-learning.com/api/email-positions",
    "https://api.whitebox-learning.com/api/extraction/email-positions",
    "https://whitebox-learning.com/api/email-positions/paginated"
]

params = {"page": 1, "page_size": 10}

results = []

for token_name, token in [("guruteja", TOKEN_A), ("ravikumar", TOKEN_B)]:
    headers = {
        "Authorization": f"Bearer {token}",
        "Origin": "https://whitebox-learning.com",
        "Referer": "https://whitebox-learning.com/"
    }
    
    for ep in endpoints:
        res_data = {"token": token_name, "url": ep}
        try:
            resp = requests.get(ep, params=params, headers=headers)
            res_data["status"] = resp.status_code
            if resp.status_code == 200:
                json_data = resp.json()
                res_data["success"] = True
                res_data["keys"] = list(json_data.keys()) if isinstance(json_data, dict) else str(type(json_data))
            else:
                res_data["success"] = False
                res_data["error"] = resp.text[:100]
        except Exception as e:
            res_data["success"] = False
            res_data["error"] = str(e)
        
        results.append(res_data)

with open("tmp/test_fetch_results.json", "w") as f:
    json.dump(results, f, indent=2)

