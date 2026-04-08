import os
import sys
import json
import requests
from pathlib import Path
from dotenv import load_dotenv, set_key

def update_env_file(env_path, adjustments):
    """Update or inject multiple key-value pairs into the .env file safely."""
    # Ensure file exists
    if not os.path.exists(env_path):
        with open(env_path, 'w') as f:
            f.write("")
            
    for key, value in adjustments.items():
        set_key(env_path, key, value)
        
def perform_login():
    """Logs into Whitebox and updates the .env tokens."""
    env_path = str(Path(".env").resolve())
    load_dotenv(env_path)
    
    email = os.environ.get("WHITEBOX_EMAIL")
    password = os.environ.get("WHITEBOX_PASSWORD")
    
    if not email or not password:
        print("❌ Error: WHITEBOX_EMAIL or WHITEBOX_PASSWORD not found in .env")
        print("Please add these variables to your .env file like this:")
        print("WHITEBOX_EMAIL=your_email@gmail.com")
        print("WHITEBOX_PASSWORD=your_password")
        return False
        
    print(f"🔄 Attempting login to Whitebox Learning as {email}...")
    
    # Standard FastAPI / OAuth2 login payload
    url = "https://api.whitebox-learning.com/api/login"
    
    # Most APIs accept json, some accept Form Data. We try JSON first (common in newer FastAPI)
    payload = {
        "username": email,
        "password": password
    }
    
    try:
        response = requests.post(url, json=payload, headers={"Origin": "https://whitebox-learning.com"}, timeout=10)
        
        # Fallback to Form Data if JSON is rejected with 422
        if response.status_code == 422:
            response = requests.post(url, data=payload, headers={"Origin": "https://whitebox-learning.com"}, timeout=10)
            
        if response.status_code == 200:
            data = response.json()
            # Handle standard "access_token" or specific nested formats
            token = data.get("access_token") or data.get("token", {}).get("access_token") or data.get("token")
            
            if token:
                print("✅ Login successful! Token retrieved.")
                
                # Update both tokens used by Raw_Positions_Auto_Apply pipeline
                updates = {
                    "WHITEBOX_BEARER_TOKEN": token,
                    "WBL_API_TOKEN": token
                }
                
                update_env_file(env_path, updates)
                print("✅ Successfully updated .env with new tokens.")
                return True
            else:
                print(f"❌ Login succeeded but could not find token in response: {list(data.keys())}")
                return False
                
        elif response.status_code == 404 or response.status_code == 401:
            print("❌ Login failed! Incorrect email or password.")
            return False
        else:
            print(f"❌ Login failed! Status: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Network error while attempting to login: {e}")
        return False

if __name__ == "__main__":
    perform_login()
