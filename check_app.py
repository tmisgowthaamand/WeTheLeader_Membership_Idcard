import requests
try:
    r = requests.get('http://127.0.0.1:5000/', timeout=5)
    print(f"Status: {r.status_code}")
    print(f"Content Length: {len(r.text)}")
    if 'chatbot' in r.text.lower():
        print("Chatbot found in homepage.")
    else:
        print("Chatbot NOT found in homepage.")
except Exception as e:
    print(f"Error connecting: {e}")
