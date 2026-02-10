"""
Debug Instagram Graph API setup issues
Identifies common problems with account setup
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

BLUE = '\033[94m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

print(f"\n{BLUE}{'='*70}{RESET}")
print(f"{BLUE}Instagram Graph API Diagnostic Tool{RESET}")
print(f"{BLUE}{'='*70}{RESET}\n")

app_id = os.getenv('INSTAGRAM_APP_ID')
business_account_id = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')
access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')

print(f"{YELLOW}Current Configuration:{RESET}")
print(f"  App ID: {app_id or 'NOT SET'}")
print(f"  Business Account ID: {business_account_id or 'NOT SET'}")
print(f"  Access Token: {access_token[:50] if access_token else 'NOT SET'}...")
print()

# Check 1: Token format
print(f"{BLUE}[1/5] Checking Token Format{RESET}")
print("-" * 70)
if not access_token:
    print(f"{RED}✗ No access token found{RESET}\n")
elif '|' in access_token:
    print(f"{YELLOW}⚠ Token format looks like App Access Token (has '|'){RESET}")
    print(f"  You need a User Access Token, not an App Access Token")
    print(f"  Get it from: https://developers.facebook.com/tools/explorer/\n")
elif '@' in access_token or '$' in access_token or '!' in access_token:
    print(f"{RED}✗ Token contains unusual characters (@, $, !){RESET}")
    print(f"  This suggests the token was corrupted during copy/paste")
    print(f"  Try copying again - ensure you get the ENTIRE token\n")
elif len(access_token) < 100:
    print(f"{YELLOW}⚠ Token seems short (length: {len(access_token)}){RESET}")
    print(f"  Valid Instagram tokens are usually 200+ characters")
    print(f"  You may have copied only part of it\n")
else:
    print(f"{GREEN}✓ Token format looks reasonable (length: {len(access_token)}){RESET}\n")

# Check 2: Test with Facebook Graph API Debug tool
print(f"{BLUE}[2/5] Testing Token with Facebook Debug Tool{RESET}")
print("-" * 70)
if access_token and app_id:
    try:
        debug_url = "https://graph.facebook.com/v24.0/debug_token"
        params = {
            'input_token': access_token,
            'access_token': f"{app_id}|{os.getenv('INSTAGRAM_APP_SECRET', 'SECRET_NOT_SET')}"
        }
        
        # Try without app secret first (public info only)
        params['access_token'] = access_token
        
        response = requests.get(debug_url, params={'input_token': access_token, 'access_token': access_token}, timeout=10)
        
        if response.status_code == 200:
            data = response.json().get('data', {})
            print(f"{GREEN}✓ Token is valid{RESET}")
            print(f"  App ID: {data.get('app_id', 'Unknown')}")
            print(f"  User ID: {data.get('user_id', 'Unknown')}")
            print(f"  Expires: {data.get('expires_at', 'Unknown')}")
            print(f"  Scopes: {', '.join(data.get('scopes', []))}\n")
        else:
            error = response.json()
            print(f"{RED}✗ Token validation failed{RESET}")
            print(f"  Error: {error.get('error', {}).get('message', 'Unknown')}\n")
    except Exception as e:
        print(f"{YELLOW}⚠ Could not test token: {e}{RESET}\n")
else:
    print(f"{YELLOW}⚠ Skipped (missing token or app ID){RESET}\n")

# Check 3: Test Instagram Business Account access
print(f"{BLUE}[3/5] Testing Instagram Business Account Access{RESET}")
print("-" * 70)
if access_token and business_account_id:
    try:
        url = f"https://graph.facebook.com/v24.0/{business_account_id}"
        params = {
            'fields': 'id,username,name,profile_picture_url,followers_count,follows_count,media_count',
            'access_token': access_token
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"{GREEN}✓ Instagram Business Account accessible{RESET}")
            print(f"  Username: @{data.get('username', 'Unknown')}")
            print(f"  Name: {data.get('name', 'Unknown')}")
            print(f"  Followers: {data.get('followers_count', 0):,}")
            print(f"  Posts: {data.get('media_count', 0):,}\n")
        else:
            error = response.json()
            print(f"{RED}✗ Cannot access Instagram Business Account{RESET}")
            print(f"  Error: {error.get('error', {}).get('message', 'Unknown')}")
            print(f"  Error Code: {error.get('error', {}).get('code', 'Unknown')}")
            print(f"\n  Common causes:")
            print(f"    • Account is not a Business/Creator account")
            print(f"    • Account not linked to Facebook Page")
            print(f"    • Wrong Business Account ID")
            print(f"    • Token doesn't have instagram_basic permission\n")
    except Exception as e:
        print(f"{RED}✗ Request failed: {e}{RESET}\n")
else:
    print(f"{YELLOW}⚠ Skipped (missing token or business account ID){RESET}\n")

# Check 4: Test posting permissions
print(f"{BLUE}[4/5] Checking Content Publishing Permissions{RESET}")
print("-" * 70)
if access_token and business_account_id:
    try:
        # Try to get recent media to test permissions
        url = f"https://graph.facebook.com/v24.0/{business_account_id}/media"
        params = {
            'fields': 'id,timestamp,caption',
            'limit': 1,
            'access_token': access_token
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            print(f"{GREEN}✓ Can read media from account{RESET}")
            data = response.json()
            if data.get('data'):
                print(f"  Found {len(data['data'])} recent post(s)\n")
            else:
                print(f"  No recent posts found\n")
        else:
            error = response.json()
            print(f"{RED}✗ Cannot read media{RESET}")
            print(f"  Error: {error.get('error', {}).get('message', 'Unknown')}")
            print(f"  You may need 'instagram_content_publish' permission\n")
    except Exception as e:
        print(f"{YELLOW}⚠ Could not test: {e}{RESET}\n")
else:
    print(f"{YELLOW}⚠ Skipped (missing credentials){RESET}\n")

# Check 5: Account type verification
print(f"{BLUE}[5/5] Account Type Verification{RESET}")
print("-" * 70)
print(f"For Instagram Graph API to work, you MUST have:")
print(f"  {GREEN}✓{RESET} Instagram Business or Creator account")
print(f"  {GREEN}✓{RESET} Account linked to a Facebook Page")
print(f"  {GREEN}✓{RESET} Facebook Page connected to your app")
print()
print(f"To verify in Instagram app:")
print(f"  1. Go to Settings → Account")
print(f"  2. Check if you see 'Switch to Professional Account'")
print(f"     • If yes → You have a Personal account (needs conversion)")
print(f"     • If no → You likely have Business/Creator (good!)")
print(f"  3. If Business/Creator, check Settings → Account → Linked accounts")
print(f"     • Verify Facebook Page is connected")
print()

print(f"{BLUE}{'='*70}{RESET}")
print(f"{BLUE}Recommendations{RESET}")
print(f"{BLUE}{'='*70}{RESET}\n")

if access_token and '@' in access_token:
    print(f"{RED}CRITICAL: Your token appears corrupted{RESET}")
    print(f"  1. Go to: https://developers.facebook.com/tools/explorer/")
    print(f"  2. Generate a fresh token")
    print(f"  3. Copy carefully - use Ctrl+A, Ctrl+C to select all")
    print(f"  4. Paste into get_instagram_token.py\n")
elif access_token and '|' in access_token:
    print(f"{YELLOW}WARNING: You have an App Access Token{RESET}")
    print(f"  You need a User Access Token instead")
    print(f"  1. Go to: https://developers.facebook.com/tools/explorer/")
    print(f"  2. Make sure 'User Token' is selected (not 'App Token')")
    print(f"  3. Log in when prompted")
    print(f"  4. Generate and copy the token\n")
else:
    print(f"If you're still having issues:")
    print(f"  1. Verify your Instagram account is converted to Business")
    print(f"  2. Check that it's linked to a Facebook Page")
    print(f"  3. Ensure the Facebook Page is added to your app")
    print(f"  4. Use the Graph API Explorer to generate a fresh token")
    print(f"  5. Make sure all 3 permissions are granted:\n")
    print(f"     • instagram_basic")
    print(f"     • instagram_content_publish")
    print(f"     • pages_read_engagement\n")

print(f"Need help? See: {BLUE}docs/INSTAGRAM_GRAPH_SETUP.md{RESET}\n")
