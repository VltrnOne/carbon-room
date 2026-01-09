#!/usr/bin/env python3
"""Quick CLI tool for Global Dataroom"""

import requests
import sys
import json

BASE_URL = "http://localhost:8003"

def invoke(keyword: str, user_id: str = "cli_user"):
    """Invoke a protocol by keyword"""
    try:
        r = requests.post(f"{BASE_URL}/api/invoke", json={"keyword": keyword, "user_id": user_id})
        print(json.dumps(r.json(), indent=2))
    except requests.exceptions.ConnectionError:
        print("Error: Server not running. Start with: python api/server.py")

def list_protocols():
    """List all protocols"""
    try:
        r = requests.get(f"{BASE_URL}/api/protocols")
        data = r.json()
        if not data["protocols"]:
            print("No protocols registered yet.")
            return
        print("\nAvailable Protocols:")
        print("-" * 40)
        for p in data["protocols"]:
            print(f"  [{p['type'].upper()}] {p['name']}")
            print(f"    Tags: {', '.join(p['tags'])}")
            print(f"    {p['description'][:60]}...")
            print()
    except requests.exceptions.ConnectionError:
        print("Error: Server not running. Start with: python api/server.py")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python quick_start.py list              - List all protocols")
        print("  python quick_start.py invoke <keyword>  - Invoke a protocol")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "list":
        list_protocols()
    elif cmd == "invoke" and len(sys.argv) >= 3:
        invoke(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "cli_user")
    else:
        print("Unknown command")
