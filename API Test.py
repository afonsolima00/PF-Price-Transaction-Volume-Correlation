import requests

url = "https://api.etherscan.io/api"
params = {
    "module": "account",
    "action": "txlist",
    "address": "0x95222290DD7278Aa3Ddd389Cc1E1d165CC4BAfe5",
    "startblock": 0,
    "endblock": 99999999,
    "sort": "asc",
    "apikey": "M8NZU3KCC4U5H6NFS19DTFFU2FUVCHB8ZB"
}
response = requests.get(url, params=params)
print(response.json())
