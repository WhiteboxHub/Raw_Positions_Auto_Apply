import os
import requests
from dotenv import load_dotenv

load_dotenv()

def check_workflow():
    base_url = os.getenv('WBL_API_URL', 'https://api.whitebox-learning.com/api')
    token = os.getenv('WBL_API_TOKEN')
    workflow_key = "smart_apply"

    print(f"--- API Diagnostic ---")
    print(f"Base URL: {base_url}")
    print(f"Token present: {'Yes' if token else 'No'}")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Test 1: Check the specific workflow key
    for key in ["smart_apply", "bot_linkedin_post_contact_extractor"]:
        url = f"{base_url}/orchestrator/workflows/key/{key}"
        print(f"Checking workflow: {key}...")
        
        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                print(f"✅ FOUND! Workflow ID: {data.get('id')}")
                print(f"Name: {data.get('name')}")
            else:
                print(f"❌ NOT FOUND. Status: {resp.status_code}")
                print(f"Response: {resp.text[:200]}")
        except Exception as e:
            print(f"❗ Error connecting to API: {e}")

if __name__ == "__main__":
    check_workflow()
