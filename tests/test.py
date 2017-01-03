import requests

base_url = 'http://127.0.0.1:5000'

def test_1():
    url = base_url
    r = requests.get(url)
    print r.text

test_1()