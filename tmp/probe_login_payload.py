import requests
import json

ep = "https://api.whitebox-learning.com/api/login"
r = requests.post(ep, json={"email": "test@test.com", "password": "password"})
print(json.dumps(r.json()["detail"], indent=2))
