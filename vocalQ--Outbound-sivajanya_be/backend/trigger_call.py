import requests
import json
import sys

# Default to the number in .env if available, otherwise ask user
DEFAULT_NUMBER = "+919392665199" # Replace with your test number if needed

def trigger_call(phone_number):
    url = "http://localhost:8000/api/v1/outbound/start"
    payload = {
        "phone_numbers": [phone_number]
    }
    headers = {
        "Content-Type": "application/json"
    }

    try:
        print(f"Sending request to {url}...")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            print("Success! Call request processed.")
            print("Response:", response.json())
        else:
            print(f"Failed! Status Code: {response.status_code}")
            print("Response:", response.text)
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to backend server at http://localhost:8000")
        print("Make sure 'python run_server.py' is running in another terminal.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        number = sys.argv[1]
    else:
        number = input(f"Enter phone number to call (default: {DEFAULT_NUMBER}): ").strip() or DEFAULT_NUMBER
        
    trigger_call(number)
