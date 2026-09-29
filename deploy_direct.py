"""Deploy live-site to Cloudflare Pages via direct upload (multipart form-data via curl).

Reads Bearer token from ~/.cloudflare/config.json
Uses curl subprocess for reliable multipart form-data handling.
"""
import hashlib, os, sys, json, mimetypes, subprocess, tempfile

# Config
HOME = os.path.expanduser("~")
with open(os.path.join(HOME, ".cloudflare", "config.json"), "r", encoding="utf-8-sig") as f:
    cfg = json.load(f)
TOKEN = cfg["token"]
ACCT = "9cbeb694a120d167d786b4a7b470cb19"
SITE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "live-site")
PROJECT = "serverbudget-site"
ZONE_NAME = "serverbudget.com"
API = "https://api.cloudflare.com/client/v4"

# === Step 1: Build manifest ===
print("=== [1] Build manifest ===", flush=True)
manifest = {}
file_list = []
for fname in sorted(os.listdir(SITE_DIR)):
    fpath = os.path.join(SITE_DIR, fname)
    if not os.path.isfile(fpath):
        continue
    with open(fpath, "rb") as f:
        content = f.read()
    sha = hashlib.sha256(content).hexdigest()
    mime = mimetypes.guess_type(fname)[0] or "application/octet-stream"
    url_path = "/" + fname
    manifest[url_path] = {"hash": f"sha256-{sha}", "size": len(content), "contentType": mime}
    file_list.append((url_path, fpath))
print(f"  {len(manifest)} files in manifest")

# === Step 2: Write manifest to temp file ===
manifest_file = os.path.join(SITE_DIR, "..", "manifest.json")
manifest_file = os.path.normpath(manifest_file)
with open(manifest_file, "w") as f:
    json.dump(manifest, f)

# === Step 3: Build curl command for deployment creation ===
print("\n=== [2] Create deployment via curl (multipart) ===", flush=True)

deploy_url = f"{API}/accounts/{ACCT}/pages/projects/{PROJECT}/deployments"

# Build curl arguments
curl_args = [
    "curl", "-s", "-X", "POST", deploy_url,
    "-H", f"Authorization: Bearer {TOKEN}",
    "-F", f"manifest=@{manifest_file};type=application/json",
]

# Add each file as a form field
for url_path, fpath in file_list:
    curl_args.extend(["-F", f"{url_path}=@{fpath}"])

# Write curl args to a temp script for execution
# Using subprocess directly
result = subprocess.run(curl_args, capture_output=True, text=True, timeout=300)

try:
    r = json.loads(result.stdout)
except json.JSONDecodeError:
    print(f"  Response not JSON: {result.stdout[:500]}", file=sys.stderr)
    print(f"  stderr: {result.stderr[:500]}", file=sys.stderr)
    sys.exit(1)

if not r.get("success"):
    print(f"  Deploy FAILED: {r.get('errors')}", file=sys.stderr)
    print(f"  Full response: {json.dumps(r, indent=2)[:1000]}", file=sys.stderr)
    sys.exit(1)

deploy = r["result"]
deploy_id = deploy.get("id", "?")
deploy_url_out = deploy.get("url", "?")
jwt = deploy.get("jwt", "")
stage = deploy.get("latest_stage", {})

print(f"  Deploy ID:  {deploy_id}")
print(f"  URL:       {deploy_url_out}")
print(f"  Stage:     {stage.get('name', '?')} / {stage.get('status', '?')}")
print(f"  JWT:       {'yes' if jwt else 'no'} (len={len(jwt)})")

# Check files status
all_files = deploy.get("files", [])
missing = [f for f in all_files if f.get("status") == "missing"]
if all_files:
    print(f"  Files:     {len(all_files)} total, {len(missing)} missing")

# === Step 4: Upload missing files if JWT available ===
if missing and jwt:
    print(f"\n=== [3] Upload {len(missing)} missing files ===", flush=True)
    for finfo in missing:
        url_path = finfo.get("name", finfo.get("file_name", ""))
        fname = url_path.lstrip("/")
        fpath = os.path.join(SITE_DIR, fname)
        if not os.path.isfile(fpath):
            print(f"  SKIP {fname}")
            continue
        mime = mimetypes.guess_type(fname)[0] or "application/octet-stream"
        upload_url = f"{API}/pages/assets/upload?fileName={url_path}"
        upload_result = subprocess.run([
            "curl", "-s", "-X", "PUT", upload_url,
            "-H", f"Authorization: Bearer {jwt}",
            "-H", f"Content-Type: {mime}",
            "--data-binary", f"@{fpath}",
        ], capture_output=True, text=True, timeout=120)
        print(f"  {'OK ' if 'success\":true' in upload_result.stdout or '200' in upload_result.stdout else 'FAIL'} {fname}")

