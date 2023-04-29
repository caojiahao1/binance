import requests
import main

url=main.ngrok_url
data = {
"order":"0",
"symbol": "ARBUSDT",
"signal": "short",
"price" : "1.2303","leverage": "50"
}
re = requests.post(url,json=data)
print(re.text)