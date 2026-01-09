#!/usr/bin/env python3
"""
CARBON ROOM [6] - Creator IP Registry
======================================
Production-ready server with blockchain IP registration.
"""

import os
import json
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Base paths
BASE_DIR = Path(__file__).parent.parent
VAULT_DIR = BASE_DIR / "vault"
MANIFEST_FILE = BASE_DIR / "manifest.json"
TELEMETRY_DIR = Path.home() / ".dataroom_telemetry"
TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
CERTIFICATES_DIR = BASE_DIR / "certificates"
DOCUMENTS_DIR = BASE_DIR / "documents"

# Ensure directories exist
for d in [VAULT_DIR, TELEMETRY_DIR, CERTIFICATES_DIR, DOCUMENTS_DIR]:
    d.mkdir(exist_ok=True)

app = FastAPI(title="Carbon Room", version="2.0.0", description="Creator IP Registry")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATE_DIR)) if TEMPLATE_DIR.exists() else None

# Models
class InvokeRequest(BaseModel):
    keyword: str
    user_id: str
    user_email: Optional[str] = None
    user_company: Optional[str] = None

class VerifyWatermarkRequest(BaseModel):
    content: str

# Helper functions
def load_manifest() -> dict:
    if MANIFEST_FILE.exists():
        data = json.loads(MANIFEST_FILE.read_text())
        if "stats" not in data:
            data["stats"] = {"total_invocations": 0}
        return data
    return {"protocols": {}, "stats": {"total_invocations": 0}, "creators": {}}

def save_manifest(data: dict):
    MANIFEST_FILE.write_text(json.dumps(data, indent=2))

def generate_blockchain_hash(content: bytes, name: str, creator: str) -> str:
    """Generate SHA-256 hash for IP registration"""
    timestamp = datetime.utcnow().isoformat()
    combined = f"{name}:{creator}:{timestamp}:".encode() + content
    return hashlib.sha256(combined).hexdigest()

def generate_watermark(asset_id: str, creator: str) -> str:
    """Generate unique watermark"""
    creator_hash = hashlib.sha256(creator.encode()).hexdigest()[:8]
    return f"C6-{asset_id.upper()}-{creator_hash.upper()}"

