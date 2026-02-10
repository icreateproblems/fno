"""
Helper script to get Instagram Graph API access token
Run this to get step-by-step instructions
"""
import webbrowser
import os
from dotenv import load_dotenv

load_dotenv()

BLUE = '\033[94m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

print(f"\n{BLUE}{'='*70}{RESET}")
print(f"{BLUE}Instagram Graph API Token Generator{RESET}")
print(f"{BLUE}{'='*70}{RESET}\n")

app_id = os.getenv('INSTAGRAM_APP_ID')
business_account_id = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')

if not app_id:
    print(f"{YELLOW}⚠ INSTAGRAM_APP_ID not found in .env{RESET}")
    print("You'll need to select your app manually in Graph API Explorer\n")
else:
    print(f"Using App ID: {app_id}\n")

print(f"{GREEN}Step 1: Open Facebook Graph API Explorer{RESET}")
print("We'll open this URL in your browser:")
print(f"{BLUE}https://developers.facebook.com/tools/explorer/{RESET}\n")

input("Press Enter to open Graph API Explorer...")
webbrowser.open("https://developers.facebook.com/tools/explorer/")

print(f"\n{GREEN}Step 2: Configure Permissions{RESET}")
print("-" * 70)
print("In the Graph API Explorer:")
print("  1. Select your app from the dropdown (if not already selected)")
print("  2. Select your Instagram Business Account")
print("  3. Click on 'Permissions' dropdown")
print("  4. Add these permissions:")
print(f"     {BLUE}• instagram_basic{RESET}")
print(f"     {BLUE}• instagram_content_publish{RESET}")
print(f"     {BLUE}• pages_read_engagement{RESET}")
print("  5. Click 'Generate Access Token'")
print("  6. Approve the permissions when prompted\n")

print(f"{GREEN}Step 3: Copy Your Token{RESET}")
print("-" * 70)
print("After generating:")
print("  1. Copy the entire access token (starts with IGAA... or EAA...)")
print("  2. IMPORTANT: Copy the ENTIRE token, it's very long!")
print("  3. The token might wrap to multiple lines - copy it all\n")

token = input(f"{YELLOW}Paste your access token here:{RESET} ").strip()

if not token:
    print(f"\n{RED}❌ No token provided{RESET}")
    exit(1)

# Basic validation
if len(token) < 50:
    print(f"\n{RED}❌ Token too short - make sure you copied the entire token{RESET}")
    exit(1)

if not (token.startswith('IGAA') or token.startswith('EAA')):
    print(f"\n{YELLOW}⚠ Token doesn't start with IGAA or EAA{RESET}")
    print("This might not be a valid Instagram Graph API token")
    print("Make sure you're using the Graph API Explorer, not Instagram Basic Display")
    continue_anyway = input("Continue anyway? (y/n): ").lower()
    if continue_anyway != 'y':
        exit(1)

# Test the token
print(f"\n{BLUE}Testing token...{RESET}")

import requests

if business_account_id:
    url = f"https://graph.facebook.com/v24.0/{business_account_id}"
    params = {
        'fields': 'username,followers_count',
        'access_token': token
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            username = data.get('username', 'Unknown')
            followers = data.get('followers_count', 0)
            print(f"{GREEN}✓ Token is valid!{RESET}")
            print(f"  Account: @{username}")
            print(f"  Followers: {followers:,}")
        else:
            error = response.json()
            print(f"{RED}✗ Token validation failed:{RESET}")
            print(f"  {error.get('error', {}).get('message', 'Unknown error')}")
            print("\nMake sure you:")
            print("  1. Added the correct permissions")
            print("  2. Selected your Instagram Business Account")
            print("  3. Copied the ENTIRE token")
            exit(1)
    except Exception as e:
        print(f"{YELLOW}⚠ Could not test token: {e}{RESET}")
        print("Continuing anyway...\n")
else:
    print(f"{YELLOW}⚠ No business account ID to test against{RESET}")
    print("Continuing anyway...\n")

# Update .env file
print(f"\n{GREEN}Step 4: Update .env file{RESET}")
print("-" * 70)

env_path = '.env'
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Replace or add token
    token_found = False
    for i, line in enumerate(lines):
        if line.startswith('INSTAGRAM_ACCESS_TOKEN='):
            lines[i] = f'INSTAGRAM_ACCESS_TOKEN={token}\n'
            token_found = True
            break
    
    if not token_found:
        # Add token before Instagram business account ID line
        for i, line in enumerate(lines):
            if line.startswith('INSTAGRAM_BUSINESS_ACCOUNT_ID='):
                lines.insert(i, f'INSTAGRAM_ACCESS_TOKEN={token}\n')
                break
    
    with open(env_path, 'w') as f:
        f.writelines(lines)
    
    print(f"{GREEN}✓ Token saved to .env{RESET}\n")
else:
    print(f"{RED}❌ .env file not found{RESET}")
    print(f"Please manually add to .env:")
    print(f"\nINSTAGRAM_ACCESS_TOKEN={token}\n")
    exit(1)

print(f"{GREEN}{'='*70}{RESET}")
print(f"{GREEN}✅ Setup complete!{RESET}")
print(f"{GREEN}{'='*70}{RESET}\n")

print("Next steps:")
print(f"  1. Run: {BLUE}python verify_instagram_setup.py{RESET}")
print(f"  2. All checks should pass ✓")
print(f"  3. Run: {BLUE}python scripts/post_instagram_graph.py{RESET}")
print(f"  4. Your first post should go live! 🎉\n")

print(f"{YELLOW}Note: Short-term tokens expire in 1 hour{RESET}")
print(f"For long-lived tokens (60 days), see: {BLUE}docs/INSTAGRAM_GRAPH_SETUP.md{RESET}\n")
