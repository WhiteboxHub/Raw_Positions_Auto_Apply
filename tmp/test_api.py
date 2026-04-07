import os
import requests
from dotenv import load_dotenv

load_dotenv()
session_token = os.environ.get("WHITEBOX_SESSION_TOKEN")

cookies = {"next-auth.session-token": session_token}

# 1. Get the actual API token via NextAuth session
session_url = "https://whitebox-learning.com/api/auth/session"
session_resp = requests.get(session_url, cookies=cookies)

print(f"Session Status: {session_resp.status_code}")
if session_resp.status_code == 200:
    session_data = session_resp.json()
    print("Session Keys:", session_data.keys())
    
    # Extract the token (can be under access_token, accessToken, user['token'], etc)
    token = session_data.get('accessToken') or session_data.get('token')
    if not token and 'user' in session_data:
        token = session_data['user'].get('accessToken') or session_data['user'].get('token')
        
    print(f"Extracted Token attached? {'Yes' if token else 'No'}")
    
    if token:
        # 2. Call the real API
        api_url = "https://api.whitebox-learning.com/api/email-positions/paginated"
        headers = {
            "Authorization": f"Bearer {token}",
            "Origin": "https://whitebox-learning.com",
            "Referer": "https://whitebox-learning.com/"
        }
        params = {"page": 1, "page_size": 5}
        
        api_resp = requests.get(api_url, params=params, headers=headers)
        print(f"API Status: {api_resp.status_code}")
        if api_resp.status_code == 200:
            api_data = api_resp.json()
            items = api_data.get("items", []) if isinstance(api_data, dict) else (api_data if isinstance(api_data, list) else [])
            print("API returned elements:", len(items))
            if items:
                print("First element dates:")
                print("extracted_at:", items[0].get("extracted_at"))
                print("extraction_date:", items[0].get("extraction_date"))
                print("created_at:", items[0].get("created_at"))
        else:
            print("API error:", api_resp.text[:200])
else:
    print("Session error:", session_resp.text[:200])
