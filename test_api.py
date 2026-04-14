import requests
import json

def test_health():
    print("\n--- Testing Health ---")
    response = requests.get("http://localhost:8080/health")
    print(f"Status: {response.status_code}")
    print(response.json())

def test_models():
    print("\n--- Testing Models Listing ---")
    response = requests.get("http://localhost:8080/v1/models")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(data)
        print(f"Found {len(data['data'])} models")
        if data['data']:
            print(f"First model: {data['data'][0]['id']}")
    else:
        print(f"Error: {response.text}")

def test_completion(model="gemini-1.5-pro"):
    print(f"\n--- Testing Completion with model: {model} ---")
    url = "http://localhost:8080/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ]
    }

    response = requests.post(url, headers=headers, json=data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_health()
    test_models()
    test_completion("gemini-3-flash-preview")
    test_completion("google/gemini-3-flash-preview")
# litellm.completion不会自己处理吗？我总感觉问题可能不知是json格式的问题
