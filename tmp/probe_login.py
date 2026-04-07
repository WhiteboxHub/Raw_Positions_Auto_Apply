import requests
import json

endpoints = [
    "https://api.whitebox-learning.com/api/login",
    "https://api.whitebox-learning.com/api/auth/login",
    "https://api.whitebox-learning.com/api/login/access-token",
    "https://api.whitebox-learning.com/api/v1/login/access-token",
    "https://api.whitebox-learning.com/login"
]

results = []

for ep in endpoints:
    # Test JSON login
    try:
        r = requests.post(ep, json={"email": "test@test.com", "password": "password"}, timeout=5)
        results.append({"url": ep, "method": "json", "status": r.status_code, "text": r.text[:100]})
    except:
        pass
        
    # Test Form data login (OAuth2 standard)
    try:
        r = requests.post(ep, data={"username": "test@test.com", "password": "password"}, timeout=5)
        results.append({"url": ep, "method": "form", "status": r.status_code, "text": r.text[:100]})
    except:
        pass

with open("tmp/probe_results.json", "w") as f:
    json.dump(results, f, indent=2)
