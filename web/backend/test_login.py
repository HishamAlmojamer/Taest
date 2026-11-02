import urllib.request
import urllib.error
import json


def main():
    data = json.dumps({"username": "admin", "password": "admin123"}).encode()
    req = urllib.request.Request(
        "http://localhost:8001/api/auth/login",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print("Status:", resp.status)
            print("Body:", resp.read().decode())
    except urllib.error.HTTPError as e:
        print("Status:", e.code)
        print("Body:", e.read().decode())


if __name__ == "__main__":
    main()
