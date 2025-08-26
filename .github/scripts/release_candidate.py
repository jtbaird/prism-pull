import requests
import tomllib

url = f"https://pypi.org/pypi/prism-pull/json"
resp = requests.get(url)
if resp.status_code == 200:
    data = resp.json()
    latest = data["info"]["version"]

with open("pyproject.toml", "rb") as f:
    data = tomllib.load(f)

if latest == data["project"]["version"]:
    raise ValueError("Latest version on PyPI matches pyproject.toml")
