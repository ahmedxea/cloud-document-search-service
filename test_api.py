"""
Simple test script for the FastAPI search API.
Tests the /search endpoint with sample queries.
"""
import requests
import json
import sys

API_BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint"""
    print("=" * 60)
    print("Testing Health Endpoint")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2)}\n")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}\n")
        return False


def test_search(query: str, limit: int = 10):
    """Test search endpoint"""
    print("=" * 60)
    print(f"Search Query: '{query}' (limit={limit})")
    print("=" * 60)
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/search",
            params={"q": query, "limit": limit}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total Results: {data['total_results']}\n")
            
            for i, result in enumerate(data['results'], 1):
                print(f"{i}. {result['file_name']} (score: {result['score']})")
                print(f"   Path: {result['file_path']}")
                print(f"   URL: {result['url']}")
                print(f"   Type: {result['mime_type']}")
                
                if result.get('highlights'):
                    print(f"   Match: {result['highlights'][0][:100]}...")
                print()
            
            return True
        else:
            print(f"Error: {response.text}\n")
            return False
            
    except Exception as e:
        print(f"Error: {e}\n")
        return False


def test_stats():
    """Test stats endpoint"""
    print("=" * 60)
    print("Testing Stats Endpoint")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE_URL}/stats")
        print(f"Status Code: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2)}\n")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}\n")
        return False


def main():
    """Run all API tests"""
    print("\n" + "=" * 60)
    print("Document Search API - Test Suite")
    print("=" * 60 + "\n")
    
    # Check if API is running
    try:
        requests.get(f"{API_BASE_URL}/", timeout=2)
    except requests.exceptions.ConnectionError:
        print("Error: API server is not running!")
        print("\nStart the server with:")
        print("  python -m search_service.api.app")
        print("  OR")
        print("  uvicorn search_service.api.app:app --reload")
        sys.exit(1)
    
    # Run tests
    test_health()
    test_stats()
    
    # Test searches
    test_queries = [
        ("engineering", 5),
        ("search", 5),
        ("API", 5),
        ("laptop", 5),
        ("elasticsearch", 5),
    ]
    
    for query, limit in test_queries:
        test_search(query, limit)
    
    print("=" * 60)
    print("All API tests complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
