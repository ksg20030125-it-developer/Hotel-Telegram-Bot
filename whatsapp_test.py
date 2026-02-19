#!/usr/bin/env python3
"""
Simple WhatsApp test sender (Twilio)

Usage (dry-run, safe):
  .\.venv\Scripts\python.exe whatsapp_test.py --to +1234567890 --body "Hello from test"

To actually send a message (unsafe to run without checking credentials):
  # set env vars or pass --sid and --token
  $env:TWILIO_SID = 'ACxxxx' ; $env:TWILIO_TOKEN = 'xxxxxxxx' ; $env:TWILIO_WHATSAPP_FROM = '+1415xxxx'
  .\.venv\Scripts\python.exe whatsapp_test.py --to +{RECIPIENT} --body "Hello" --send

Notes:
- Uses Twilio REST API (Accounts /Messages endpoint).
- By default the script runs in dry-run mode. Use --send to perform the POST.
- Prefer setting `TWILIO_SID`, `TWILIO_TOKEN`, and `TWILIO_WHATSAPP_FROM` as environment variables instead of embedding secrets.
"""

import os
import sys
import argparse
import base64
import urllib.parse
import urllib.request
import json
from typing import Optional


def send_message_twilio(sid: str, token: str, from_whatsapp: str, to_whatsapp: str, body: str) -> dict:
    """Send a WhatsApp message via Twilio REST API and return parsed JSON response."""
    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    payload = {
        "From": f"whatsapp:{from_whatsapp}",
        "To": f"whatsapp:{to_whatsapp}",
        "Body": body
    }
    data = urllib.parse.urlencode(payload).encode("utf-8")

    auth_raw = f"{sid}:{token}".encode("utf-8")
    auth_b64 = base64.b64encode(auth_raw).decode("ascii")

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Basic {auth_b64}")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(req, timeout=30) as resp:
        resp_text = resp.read().decode("utf-8")
        try:
            return json.loads(resp_text)
        except Exception:
            return {"raw": resp_text}


def mask_secret(s: Optional[str]) -> str:
    if not s:
        return "(missing)"
    if len(s) <= 6:
        return "*" * len(s)
    return s[:3] + "*" * (len(s) - 6) + s[-3:]


def main():
    parser = argparse.ArgumentParser(description="Simple Twilio WhatsApp test sender (dry-run by default).")
    parser.add_argument("--sid", help="Twilio Account SID (or set TWILIO_SID env var)")
    parser.add_argument("--token", help="Twilio Auth Token (or set TWILIO_TOKEN env var)")
    parser.add_argument("--from", dest="from_whatsapp", help="WhatsApp-enabled Twilio number (E164, no 'whatsapp:' prefix). Can be set via TWILIO_WHATSAPP_FROM env var.")
    parser.add_argument("--to", required=True, help="Recipient phone number in E.164 format (e.g. +381601234567)")
    parser.add_argument("--body", required=True, help="Message body to send")
    parser.add_argument("--send", action="store_true", help="Actually send the message (default: dry-run)")
    args = parser.parse_args()

    sid = args.sid or os.environ.get("TWILIO_SID")
    token = args.token or os.environ.get("TWILIO_TOKEN")
    from_whatsapp = args.from_whatsapp or os.environ.get("TWILIO_WHATSAPP_FROM")

    # Dry-run: show what would be sent; require --send to do network call
    print("--- WhatsApp Test (Twilio) ---")
    print(f"To: {args.to}")
    print(f"From: {from_whatsapp or '(missing)'}")
    print(f"Body: {args.body[:200]}")
    print(f"SID: {mask_secret(sid)}")
    print(f"Token: {mask_secret(token)}")
    print(f"Action: {'SEND' if args.send else 'DRY-RUN (no network)'}")
    print("------------------------------")

    if not args.send:
        print("Dry-run complete. No network requests performed. To actually send, re-run with --send and ensure credentials are provided via env vars or --sid/--token and --from.")
        return

    # perform validations before sending
    missing = []
    if not sid:
        missing.append('TWILIO_SID')
    if not token:
        missing.append('TWILIO_TOKEN')
    if not from_whatsapp:
        missing.append('TWILIO_WHATSAPP_FROM')

    if missing:
        print(f"Cannot send message — missing: {', '.join(missing)}")
        print("Set environment variables or supply --sid/--token/--from arguments.")
        return

    # Send
    try:
        resp = send_message_twilio(sid, token, from_whatsapp, args.to, args.body)
        print("Message sent. Twilio response:")
        print(json.dumps(resp, ensure_ascii=False, indent=2))
    except urllib.error.HTTPError as he:
        err_text = he.read().decode('utf-8', errors='ignore')
        print(f"HTTPError: {he.code} {he.reason}")
        try:
            print(json.dumps(json.loads(err_text), ensure_ascii=False, indent=2))
        except Exception:
            print(err_text)
    except Exception as e:
        print(f"Error sending message: {e}")


if __name__ == '__main__':
    main()
