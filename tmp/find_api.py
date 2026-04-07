import os
import requests
from dotenv import load_dotenv

load_dotenv()

def find_correct_endpoint():
    token = os.getenv('WBL_API_TOKEN')
    key = "bot_linkedin_post_contact_extractor"
    
    # Possible base URLs to test
    bases = [
        "https://api.whitebox-learning.com/api",
        "https://api.whitebox-learning.com",
        "https://whitebox-learning.com/api",
        "https://whitebox-learning.com"
    ]
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    print(f"--- Endpoint Discovery ---")
    print(f"Testing key: {key}")
    
    for base in bases:
        url = f"{base}/orchestrator/workflows/key/{key}"
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            print(f"URL: {url} -> Status: {resp.status_code}")
            if resp.status_code == 200:
                print(f"✅ SUCCESS! Found at: {base}")
                return
        except Exception:
            print(f"URL: {url} -> Connection Error")

if __name__ == "__main__":
    find_correct_endpoint()