# === Step 5: Wait and check deployment status ===
import time
print("\n=== [4] Checking deployment status ===", flush=True)
for attempt in range(6):
    time.sleep(5)
    check_result = subprocess.run([
        "curl", "-s", "-X", "GET",
        f"{API}/accounts/{ACCT}/pages/projects/{PROJECT}/deployments/{deploy_id}",
        "-H", f"Authorization: Bearer {TOKEN}",
    ], capture_output=True, text=True, timeout=30)
    try:
        cr = json.loads(check_result.stdout)
        if cr.get("success"):
            d = cr["result"]
            stage = d.get("latest_stage", {})
            print(f"  [{attempt+1}] Stage: {stage.get('name', '?')} / {stage.get('status', '?')}")
            if stage.get("status") == "success" and stage.get("name") == "deploy":
                print("  Deployment SUCCESS!")
                break
    except:
        pass

# === Step 6: Add custom domain ===
print("\n=== [5] Add custom domain ===", flush=True)
domain_result = subprocess.run([
    "curl", "-s", "-X", "POST",
    f"{API}/accounts/{ACCT}/pages/projects/{PROJECT}/domains",
    "-H", f"Authorization: Bearer {TOKEN}",
    "-H", "Content-Type: application/json",
    "-d", json.dumps({"name": ZONE_NAME}),
], capture_output=True, text=True, timeout=30)
try:
    dr = json.loads(domain_result.stdout)
    if dr.get("success"):
        print(f"  Custom domain '{ZONE_NAME}' added!")
    elif any("already" in str(e).lower() or "exist" in str(e).lower() for e in dr.get("errors", [])):
        print(f"  Custom domain already exists.")
    else:
        print(f"  Custom domain result: {dr.get('errors', dr.get('messages', 'unknown'))}")
except:
    print(f"  Domain response: {domain_result.stdout[:300]}")

# === Step 7: Update DNS CNAME ===
print("\n=== [6] Update DNS CNAME ===", flush=True)
# Get zone ID
zone_result = subprocess.run([
    "curl", "-s", "-X", "GET",
    f"{API}/zones?name={ZONE_NAME}",
    "-H", f"Authorization: Bearer {TOKEN}",
], capture_output=True, text=True, timeout=30)
try:
    zr = json.loads(zone_result.stdout)
    if zr.get("success") and zr["result"]:
        zone_id = zr["result"][0]["id"]
        # Get project subdomain
        proj_result = subprocess.run([
            "curl", "-s", "-X", "GET",
            f"{API}/accounts/{ACCT}/pages/projects/{PROJECT}",
            "-H", f"Authorization: Bearer {TOKEN}",
        ], capture_output=True, text=True, timeout=30)
        pr = json.loads(proj_result.stdout)
        new_target = pr["result"]["subdomain"]

        # Get existing CNAME for serverbudget.com
        dns_result = subprocess.run([
            "curl", "-s", "-X", "GET",
            f"{API}/zones/{zone_id}/dns_records?type=CNAME&name={ZONE_NAME}",
            "-H", f"Authorization: Bearer {TOKEN}",
        ], capture_output=True, text=True, timeout=30)
        dnsr = json.loads(dns_result.stdout)
        if dnsr.get("success") and dnsr["result"]:
            rec_id = dnsr["result"][0]["id"]
            old_target = dnsr["result"][0]["content"]
            # Update CNAME
            upd_result = subprocess.run([
                "curl", "-s", "-X", "PUT",
                f"{API}/zones/{zone_id}/dns_records/{rec_id}",
                "-H", f"Authorization: Bearer {TOKEN}",
                "-H", "Content-Type: application/json",
                "-d", json.dumps({"type": "CNAME", "name": ZONE_NAME, "content": new_target, "proxied": True}),
            ], capture_output=True, text=True, timeout=30)
            updr = json.loads(upd_result.stdout)
            if updr.get("success"):
                print(f"  CNAME updated: {old_target} -> {new_target}")
            else:
                print(f"  CNAME update FAILED: {updr.get('errors')}")
        else:
            # Create new CNAME
            create_result = subprocess.run([
                "curl", "-s", "-X", "POST",
                f"{API}/zones/{zone_id}/dns_records",
                "-H", f"Authorization: Bearer {TOKEN}",
                "-H", "Content-Type: application/json",
                "-d", json.dumps({"type": "CNAME", "name": ZONE_NAME, "content": new_target, "proxied": True}),
            ], capture_output=True, text=True, timeout=30)
            cr2 = json.loads(create_result.stdout)
            if cr2.get("success"):
                print(f"  CNAME created: -> {new_target}")
            else:
                print(f"  CNAME create FAILED: {cr2.get('errors')}")
    else:
        print(f"  Zone not found")
except Exception as e:
    print(f"  DNS error: {e}")

# === Final report ===
print("\n=== DEPLOY COMPLETE ===")
print(f"  Project:       {PROJECT}")
print(f"  Deploy URL:   {deploy_url_out}")
print(f"  Custom domain: {ZONE_NAME}")
print(f"  Verify URL:   https://{ZONE_NAME}/cheap-vps-hosting.html")

# Cleanup manifest file
try:
    os.remove(manifest_file)
except:
    pass
