
"""
Azure OpenAI Connection Diagnostic Tool
========================================
Run this script BEFORE running the chatbot to verify your Azure OpenAI setup.

Usage: python test_connection.py
"""

import sys

# ─── YOUR CREDENTIALS (paste the same values from app.py) ───────────────────
API_KEY = "808cf0ccab8445b39c6d8767a7e2c433"                     # ← Paste your Azure OpenAI key
ENDPOINT = "https://entgptopenai.openai.azure.com"   # ← Your endpoint
DEPLOYMENT = "gpt-4o-mini"                            # ← Your deployment name
API_VERSION = "2023-07-01-preview"                    # ← API version

# ════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  AZURE OPENAI CONNECTION DIAGNOSTIC")
print("=" * 60)

# ─── Test 1: Check if key is provided ───────────────────────────────────────
print("\n[1/6] Checking API key...")
if not API_KEY or API_KEY.strip() == "":
    print("  ❌ FAIL: API key is empty!")
    print("  → Paste your key in this script on line 12")
    sys.exit(1)
else:
    print(f"  ✅ Key present: {API_KEY[:6]}...{API_KEY[-4:]} (length: {len(API_KEY)})")

# ─── Test 2: Check endpoint format ─────────────────────────────────────────
print("\n[2/6] Checking endpoint format...")
issues = []
if not ENDPOINT.startswith("https://"):
    issues.append("Must start with https://")
if ENDPOINT.endswith("/"):
    print(f"  ⚠️  Trailing slash detected — removing it")
    ENDPOINT = ENDPOINT.rstrip("/")
if "openai.azure.com" not in ENDPOINT:
    issues.append("Should contain 'openai.azure.com'")
if issues:
    for i in issues:
        print(f"  ❌ {i}")
else:
    print(f"  ✅ Endpoint looks correct: {ENDPOINT}")

# ─── Test 3: Check network connectivity ────────────────────────────────────
print("\n[3/6] Testing network connectivity...")
import urllib.request
import urllib.error
try:
    req = urllib.request.Request(ENDPOINT, method="HEAD")
    urllib.request.urlopen(req, timeout=10)
    print(f"  ✅ Can reach {ENDPOINT}")
except urllib.error.HTTPError as e:
    # HTTP errors mean we CAN reach it (just not authorized without proper headers)
    print(f"  ✅ Can reach endpoint (HTTP {e.code} — expected without auth headers)")
except urllib.error.URLError as e:
    print(f"  ❌ FAIL: Cannot reach endpoint!")
    print(f"  Error: {e.reason}")
    print(f"  → Check your internet connection")
    print(f"  → Check if your network/firewall blocks Azure endpoints")
    print(f"  → Check if endpoint URL is correct")
    print(f"  → If on VPN/corporate network, try without VPN")
    sys.exit(1)
except Exception as e:
    print(f"  ❌ FAIL: {e}")
    sys.exit(1)

# ─── Test 4: Check openai package ──────────────────────────────────────────
print("\n[4/6] Checking openai package...")
try:
    import openai
    print(f"  ✅ openai package version: {openai.__version__}")
    
    major_ver = int(openai.__version__.split(".")[0])
    if major_ver < 1:
        print(f"  ❌ WARNING: openai version {openai.__version__} is too old!")
        print(f"  → Run: pip install --upgrade openai")
except ImportError:
    print("  ❌ FAIL: openai package not installed!")
    print("  → Run: pip install openai")
    sys.exit(1)

# ─── Test 5: Test API versions ─────────────────────────────────────────────
print("\n[5/6] Testing API connection...")

from openai import AzureOpenAI

# Try multiple API versions in case the configured one doesn't work
api_versions_to_try = [
    API_VERSION,             # User's configured version first
    "2024-08-01-preview",
    "2024-02-15-preview",
    "2023-12-01-preview",
    "2023-07-01-preview",
]
# Remove duplicates while preserving order
seen = set()
api_versions_to_try = [v for v in api_versions_to_try if not (v in seen or seen.add(v))]

