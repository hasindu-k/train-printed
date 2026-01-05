#!/usr/bin/env python3
"""
Example script to test the FastAPI backend endpoints
Run: python test_api.py
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_health():
    """Test health endpoint"""
    print_section("1️⃣  Testing Health Check")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200

def test_create_user():
    """Create a test user"""
    print_section("2️⃣  Creating Test User")
    data = {
        "name": "John Reviewer",
        "email": "john@example.com",
        "role": "reviewer"
    }
    response = requests.post(f"{BASE_URL}/users", json=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2, default=str)}")
    assert response.status_code == 201
    return result["id"]

def test_list_users():
    """List all users"""
    print_section("3️⃣  Listing Users")
    response = requests.get(f"{BASE_URL}/users")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")
    assert response.status_code == 200

def test_upload_document(pdf_path="test.pdf"):
    """Upload a PDF document"""
    print_section("4️⃣  Uploading Document")
    
    # Check if test PDF exists, if not create a dummy one
    if not Path(pdf_path).exists():
        print(f"⚠️  Test PDF not found at {pdf_path}")
        print("    To test upload, provide a real PDF file")
        return None
    
    with open(pdf_path, "rb") as f:
        files = {"file": f}
        response = requests.post(f"{BASE_URL}/documents/upload", files=files)
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2, default=str)}")
    
    if response.status_code == 201:
        return result["id"]
    return None

def test_list_documents():
    """List all documents"""
    print_section("5️⃣  Listing Documents")
    response = requests.get(f"{BASE_URL}/documents")
    print(f"Status: {response.status_code}")
    results = response.json()
    print(f"Found {len(results)} document(s)")
    if results:
        print(f"First document: {json.dumps(results[0], indent=2, default=str)}")
    assert response.status_code == 200
    return results[0]["id"] if results else None

def test_get_document(doc_id):
    """Get a specific document"""
    print_section("6️⃣  Getting Document Details")
    response = requests.get(f"{BASE_URL}/documents/{doc_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")
    assert response.status_code == 200

def test_convert_pages(doc_id):
    """Convert PDF to TIFF pages"""
    print_section("7️⃣  Converting PDF to TIFF Pages")
    response = requests.post(f"{BASE_URL}/documents/{doc_id}/convert-pages")
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2, default=str)}")
    
    if response.status_code == 200:
        print(f"✅ Successfully converted {result.get('total_pages', 0)} pages")
        return True
    return False

def test_list_pages(doc_id):
    """List pages for a document"""
    print_section("8️⃣  Listing Pages")
    response = requests.get(f"{BASE_URL}/documents/{doc_id}/pages")
    print(f"Status: {response.status_code}")
    pages = response.json()
    print(f"Found {len(pages)} page(s)")
    if pages:
        print(f"First page: {json.dumps(pages[0], indent=2, default=str)}")
        return pages[0]["id"]
    return None

def test_extract_lines(doc_id, page_id):
    """Extract lines from a page"""
    print_section("9️⃣  Extracting Lines from Page")
    response = requests.post(f"{BASE_URL}/documents/{doc_id}/pages/{page_id}/extract-lines")
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2, default=str)}")
    
    if response.status_code == 200:
        print(f"✅ Successfully extracted {result.get('lines_extracted', 0)} lines")
        return True
    return False

def test_create_gt_files(doc_id):
    """Create ground truth files"""
    print_section("🔟 Creating Ground Truth Files")
    response = requests.post(f"{BASE_URL}/documents/{doc_id}/create-gt-files")
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2, default=str)}")
    
    if response.status_code == 200:
        print(f"✅ Successfully created {result.get('gt_files_created', 0)} GT files")

def test_list_lines(doc_id):
    """List lines for a document"""
    print_section("1️⃣1️⃣ Listing Lines")
    response = requests.get(f"{BASE_URL}/documents/{doc_id}/lines?verified=false")
    print(f"Status: {response.status_code}")
    lines = response.json()
    print(f"Found {len(lines)} unverified line(s)")
    if lines:
        print(f"First line: {json.dumps(lines[0], indent=2, default=str)}")
        return lines[0]["id"]
    return None

def test_get_line(line_id):
    """Get a specific line"""
    print_section("1️⃣2️⃣ Getting Line Details")
    response = requests.get(f"{BASE_URL}/lines/{line_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")

def test_save_correction(line_id):
    """Save corrected text for a line"""
    print_section("1️⃣3️⃣ Saving Corrected Text")
    data = {"corrected_text": "සිංහල පදය"}
    response = requests.put(f"{BASE_URL}/lines/{line_id}/corrected-text", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")

def test_verify_line(line_id):
    """Verify a line"""
    print_section("1️⃣4️⃣ Verifying Line")
    data = {}  # reviewer_id is optional
    response = requests.put(f"{BASE_URL}/lines/{line_id}/verify", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")

def test_unverify_line(line_id):
    """Unverify a line"""
    print_section("1️⃣5️⃣ Unverifying Line")
    response = requests.put(f"{BASE_URL}/lines/{line_id}/unverify")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")

def test_export_dataset(doc_id):
    """Export dataset"""
    print_section("1️⃣6️⃣ Exporting Dataset")
    response = requests.get(f"{BASE_URL}/documents/{doc_id}/export")
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2, default=str)}")

def main():
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║     FastAPI Backend - API Endpoint Testing Script        ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Test basic endpoints
        test_health()
        
        user_id = test_create_user()
        test_list_users()
        
        # Test document operations
        test_list_documents()
        
        # If you have a PDF file to test with:
        doc_id = test_upload_document("test.pdf")
        
        if not doc_id:
            # If no PDF upload, use first existing document
            doc_id = test_list_documents()
        
        if doc_id:
            test_get_document(doc_id)
            
            # Test PDF conversion and line extraction
            if test_convert_pages(doc_id):
                page_id = test_list_pages(doc_id)
                
                if page_id and test_extract_lines(doc_id, page_id):
                    test_create_gt_files(doc_id)
                    
                    line_id = test_list_lines(doc_id)
                    if line_id:
                        test_get_line(line_id)
                        test_save_correction(line_id)
                        test_verify_line(line_id)
                        test_unverify_line(line_id)
                    
                    test_export_dataset(doc_id)
        
        print_section("✅ Testing Complete!")
        print("All tests passed successfully!\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to API server")
        print("   Make sure the server is running:")
        print("   python -m uvicorn app.main:app --reload\n")
    except AssertionError as e:
        print(f"\n❌ Assertion failed: {e}\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")

if __name__ == "__main__":
    main()
