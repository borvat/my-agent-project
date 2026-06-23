#!/usr/bin/env python3
import os
import sys
import json
import argparse
import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "https://borvat.stockitup.nl/api/v1"
ENDPOINT = "/sellers/"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-get", action="store_true")
    args = parser.parse_args()

    if not args.confirm_get:
        print("PREFLIGHT BLOCKED: add --confirm-get to execute GET /sellers/")
        sys.exit(2)

    client_id = os.environ.get("STOCKITUP_CLIENT_ID")
    client_secret = os.environ.get("STOCKITUP_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("ERROR: Missing STOCKITUP_CLIENT_ID or STOCKITUP_CLIENT_SECRET")
        sys.exit(1)

    url = BASE_URL + ENDPOINT

    try:
        r = requests.get(
            url,
            auth=HTTPBasicAuth(client_id, client_secret),
            headers={"Accept": "application/json"},
            timeout=20,
        )

        print(f"HTTP_STATUS: {r.status_code}")

        try:
            data = r.json()
        except Exception:
            print("ERROR: Response is not JSON")
            print(r.text[:500])
            sys.exit(1)

        if r.status_code != 200:
            print(json.dumps(data, ensure_ascii=False, indent=2)[:1000])
            sys.exit(1)

        if isinstance(data, dict):
            sellers = data.get("results") or data.get("items") or data.get("sellers") or []
        elif isinstance(data, list):
            sellers = data
        else:
            sellers = []

        print(f"count: {len(sellers)}")

        fields = sorted(set().union(*(s.keys() for s in sellers if isinstance(s, dict)))) if sellers else []
        print("available_fields:", fields)

        for s in sellers:
            if isinstance(s, dict):
                print({
                    "seller_id": s.get("id"),
                    "name": s.get("name")
                })

    except requests.RequestException as e:
        print("REQUEST_ERROR:", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
