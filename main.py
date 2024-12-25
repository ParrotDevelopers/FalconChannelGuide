import requests
import os

filename = "epg.xml.gz"
if os.path.exists(filename):
    os.remove(filename)

response = requests.get(os.getenv("EPG_URL"))

open(filename, "wb").write(response.content)
