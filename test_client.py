"""
Test client to verify server endpoints over HTTPS using the self-signed cert.pem.
"""
import requests

BASE_URL = "https://127.0.0.1:8443"
CERT_PATH = "cert.pem"

def test_flow():
    # 1. Health check
    print("Testing /health...")
    res = requests.get(f"{BASE_URL}/health", verify=CERT_PATH)
    print(f"Status: {res.status_code}, Response: {res.json()}")
    assert res.status_code == 200

    # 2. Register a weak password (expecting 400 with feedback)
    print("\nTesting registration with weak password...")
    res = requests.post(
        f"{BASE_URL}/register",
        json={"username": "atharva", "password": "123"},
        verify=CERT_PATH
    )
    print(f"Status: {res.status_code}, Response: {res.json()}")
    assert res.status_code == 400

    # 3. Register a strong password (expecting 201)
    print("\nTesting registration with strong password...")
    res = requests.post(
        f"{BASE_URL}/register",
        json={"username": "atharva", "password": "CorrectHorseBatteryStaple99!"},
        verify=CERT_PATH
    )
    print(f"Status: {res.status_code}, Response: {res.json()}")
    # 201 on success, or 400 if user already registered from a previous test run
    assert res.status_code in (201, 400)

    # 4. Login correctly (expecting 200)
    print("\nTesting correct login...")
    res = requests.post(
        f"{BASE_URL}/login",
        json={"username": "atharva", "password": "CorrectHorseBatteryStaple99!"},
        verify=CERT_PATH
    )
    print(f"Status: {res.status_code}, Response: {res.json()}")
    assert res.status_code == 200

    # 5. Login with a wrong password (expecting 401)
    print("\nTesting login with wrong password...")
    res = requests.post(
        f"{BASE_URL}/login",
        json={"username": "atharva", "password": "WrongPassword123!"},
        verify=CERT_PATH
    )
    print(f"Status: {res.status_code}, Response: {res.json()}")
    assert res.status_code == 401

    # 6. Login as an unknown user (expecting the exact same 401 message)
    print("\nTesting login with unknown user...")
    res = requests.post(
        f"{BASE_URL}/login",
        json={"username": "nonexistentuser", "password": "AnyPassword123!"},
        verify=CERT_PATH
    )
    print(f"Status: {res.status_code}, Response: {res.json()}")
    assert res.status_code == 401

    print("\nAll tests passed successfully!")

if __name__ == "__main__":
    test_flow()