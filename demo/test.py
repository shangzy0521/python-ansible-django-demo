import requests
r1 = requests.post('http://127.0.0.1:8000/demo/test')
print(r1, r1.text)