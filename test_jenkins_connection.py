"""
Test Jenkins Connection
Run this to verify your Jenkins credentials and connection
"""

import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth

load_dotenv()

JENKINS_URL = os.getenv('JENKINS_URL', 'http://localhost:8080')
JENKINS_USER = os.getenv('JENKINS_USER')
JENKINS_TOKEN = os.getenv('JENKINS_TOKEN')

print("=" * 60)
print("Jenkins Connection Test")
print("=" * 60)
print(f"Jenkins URL: {JENKINS_URL}")
print(f"Username: {JENKINS_USER}")
print(f"Token: {'*' * 10 if JENKINS_TOKEN else 'NOT SET'}")
print("=" * 60)

if not JENKINS_USER or not JENKINS_TOKEN:
    print("\n❌ ERROR: Jenkins credentials not configured in .env file")
    print("\nPlease set:")
    print("  JENKINS_URL=http://localhost:8080")
    print("  JENKINS_USER=your-username")
    print("  JENKINS_TOKEN=your-api-token")
    exit(1)

# Test 1: Basic connectivity
print("\n[Test 1] Testing basic connectivity...")
try:
    response = requests.get(f"{JENKINS_URL}/api/json", timeout=5, verify=False)
    if response.status_code == 200:
        print("✅ Jenkins is reachable (no auth)")
    elif response.status_code == 403:
        print("✅ Jenkins is reachable (auth required)")
    else:
        print(f"⚠️  Jenkins returned status code: {response.status_code}")
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to Jenkins - is it running?")
    print(f"   Make sure Jenkins is running on {JENKINS_URL}")
    exit(1)
except Exception as e:
    print(f"❌ Connection error: {e}")
    exit(1)

# Test 2: Authentication
print("\n[Test 2] Testing authentication...")
try:
    auth = HTTPBasicAuth(JENKINS_USER, JENKINS_TOKEN)
    response = requests.get(f"{JENKINS_URL}/api/json", auth=auth, timeout=5, verify=False)
    
    if response.status_code == 200:
        print("✅ Authentication successful")
    elif response.status_code == 401:
        print("❌ Authentication failed - check username/token")
        exit(1)
    elif response.status_code == 403:
        print("❌ Forbidden - user doesn't have API access")
        exit(1)
    else:
        print(f"⚠️  Unexpected status: {response.status_code}")
except Exception as e:
    print(f"❌ Auth test failed: {e}")
    exit(1)

# Test 3: Fetch jobs
print("\n[Test 3] Fetching Jenkins jobs...")
try:
    response = requests.get(
        f"{JENKINS_URL}/api/json?tree=jobs[name]",
        auth=auth,
        timeout=10,
        verify=False
    )
    response.raise_for_status()
    data = response.json()
    jobs = data.get('jobs', [])
    
    print(f"✅ Found {len(jobs)} Jenkins jobs:")
    for job in jobs[:10]:  # Show first 10
        print(f"   - {job['name']}")
    
    if len(jobs) > 10:
        print(f"   ... and {len(jobs) - 10} more")
    
    if len(jobs) == 0:
        print("   ⚠️  No jobs found - create some jobs in Jenkins first")
        
except Exception as e:
    print(f"❌ Failed to fetch jobs: {e}")
    exit(1)

# Test 4: Check for failed builds
print("\n[Test 4] Checking for failed builds...")
failed_count = 0
for job in jobs[:5]:  # Check first 5 jobs
    try:
        job_name = job['name']
        response = requests.get(
            f"{JENKINS_URL}/job/{job_name}/api/json?tree=builds[number,result]{{0,5}}",
            auth=auth,
            timeout=10,
            verify=False
        )
        if response.status_code == 200:
            builds = response.json().get('builds', [])
            for build in builds:
                if build.get('result') in ['FAILURE', 'UNSTABLE', 'ABORTED']:
                    failed_count += 1
                    print(f"   Found failed build: {job_name}#{build['number']} - {build['result']}")
    except:
        continue

if failed_count > 0:
    print(f"\n✅ Found {failed_count} failed builds to analyze")
else:
    print("\n⚠️  No failed builds found - trigger some failing builds to test")

print("\n" + "=" * 60)
print("✅ All tests passed! Jenkins integration is ready")
print("=" * 60)
print("\nYou can now:")
print("1. Uncomment Jenkins config in .env")
print("2. Run: python src/main/app.py")
print("3. App will auto-poll Jenkins every 5 minutes")
