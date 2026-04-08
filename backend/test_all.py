import urllib.request
import json

queries = [
    'How can I contact the admission office?',
    'Where can I get the fee payment challan?',
    'Tell me about the placement cell.',
    'Who is the HOD of CSE?',
    'What are the office timings?',
    'Where is the nearest space station?'
]

results = {}
for q in queries:
    try:
        data = json.dumps({'message': q}).encode('utf-8')
        req = urllib.request.Request('http://127.0.0.1:8000/chat', method='POST', data=data, headers={'Content-Type': 'application/json'})
        res = urllib.request.urlopen(req)
        results[q] = json.loads(res.read().decode())
    except Exception as e:
        results[q] = str(e)

with open('results.json', 'w') as f:
    json.dump(results, f, indent=2)
