import requests
import json

def test_health():
    response = requests.get("http://localhost:8080/health")
    print(f"Health check: {response.status_code}")
    print(response.json())

def test_completion():
    url = "http://localhost:8080/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "vertex_ai/gemini-pro",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ]
    }
    
    response = requests.post(url, headers=headers, json=data)
    print(f"Completion status: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_health()
    print("-" * 20)
    test_completion()