working_version = None

for version in api_versions_to_try:
    try:
        test_client = AzureOpenAI(
            api_key=API_KEY,
            api_version=version,
            azure_endpoint=ENDPOINT,
        )
        response = test_client.chat.completions.create(
            model=DEPLOYMENT,
            messages=[{"role": "user", "content": "Say OK"}],
            max_tokens=5,
            temperature=0,
        )
        reply = response.choices[0].message.content.strip()
        print(f"  ✅ api_version '{version}' → WORKS! Response: \"{reply}\"")
        working_version = version
        break
    except openai.AuthenticationError as e:
        print(f"  ❌ api_version '{version}' → AUTHENTICATION FAILED")
        print(f"     Error: {e}")
        print(f"     → Your API key is invalid or expired")
        print(f"     → Get a new key from Azure Portal → OpenAI resource → Keys and Endpoint")
        break
    except openai.NotFoundError as e:
        print(f"  ❌ api_version '{version}' → NOT FOUND")
        print(f"     Error: {e}")
        print(f"     → Deployment '{DEPLOYMENT}' may not exist")
        print(f"     → Check Azure AI Studio → Deployments for the exact name")
        if "DeploymentNotFound" in str(e):
            break
    except openai.APIConnectionError as e:
        print(f"  ❌ api_version '{version}' → CONNECTION ERROR")
        print(f"     Error: {e}")
        if "certificate" in str(e).lower() or "ssl" in str(e).lower():
            print(f"     → SSL/Certificate issue. Try: pip install certifi")
            print(f"     → Or set: import ssl; ssl._create_default_https_context = ssl._create_unverified_context")
        elif "proxy" in str(e).lower():
            print(f"     → Proxy issue. Check your network proxy settings")
        else:
            print(f"     → Network issue — firewall, VPN, or proxy may be blocking")
            print(f"     → Try: pip install --upgrade openai httpx")
        break
    except openai.RateLimitError:
        print(f"  ⚠️  api_version '{version}' → Rate limited (but connection works!)")
        working_version = version
        break
    except openai.APIStatusError as e:
        print(f"  ❌ api_version '{version}' → API Error (status {e.status_code})")
        print(f"     {e.message}")
    except Exception as e:
        print(f"  ❌ api_version '{version}' → {type(e).__name__}: {e}")

# ─── Test 6: Summary ───────────────────────────────────────────────────────
print("\n" + "=" * 60)
if working_version:
    print("  ✅ CONNECTION SUCCESSFUL!")
    print(f"\n  Working configuration:")
    print(f"    Endpoint   : {ENDPOINT}")
    print(f"    Deployment : {DEPLOYMENT}")
    print(f"    API Version: {working_version}")
    print(f"    Key        : {API_KEY[:6]}...{API_KEY[-4:]}")
    
    if working_version != API_VERSION:
        print(f"\n  ⚠️  NOTE: Your configured api_version '{API_VERSION}' didn't work.")
        print(f"  → Update app.py to use api_version='{working_version}'")
    
    print(f"\n  Copy this to your app.py:\n")
    print(f'    client = AzureOpenAI(')
    print(f'        api_key="{API_KEY[:6]}...YOUR_FULL_KEY",')
    print(f'        api_version="{working_version}",')
    print(f'        azure_endpoint="{ENDPOINT}",')
    print(f'    )')
    print(f'    DEPLOYMENT_NAME = "{DEPLOYMENT}"')
else:
    print("  ❌ CONNECTION FAILED")
    print("\n  Common fixes:")
    print("  1. Verify API key in Azure Portal → OpenAI resource → Keys and Endpoint")
    print("  2. Verify deployment name in Azure AI Studio → Deployments")
    print("  3. Check if resource is in an active Azure subscription")
    print("  4. Try: pip install --upgrade openai httpx certifi")
    print("  5. If on corporate network/VPN, try from a different network")
    print("  6. Check if Azure OpenAI resource region supports gpt-4o-mini")

print("=" * 60 + "\n")