import json
import urllib.request
import urllib.error

print("Testing Endpoints...")

# Test 1: Health
try:
    req = urllib.request.Request("http://127.0.0.1:8081/health")
    res = urllib.request.urlopen(req)
    print("Health:", res.read().decode())
except Exception as e:
    print("Health test failed:", e)

# Test 2: Chat Valid
try:
    data = json.dumps({"message": "What are the timings?"}).encode('utf-8')
    req = urllib.request.Request("http://127.0.0.1:8081/api/v1/chat", method="POST", data=data, headers={"Content-Type": "application/json"})
    res = urllib.request.urlopen(req)
    print("Chat Valid:", res.read().decode())
except Exception as e:
    print("Chat Valid test failed:", e)

# Test 3: Chat Invalid (Empty message causing a 400 manually raised in code)
try:
    data = json.dumps({"message": ""}).encode('utf-8')
    req = urllib.request.Request("http://127.0.0.1:8081/api/v1/chat", method="POST", data=data, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)
except urllib.error.HTTPError as e:
    print(f"Chat Invalid (Expected Error): {e.code} - {e.read().decode()}")
except Exception as e:
    print("Chat Invalid test unexpectedly failed:", e)