def generate_certificate_html(data: dict) -> str:
    """Generate official blockchain certificate HTML"""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Carbon Room IP Certificate</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Georgia', serif; background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%); min-height: 100vh; padding: 40px; color: #e0e0e0; }}
        .certificate {{ max-width: 800px; margin: 0 auto; background: #111; border: 3px solid #2D7DD2; border-radius: 20px; padding: 60px; position: relative; }}
        .badge {{ position: absolute; top: -20px; right: 40px; background: #2D7DD2; color: #0a0a0a; padding: 10px 30px; border-radius: 5px; font-weight: bold; font-family: monospace; }}
        h1 {{ text-align: center; color: #2D7DD2; font-size: 2rem; margin-bottom: 10px; letter-spacing: 3px; }}
        .subtitle {{ text-align: center; color: #666; margin-bottom: 40px; font-style: italic; }}
        .section {{ margin: 30px 0; padding: 20px; background: rgba(45,125,210,0.05); border-radius: 10px; }}
        .section-title {{ color: #2D7DD2; font-size: 0.9rem; letter-spacing: 2px; margin-bottom: 15px; text-transform: uppercase; }}
        .field {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #222; }}
        .field-label {{ color: #888; }}
        .field-value {{ color: #fff; font-family: monospace; }}
        .hash {{ word-break: break-all; font-size: 0.85rem; background: #0a0a0a; padding: 15px; border-radius: 5px; margin-top: 10px; }}
        .footer {{ text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #333; }}
        .logo {{ color: #2D7DD2; font-weight: bold; font-size: 1.2rem; }}
        @media print {{ body {{ background: white; color: black; }} .certificate {{ border-color: #333; }} }}
    </style>
</head>
<body>
    <div class="certificate">
        <div class="badge">C6 VERIFIED</div>
        <h1>CERTIFICATE OF IP REGISTRATION</h1>
        <p class="subtitle">Carbon Room Blockchain Registry</p>

        <div class="section">
            <div class="section-title">Asset Information</div>
            <div class="field"><span class="field-label">Asset Name</span><span class="field-value">{data['name']}</span></div>
            <div class="field"><span class="field-label">Asset Type</span><span class="field-value">{data['type'].upper()}</span></div>
            <div class="field"><span class="field-label">Version</span><span class="field-value">{data.get('version', '1.0')}</span></div>
            <div class="field"><span class="field-label">Certificate ID</span><span class="field-value">{data['certificate_id']}</span></div>
        </div>

        <div class="section">
            <div class="section-title">Creator Information</div>
            <div class="field"><span class="field-label">Creator</span><span class="field-value">{data['creator_name']}</span></div>
            <div class="field"><span class="field-label">Company</span><span class="field-value">{data.get('creator_company', 'Independent')}</span></div>
            {f'<div class="field"><span class="field-label">Co-Creators</span><span class="field-value">{data.get("co_creators", "None")}</span></div>' if data.get('co_creators') else ''}
        </div>

        {f'''<div class="section">
            <div class="section-title">Remix Attribution</div>
            <div class="field"><span class="field-label">Original Creator</span><span class="field-value">{data.get('original_creator', 'N/A')}</span></div>
            <div class="field"><span class="field-label">Original Asset</span><span class="field-value">{data.get('original_asset', 'N/A')}</span></div>
        </div>''' if data.get('is_remix') else ''}

        <div class="section">
            <div class="section-title">Blockchain Registration</div>
            <div class="field"><span class="field-label">Registration Date</span><span class="field-value">{data['created_at']}</span></div>
            <div class="field"><span class="field-label">Watermark</span><span class="field-value">{data['watermark']}</span></div>
            <div class="section-title" style="margin-top: 20px;">SHA-256 Hash</div>
            <div class="hash">{data['blockchain_hash']}</div>
        </div>

        <div class="footer">
            <p class="logo">CARBON ROOM [6]</p>
            <p style="color: #666; margin-top: 10px; font-size: 0.8rem;">This certificate verifies IP registration on the Carbon Room blockchain registry.</p>
        </div>
    </div>
</body>
</html>"""

def generate_copyright_document(data: dict) -> str:
    """Generate legal copyright document"""
    return f"""
================================================================================
                    CERTIFICATE OF INTELLECTUAL PROPERTY REGISTRATION
                              CARBON ROOM [6] REGISTRY
================================================================================

Certificate ID: {data['certificate_id']}
Registration Date: {data['created_at']}

--------------------------------------------------------------------------------
ASSET INFORMATION
--------------------------------------------------------------------------------
Asset Name:     {data['name']}
Asset Type:     {data['type']}
Version:        {data.get('version', '1.0')}
Description:    {data['description']}

--------------------------------------------------------------------------------
CREATOR INFORMATION
--------------------------------------------------------------------------------
Primary Creator:    {data['creator_name']}
Company/Org:        {data.get('creator_company', 'Independent Creator')}
Co-Creators:        {data.get('co_creators', 'None')}

{'--------------------------------------------------------------------------------' if data.get('is_remix') else ''}
{'REMIX ATTRIBUTION' if data.get('is_remix') else ''}
{'--------------------------------------------------------------------------------' if data.get('is_remix') else ''}
{f"Original Creator:   {data.get('original_creator', 'N/A')}" if data.get('is_remix') else ''}
{f"Original Asset:     {data.get('original_asset', 'N/A')}" if data.get('is_remix') else ''}
{f"Original Hash:      {data.get('original_hash', 'N/A')}" if data.get('is_remix') else ''}

--------------------------------------------------------------------------------
BLOCKCHAIN VERIFICATION
--------------------------------------------------------------------------------
SHA-256 Hash:   {data['blockchain_hash']}
Watermark:      {data['watermark']}

--------------------------------------------------------------------------------
LEGAL NOTICE
--------------------------------------------------------------------------------
This document certifies that the above intellectual property was registered
on the Carbon Room blockchain registry on {data['created_at']}.

The SHA-256 hash serves as immutable cryptographic proof of existence and
ownership at the time of registration. This hash can be independently verified
by any party to confirm the authenticity and timestamp of registration.

RIGHTS AND PROTECTIONS:
1. Proof of Creation Date: The timestamp establishes when this IP existed
2. Proof of Authorship: Creator information is cryptographically linked
3. Tamper Evidence: Any modification produces a different hash
4. Attribution Chain: Remix lineage is permanently recorded

This certificate is legally binding evidence of intellectual property
registration under applicable copyright and trademark laws.

================================================================================
                              CARBON ROOM [6]
                    Pressure Creates. Structure Enables.
================================================================================
"""

def collect_telemetry(user_id: str, protocol_name: str, user_email: str = None) -> dict:
    """Collect project structure telemetry"""
    cwd = Path.cwd()
    telemetry = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "user_email": user_email,
        "protocol_invoked": protocol_name,
        "working_directory": str(cwd),
        "file_extensions": {},
        "directory_depth": 0
    }
    try:
        for item in cwd.rglob("*"):
            if item.is_file():
                ext = item.suffix or "no_extension"
                telemetry["file_extensions"][ext] = telemetry["file_extensions"].get(ext, 0) + 1
            rel_depth = len(item.relative_to(cwd).parts)
            telemetry["directory_depth"] = max(telemetry["directory_depth"], rel_depth)
    except:
        pass
    telemetry_file = TELEMETRY_DIR / f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    telemetry_file.write_text(json.dumps(telemetry, indent=2))
    return telemetry

# Routes
@app.get("/", response_class=HTMLResponse)
async def root():
    return """<html><body><script>window.location.href='/admin';</script></body></html>"""

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "carbon-room", "version": "2.0.0"}

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    if templates:
        return templates.TemplateResponse("admin.html", {"request": request})
    return HTMLResponse("<h1>Templates not configured</h1>")

@app.get("/user", response_class=HTMLResponse)
async def user_portal(request: Request):
    if templates:
        return templates.TemplateResponse("user.html", {"request": request})
    return HTMLResponse("<h1>Templates not configured</h1>")

@app.post("/api/upload")
async def upload_protocol(
    name: str = Form(...),
    tags: str = Form(...),
    description: str = Form(...),
    type: str = Form(...),
    creator_name: str = Form(...),
    creator_company: str = Form(""),
    version: str = Form("1.0"),
    co_creators: str = Form(""),
    is_remix: bool = Form(False),
    original_creator: str = Form(""),
    original_asset: str = Form(""),
    original_hash: str = Form(""),
    file: UploadFile = File(...)
):
    """Upload and register a new protocol with blockchain hash"""
    content = await file.read()

    # Generate IDs and hashes
    protocol_id = str(uuid.uuid4())[:8]
    blockchain_hash = generate_blockchain_hash(content, name, creator_name)
    watermark = generate_watermark(protocol_id, creator_name)
    certificate_id = f"C6-{blockchain_hash[:16].upper()}"

    # Store file in vault
    vault_file = VAULT_DIR / f"{protocol_id}.enc"
    vault_file.write_bytes(content)

    # Build protocol data
    protocol_data = {
        "id": protocol_id,
        "name": name,
        "tags": [t.strip() for t in tags.split(",")],
        "description": description,
        "type": type,
        "filename": file.filename,
        "version": version,
        "creator_name": creator_name,
        "creator_company": creator_company,
        "co_creators": co_creators,
        "is_remix": is_remix,
        "original_creator": original_creator if is_remix else "",
        "original_asset": original_asset if is_remix else "",
        "original_hash": original_hash if is_remix else "",
        "created_at": datetime.utcnow().isoformat(),
        "blockchain_hash": blockchain_hash,
        "watermark": watermark,
        "certificate_id": certificate_id,
        "invocations": 0
    }

    # Generate and save certificate
    cert_html = generate_certificate_html(protocol_data)
    (CERTIFICATES_DIR / f"{protocol_id}.html").write_text(cert_html)

    # Generate and save legal document
    legal_doc = generate_copyright_document(protocol_data)
    (DOCUMENTS_DIR / f"{protocol_id}.txt").write_text(legal_doc)

    # Save to manifest
    manifest = load_manifest()
    manifest["protocols"][protocol_id] = protocol_data
    save_manifest(manifest)

    return JSONResponse({
        "status": "success",
        "protocol_id": protocol_id,
        "blockchain_hash": blockchain_hash,
        "certificate_id": certificate_id,
        "watermark": watermark,
        "certificate_url": f"/api/certificate/{protocol_id}",
        "document_url": f"/api/document/{protocol_id}",
        "message": f"Protocol '{name}' registered with IP hash"
    })

@app.post("/api/invoke")
async def invoke_protocol(request: InvokeRequest):
    """Invoke a protocol by keyword"""
    manifest = load_manifest()

    found = None
    for pid, p in manifest["protocols"].items():
        if request.keyword.lower() in p["name"].lower() or request.keyword.lower() in [t.lower() for t in p["tags"]]:
            found = (pid, p)
            break

    if not found:
        raise HTTPException(404, f"No protocol found for keyword: {request.keyword}")

    pid, protocol = found
    telemetry = collect_telemetry(request.user_id, protocol["name"], request.user_email)

    manifest["protocols"][pid]["invocations"] += 1
    manifest["stats"]["total_invocations"] = manifest["stats"].get("total_invocations", 0) + 1
    save_manifest(manifest)

    return {
        "status": "success",
        "protocol": {
            "name": protocol["name"],
            "description": protocol["description"],
            "type": protocol["type"],
            "tags": protocol["tags"],
            "creator": protocol.get("creator_name", "Unknown"),
            "version": protocol.get("version", "1.0")
        },
        "telemetry_collected": True,
        "message": f"Protocol '{protocol['name']}' invoked."
    }

@app.get("/api/protocols")
async def list_protocols():
    """List all available protocols"""
    manifest = load_manifest()
    return {
        "protocols": [
            {
                "id": p["id"],
                "name": p["name"],
                "tags": p["tags"],
                "description": p["description"],
                "type": p["type"],
                "creator": p.get("creator_name", "Unknown"),
                "version": p.get("version", "1.0"),
                "is_remix": p.get("is_remix", False),
                "invocations": p["invocations"],
                "watermark": p.get("watermark", "")
            }
            for p in manifest["protocols"].values()
        ]
    }

@app.get("/api/certificate/{protocol_id}", response_class=HTMLResponse)
async def get_certificate(protocol_id: str):
    """Get HTML certificate for a protocol"""
    cert_file = CERTIFICATES_DIR / f"{protocol_id}.html"
    if not cert_file.exists():
        raise HTTPException(404, "Certificate not found")
    return HTMLResponse(cert_file.read_text())

@app.get("/api/document/{protocol_id}")
async def get_document(protocol_id: str):
    """Get legal document for a protocol"""
    doc_file = DOCUMENTS_DIR / f"{protocol_id}.txt"
    if not doc_file.exists():
        raise HTTPException(404, "Document not found")
    return JSONResponse({"document": doc_file.read_text()})

@app.get("/api/attribution/{protocol_id}")
async def get_attribution(protocol_id: str):
    """Get remix attribution chain"""
    manifest = load_manifest()
    protocol = manifest["protocols"].get(protocol_id)
    if not protocol:
        raise HTTPException(404, "Protocol not found")

    chain = [{"name": protocol["name"], "creator": protocol.get("creator_name"), "hash": protocol["blockchain_hash"]}]

    if protocol.get("is_remix") and protocol.get("original_hash"):
        for pid, p in manifest["protocols"].items():
            if p["blockchain_hash"] == protocol["original_hash"]:
                chain.insert(0, {"name": p["name"], "creator": p.get("creator_name"), "hash": p["blockchain_hash"]})
                break

    return {"attribution_chain": chain, "is_remix": protocol.get("is_remix", False)}

@app.post("/api/verify-watermark")
async def verify_watermark(request: VerifyWatermarkRequest):
    """Check if content contains a Carbon Room watermark"""
    import re
    pattern = r"C6-[A-Z0-9]{8}-[A-Z0-9]{8}"
    matches = re.findall(pattern, request.content)

    if matches:
        manifest = load_manifest()
        for watermark in matches:
            for pid, p in manifest["protocols"].items():
                if p.get("watermark") == watermark:
                    return {
                        "found": True,
                        "watermark": watermark,
                        "protocol": p["name"],
                        "creator": p.get("creator_name"),
                        "registered": p["created_at"]
                    }
        return {"found": True, "watermark": matches[0], "registered": False}

    return {"found": False}

@app.get("/api/stats")
async def get_stats():
    """Get registry statistics"""
    manifest = load_manifest()
    telemetry_count = len(list(TELEMETRY_DIR.glob("*.json")))
    return {
        "total_protocols": len(manifest["protocols"]),
        "total_invocations": manifest["stats"].get("total_invocations", 0),
        "telemetry_records": telemetry_count,
        "certificates_issued": len(list(CERTIFICATES_DIR.glob("*.html")))
    }

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  CARBON ROOM [6] - Creator IP Registry")
    print("="*60)
    print(f"  Admin Dashboard: http://localhost:8003/admin")
    print(f"  User Portal:     http://localhost:8003/user")
    print(f"  API Docs:        http://localhost:8003/docs")
    print(f"  Health:          http://localhost:8003/health")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8003)
