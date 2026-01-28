import requests
payload = {
  "tp_history": [0.0, 0.0, 0.1, 5.2, 12.3, 3.1, 0.0],
  "t2m_history":[15,15,14,13,12,12,11]
}
r = requests.post("http://127.0.0.1:8000/predict", json=payload)
print(r.json())
