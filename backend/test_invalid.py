import json
import urllib.request
import urllib.error

try:
    req = urllib.request.Request("http://127.0.0.1:8000/chat", method="POST", data=json.dumps({}).encode("utf-8"), headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)
except urllib.error.HTTPError as e:
    print("chat error:", e.code, e.read().decode())
