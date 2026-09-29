"""Deploy site to Cloudflare Pages via direct upload API (Bearer token auth).

Auth: reads API token from ~/.cloudflare/config.json
Project: serverbudget-site (direct-upload, NOT git-connected)
Site dir: live-site/
After deploy: adds custom domain serverbudget.com + updates DNS CNAME
"""
import hashlib, os, sys, json, mimetypes, urllib.request, urllib.error, urllib.parse

# --- Config: read stored Bearer token ---
HOME = os.path.expanduser("~")
TOKEN_FILE = os.path.join(HOME, ".cloudflare", "config.json")
with open(TOKEN_FILE, "r", encoding="utf-8-sig") as f:
    _cfg = json.load(f)
TOKEN = _cfg["token"]

ACCT = "9cbeb694a120d167d786b4a7b470cb19"
SITE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "live-site")
PROJECT = "serverbudget-site"
ZONE_NAME = "serverbudget.com"
API = "https://api.cloudflare.com/client/v4"

def cf_request(method, path, data=None):
    """API request using Bearer token auth."""
    h = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    req = urllib.request.Request(f"{API}{path}", data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return json.loads(body)
        except Exception:
            return {"success": False, "errors": [{"message": body[:500]}]}

def upload_file(jwt, url_path, content, mime):
    """Upload a single file using the upload JWT."""
    upload_url = f"{API}/pages/assets/upload"
    headers = {
        "Authorization": f"Bearer {jwt}",
        "Content-Type": mime,
    }
    # Use query param for file name
    full_url = f"{upload_url}?fileName={urllib.parse.quote(url_path)}"
    req = urllib.request.Request(full_url, data=content, headers=headers, method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

# === Step 1: Create project (direct-upload type) ===
print("=== [1] Create Pages project ===", flush=True)
r = cf_request("POST", f"/accounts/{ACCT}/pages/projects",
               data=json.dumps({"name": PROJECT, "production_branch": "main"}).encode())
if r.get("success"):
    sub = r["result"].get("subdomain", "?")
    print(f"  Project '{PROJECT}' created. subdomain: {sub}")
elif any("already" in str(e).lower() or "exists" in str(e).lower() for e in r.get("errors", [])):
    print(f"  Project '{PROJECT}' already exists, continuing.")
    r2 = cf_request("GET", f"/accounts/{ACCT}/pages/projects/{PROJECT}")
    if r2.get("success"):
        sub = r2["result"].get("subdomain", "?")
        print(f"  subdomain: {sub}")
    else:
        print(f"  Cannot find project: {r2.get('errors')}", file=sys.stderr)
        sys.exit(1)
else:
    print(f"  Create FAILED: {r.get('errors')}", file=sys.stderr)
    sys.exit(1)

# === Step 2: Get upload JWT ===
print("\n=== [2] Get upload JWT ===", flush=True)
r = cf_request("POST", f"/accounts/{ACCT}/pages/projects/{PROJECT}/upload-token")
if not r.get("success"):
    print(f"  Upload token FAILED: {r.get('errors')}", file=sys.stderr)
    sys.exit(1)
jwt = r["result"]["jwt"]
print(f"  JWT obtained (len={len(jwt)})")

# === Step 3: Upload each file ===
print("\n=== [3] Upload files ===", flush=True)
files = sorted(os.listdir(SITE_DIR))
manifest = {}
for fname in files:
    fpath = os.path.join(SITE_DIR, fname)
    if not os.path.isfile(fpath):
        continue
    with open(fpath, "rb") as f:
        content = f.read()
    sha = hashlib.sha256(content).hexdigest()
    file_hash = f"sha256-{sha}"
    size = len(content)
    mime = mimetypes.guess_type(fname)[0] or "application/octet-stream"
    url_path = "/" + fname

    manifest[url_path] = {"hash": file_hash, "size": size, "contentType": mime}

    code, body = upload_file(jwt, url_path, content, mime)
    ok = code in (200, 201)
    if not ok:
        # Retry with X-File-Name header instead of query param
        upload_url = f"{API}/pages/assets/upload"
        headers = {
            "Authorization": f"Bearer {jwt}",
            "Content-Type": mime,
            "X-File-Name": url_path,
        }
        req = urllib.request.Request(upload_url, data=content, headers=headers, method="PUT")
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                code, body = resp.status, resp.read().decode()
                ok = code in (200, 201)
        except urllib.error.HTTPError as e:
            code, body = e.code, e.read().decode()
            ok = code in (200, 201)
    if not ok:
        print(f"  FAIL {fname}: HTTP {code} - {body[:200]}", file=sys.stderr)
        sys.exit(1)
    print(f"  OK   {fname:50} {size:>7} bytes")

print(f"\n  Manifest: {len(manifest)} files")

# === Step 4: Create deployment ===
print("\n=== [4] Create deployment ===", flush=True)
deploy_body = {
    "manifest": manifest,
    "deployment_trigger": {
        "type": "direct-upload",
        "metadata": {"commit_hash": hashlib.sha256(json.dumps(manifest).encode()).hexdigest()[:40]}
    },
}
r = cf_request("POST", f"/accounts/{ACCT}/pages/projects/{PROJECT}/deployments",
               data=json.dumps(deploy_body).encode())
if not r.get("success"):
    print(f"  Deploy FAILED: {r.get('errors')}", file=sys.stderr)
    print(json.dumps(r, indent=2)[:1000], file=sys.stderr)
    sys.exit(1)

deploy = r["result"]
deploy_url = deploy.get("url", "?")
deploy_id = deploy.get("id", "?")
print(f"  Deploy SUCCESS!")
print(f"  ID:       {deploy_id}")
print(f"  URL:      {deploy_url}")
print(f"  Stage:    {deploy.get('latest_stage', {}).get('name', '?')} / {deploy.get('latest_stage', {}).get('status', '?')}")
print(f"  Env:      {deploy.get('environment', '?')}")

# === Step 5: Add custom domain serverbudget.com ===
print("\n=== [5] Add custom domain ===", flush=True)
r = cf_request("POST", f"/accounts/{ACCT}/pages/projects/{PROJECT}/domains",
               data=json.dumps({"name": ZONE_NAME}).encode())
if r.get("success"):
    print(f"  Custom domain '{ZONE_NAME}' added to project.")
elif any("already" in str(e).lower() or "exist" in str(e).lower() for e in r.get("errors", [])):
    print(f"  Custom domain '{ZONE_NAME}' already exists on project.")
else:
    print(f"  Custom domain FAILED: {r.get('errors')}", file=sys.stderr)
    print("  (May need manual DNS verification - continuing)")

# === Step 6: Update DNS CNAME to point to new project ===
print("\n=== [6] Update DNS CNAME ===", flush=True)
# Get zone ID for serverbudget.com
r = cf_request("GET", "/zones")
zone_id = None
if r.get("success"):
    for z in r["result"]:
        if z["name"] == ZONE_NAME:
            zone_id = z["id"]
            break
if not zone_id:
    print(f"  Zone '{ZONE_NAME}' not found!", file=sys.stderr)
else:
    # Get existing CNAME records for @
    r = cf_request("GET", f"/zones/{zone_id}/dns_records?type=CNAME")
    if r.get("success"):
        updated = False
        for rec in r["result"]:
            if rec["name"] == ZONE_NAME:
                # Update this CNAME to point to the new project's pages.dev subdomain
                # Get the project subdomain
                r_proj = cf_request("GET", f"/accounts/{ACCT}/pages/projects/{PROJECT}")
                if r_proj.get("success"):
                    new_target = r_proj["result"].get("subdomain", "?")
                    update_data = json.dumps({
                        "type": "CNAME",
                        "name": ZONE_NAME,
                        "content": new_target,
                        "proxied": True,
                    }).encode()
                    r_upd = cf_request("PUT", f"/zones/{zone_id}/dns_records/{rec['id']}", data=update_data)
                    if r_upd.get("success"):
                        print(f"  CNAME updated: {ZONE_NAME} -> {new_target}")
                        updated = True
                    else:
                        print(f"  CNAME update FAILED: {r_upd.get('errors')}", file=sys.stderr)
                break
        if not updated:
            # Create new CNAME
            r_proj = cf_request("GET", f"/accounts/{ACCT}/pages/projects/{PROJECT}")
            if r_proj.get("success"):
                new_target = r_proj["result"].get("subdomain", "?")
                create_data = json.dumps({
                    "type": "CNAME",
                    "name": ZONE_NAME,
                    "content": new_target,
                    "proxied": True,
                }).encode()
                r_new = cf_request("POST", f"/zones/{zone_id}/dns_records", data=create_data)
                if r_new.get("success"):
                    print(f"  CNAME created: {ZONE_NAME} -> {new_target}")
                else:
                    print(f"  CNAME create FAILED: {r_new.get('errors')}", file=sys.stderr)

print("\n=== DEPLOY COMPLETE ===")
print(f"  Project:   {PROJECT}")
print(f"  Deploy URL: {deploy_url}")
print(f"  Verify:    https://{ZONE_NAME}/cheap-vps-hosting.html")
