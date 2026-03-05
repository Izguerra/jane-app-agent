import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def verify_persistence():
    print("1. Fetching current profile...")
    try:
        response = requests.get(f"{BASE_URL}/clinics/me")
        if response.status_code != 200:
            print(f"Failed to fetch profile: {response.status_code} {response.text}")
            return False
        
        current_data = response.json()
        print(f"Current Name: {current_data.get('name')}")
    except Exception as e:
        print(f"Error fetching profile: {e}")
        return False

    print("\n2. Updating profile with test data...")
    test_data = {
        "name": "Persistence Test Studio",
        "address": "999 Test Lane",
        "phone": "555-9999",
        "description": "This is a test description to verify persistence."
    }
    
    try:
        response = requests.put(f"{BASE_URL}/clinics/me", json=test_data)
        if response.status_code != 200:
            print(f"Failed to update profile: {response.status_code} {response.text}")
            return False
        print("Update successful.")
    except Exception as e:
        print(f"Error updating profile: {e}")
        return False

    print("\n3. Fetching profile again to verify persistence...")
    try:
        response = requests.get(f"{BASE_URL}/clinics/me")
        if response.status_code != 200:
            print(f"Failed to fetch profile: {response.status_code} {response.text}")
            return False
        
        updated_data = response.json()
        print(f"Updated Name: {updated_data.get('name')}")
        print(f"Updated Address: {updated_data.get('address')}")
        
        if updated_data.get('name') == test_data['name'] and updated_data.get('address') == test_data['address']:
            print("\n✅ SUCCESS: Data persisted correctly!")
            return True
        else:
            print("\n❌ FAILURE: Data did not persist.")
            print(f"Expected: {test_data}")
            print(f"Got: {updated_data}")
            return False
            
    except Exception as e:
        print(f"Error fetching profile: {e}")
        return False

if __name__ == "__main__":
    success = verify_persistence()
    if not success:
        sys.exit(1)
