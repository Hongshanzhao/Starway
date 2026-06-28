import requests

try:
    r = requests.get('http://localhost:5000/')
    print('server responded', r.status_code, r.text)
except Exception as e:
    print('server not running yet:', e)
