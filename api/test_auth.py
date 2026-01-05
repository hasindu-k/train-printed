"""Quick test script for API authentication and endpoints."""

import requests
import json
from typing import Optional

BASE_URL = "http://localhost:8000"

# Store tokens for use across requests
access_token: Optional[str] = None
refresh_token: Optional[str] = None
current_user = None


def print_response(title: str, response):
    """Pretty print API response."""
    print(f"\n{'='*60}")
    print(f"📌 {title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2, default=str))
    except:
        print(response.text)


def auth_headers() -> dict:
    """Get authorization headers with current token."""
    if not access_token:
        return {}
    return {"Authorization": f"Bearer {access_token}"}


# ============ AUTHENTICATION TESTS ============

def test_register():
    """Test user registration."""
    global access_token, refresh_token, current_user
    
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "name": "Test Annotator",
            "email": "annotator@test.com",
            "password": "testpass123"
        }
    )
    
    print_response("Register New User", response)
    
    if response.status_code == 201:
        data = response.json()
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        current_user = data["user"]
        print(f"✅ Registration successful. Tokens saved.")
    
    return response


def test_login():
    """Test user login."""
    global access_token, refresh_token, current_user
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "annotator@test.com",
            "password": "testpass123"
        }
    )
    
    print_response("Login User", response)
    
    if response.status_code == 200:
        data = response.json()
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        current_user = data["user"]
        print(f"✅ Login successful. Tokens saved.")
    
    return response


def test_get_current_user():
    """Test getting current user info."""
    response = requests.get(
        f"{BASE_URL}/auth/me",
        headers=auth_headers()
    )
    
    print_response("Get Current User", response)
    return response


def test_refresh_token():
    """Test token refresh."""
    global access_token
    
    response = requests.post(
        f"{BASE_URL}/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    print_response("Refresh Access Token", response)
    
    if response.status_code == 200:
        data = response.json()
        access_token = data["access_token"]
        print(f"✅ Token refreshed. New access token saved.")
    
    return response


def test_logout():
    """Test logout endpoint."""
    response = requests.post(
        f"{BASE_URL}/auth/logout",
        headers=auth_headers()
    )
    
    print_response("Logout", response)
    return response


# ============ USER MANAGEMENT TESTS ============

def test_create_user_as_admin():
    """Test creating user as admin (will fail if not admin)."""
    response = requests.post(
        f"{BASE_URL}/users/admin/create",
        headers=auth_headers(),
        json={
            "name": "Test Reviewer",
            "email": "reviewer@test.com",
            "password": "reviewerpass123",
            "role": "reviewer"
        }
    )
    
    print_response("Create User as Admin", response)
    return response


def test_list_users():
    """Test listing all users (admin only)."""
    response = requests.get(
        f"{BASE_URL}/users/",
        headers=auth_headers()
    )
    
    print_response("List All Users", response)
    return response


def test_get_user():
    """Test getting specific user info."""
    if not current_user:
        print("❌ No current user. Register/login first.")
        return None
    
    user_id = current_user["id"]
    response = requests.get(
        f"{BASE_URL}/users/{user_id}",
        headers=auth_headers()
    )
    
    print_response("Get User by ID", response)
    return response


def test_update_user():
    """Test updating user info."""
    if not current_user:
        print("❌ No current user. Register/login first.")
        return None
    
    user_id = current_user["id"]
    response = requests.put(
        f"{BASE_URL}/users/{user_id}",
        headers=auth_headers(),
        json={"name": "Updated Test Annotator"}
    )
    
    print_response("Update User", response)
    return response


# ============ UNAUTHENTICATED ACCESS TEST ============

def test_unauthorized_access():
    """Test accessing protected endpoint without token."""
    response = requests.get(f"{BASE_URL}/auth/me")
    
    print_response("Unauthorized Access (No Token)", response)
    return response


def test_invalid_token():
    """Test accessing with invalid token."""
    response = requests.get(
        f"{BASE_URL}/auth/me",
        headers={"Authorization": "Bearer invalid_token_here"}
    )
    
    print_response("Invalid Token Access", response)
    return response


# ============ DOCUMENT UPLOAD TEST ============

def test_document_upload():
    """Test uploading a PDF document."""
    # Create a minimal PDF for testing
    pdf_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/Parent 2 0 R/Resources<<>>>>endobj xref 0 4 0000000000 65535 f 0000000009 00000 n 0000000058 00000 n 0000000115 00000 n trailer<</Size 4/Root 1 0 R>>startxref 190 %%EOF"
    
    response = requests.post(
        f"{BASE_URL}/documents/upload",
        headers={"Authorization": f"Bearer {access_token}"} if access_token else {},
        files={"file": ("test.pdf", pdf_content)}
    )
    
    print_response("Upload Document", response)
    return response


# ============ MAIN TEST SUITE ============

def run_all_tests():
    """Run complete authentication test suite."""
    print("\n" + "="*60)
    print("🧪 AUTHENTICATION TEST SUITE")
    print("="*60)
    
    tests = [
        ("Register User", test_register),
        ("Get Current User", test_get_current_user),
        ("Unauthorized Access", test_unauthorized_access),
        ("Invalid Token", test_invalid_token),
        ("Login User", test_login),
        ("List Users (Admin)", test_list_users),
        ("Get User by ID", test_get_user),
        ("Update User", test_update_user),
        ("Refresh Token", test_refresh_token),
        ("Document Upload", test_document_upload),
        ("Logout", test_logout),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            response = test_func()
            if response:
                success = 200 <= response.status_code < 300
                results.append((test_name, "✅ PASS" if success else f"⚠️ {response.status_code}"))
            else:
                results.append((test_name, "⏭️ SKIPPED"))
        except Exception as e:
            results.append((test_name, f"❌ ERROR: {str(e)}"))
    
    # Print summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    for test_name, result in results:
        print(f"{test_name:.<40} {result}")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Run all tests
    run_all_tests()
    
    # Or run individual tests:
    # test_register()
    # test_login()
    # test_get_current_user()
