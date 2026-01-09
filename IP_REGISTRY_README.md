# Carbon Room IP Registration System

## Overview

A comprehensive blockchain-based intellectual property registration system that provides:

- **Legal Copyright Document Generation**: Automatically generates legally-formatted copyright certificates
- **Watermark Management**: Injects unique watermarks into code/documents for provenance tracking
- **Remix Attribution Chains**: Tracks derivative works and maintains attribution lineage
- **Certificate Generation**: Creates styled HTML certificates for display and verification
- **Hash-Based Verification**: Immutable SHA-256 proof of existence and ownership

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Server                          │
│                   (api/server.py)                           │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ├─> Upload Endpoint
                    │   ├─> Generate Blockchain Hash
                    │   ├─> Create Watermark
                    │   ├─> Inject Watermark into File
                    │   ├─> Generate Copyright Document
                    │   ├─> Generate HTML Certificate
                    │   └─> Store in Manifest
                    │
                    ├─> Certificate Endpoint (HTML)
                    ├─> Document Endpoint (Plain Text)
                    ├─> Attribution Chain Endpoint
                    ├─> Watermark Verification Endpoint
                    └─> Public Verification Endpoint

┌─────────────────────────────────────────────────────────────┐
│                  IP Registry Core                           │
│               (core/ip_registry.py)                         │
│                                                             │
│  ├─> generate_copyright_document()                         │
│  ├─> generate_certificate_html()                           │
│  ├─> generate_watermark()                                  │
│  ├─> detect_watermark()                                    │
│  ├─> inject_watermark_comment()                            │
│  ├─> build_attribution_chain()                             │
│  └─> generate_composite_hash()                             │
└─────────────────────────────────────────────────────────────┘
```

## Installation

```bash
cd /Users/Morpheous/vltrndataroom/global-dataroom
pip install fastapi uvicorn python-multipart
```

## Running the Server

```bash
python api/server.py
```

Server will start on `http://localhost:8003`

- Admin Dashboard: http://localhost:8003/admin
- API Documentation: http://localhost:8003/docs
- User Portal: http://localhost:8003/user

## API Endpoints

### 1. Upload and Register IP

**POST** `/api/upload`

Registers intellectual property with full legal documentation.

**Form Fields:**
- `name` (required): Asset name
- `tags` (required): Comma-separated tags
- `description` (required): Asset description
- `type` (required): Asset type (code, document, design, media, etc.)
- `file` (required): File to upload
- `creator_name` (required): Creator's full name
- `creator_company` (optional): Company name
- `version` (optional): Version identifier (default: "1.0")
- `co_creators` (optional): Comma-separated co-creator names
- `is_remix` (optional): Boolean indicating if derivative work
- `original_creator` (optional): Original creator name if remix
- `original_asset` (optional): Original asset name if remix
- `original_hash` (optional): Original asset blockchain hash if remix

**Response:**
```json
{
  "status": "success",
  "protocol_id": "a1b2c3d4",
  "blockchain_hash": "3f8a9...",
  "certificate_id": "C6-3F8A9BC1234567890",
  "watermark": "C6-A1B2C3D4-8E7F2A1B",
  "copyright_document_url": "/api/document/a1b2c3d4",
  "certificate_url": "/api/certificate/a1b2c3d4",
  "message": "IP 'My Asset' registered with full legal protection"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8003/api/upload" \
  -F "name=MySmartContract" \
  -F "tags=solidity,defi,erc20" \
  -F "description=Revolutionary DeFi protocol" \
  -F "type=code" \
  -F "creator_name=John Developer" \
  -F "creator_company=Acme Blockchain Inc" \
  -F "version=2.1.0" \
  -F "file=@./contracts/MyToken.sol"
```

### 2. Get HTML Certificate

**GET** `/api/certificate/{asset_id}`

Returns styled HTML certificate suitable for display or printing.

**Response:** HTML page

**Example:**
```bash
curl http://localhost:8003/api/certificate/a1b2c3d4 > certificate.html
open certificate.html
```

### 3. Get Copyright Document

**GET** `/api/document/{asset_id}`

Returns plain text legal copyright document.

**Response:** Plain text legal document

**Example:**
```bash
curl http://localhost:8003/api/document/a1b2c3d4
```

### 4. Get Attribution Chain

**GET** `/api/attribution/{asset_id}`

Returns complete remix/derivative attribution chain.

**Response:**
```json
{
  "asset_id": "a1b2c3d4",
  "chain_length": 3,
  "attribution_chain": [
    {
      "asset_id": "original123",
      "name": "Original Asset",
      "creator": "Jane Creator",
      "company": "Original Co",
      "timestamp": "2025-01-01T00:00:00Z",
      "hash": "abc123...",
      "is_remix": false,
      "version": "1.0"
    },
    {
      "asset_id": "remix456",
      "name": "First Remix",
      "creator": "Bob Remixer",
      "company": "Remix Inc",
      "timestamp": "2025-06-01T00:00:00Z",
      "hash": "def456...",
      "is_remix": true,
      "version": "1.5"
    },
    {
      "asset_id": "a1b2c3d4",
      "name": "Second Generation Remix",
      "creator": "Alice Developer",
      "company": "Dev Studio",
      "timestamp": "2026-01-01T00:00:00Z",
      "hash": "ghi789...",
      "is_remix": true,
      "version": "2.0"
    }
  ],
  "is_original": false,
  "is_remix": true
}
```

### 5. Verify Watermark

**POST** `/api/verify-watermark`

Checks if content contains specified Carbon[6] watermark.

**Request Body:**
```json
{
  "content": "// Carbon[6] Watermark: C6-A1B2C3D4-8E7F2A1B\n\nfunction myCode() {}",
  "watermark": "C6-A1B2C3D4-8E7F2A1B"
}
```

**Response:**
```json
{
  "watermark": "C6-A1B2C3D4-8E7F2A1B",
  "detected": true,
  "message": "Watermark detected in content"
}
```

### 6. Get Complete Asset Details

**GET** `/api/asset/{asset_id}`

Returns full asset metadata with links to all resources.

**Response:**
```json
{
  "asset": {
    "id": "a1b2c3d4",
    "name": "MySmartContract",
    "creator_name": "John Developer",
    "creator_company": "Acme Blockchain Inc",
    "blockchain_hash": "3f8a9...",
    "watermark": "C6-A1B2C3D4-8E7F2A1B",
    "certificate_id": "C6-3F8A9BC1234567890",
    "version": "2.1.0",
    "is_remix": false,
    "co_creators": ["Jane Co-Dev"],
    "created_at": "2026-01-09T00:00:00Z"
  },
  "attribution_chain": [...],
  "links": {
    "certificate": "/api/certificate/a1b2c3d4",
    "copyright_document": "/api/document/a1b2c3d4",
    "attribution": "/api/attribution/a1b2c3d4"
  }
}
```

### 7. Public Verification by Hash

**GET** `/api/verify/{hash_prefix}`

Verify registration by certificate ID or hash prefix (public endpoint).

**Example:**
```bash
curl http://localhost:8003/api/verify/3f8a9bc
```

**Response:**
```json
{
  "verified": true,
  "hash_prefix": "3f8a9bc",
  "matches": [
    {
      "name": "MySmartContract",
      "creator": "John Developer",
      "creator_company": "Acme Blockchain Inc",
      "registered": "2026-01-09T00:00:00Z",
      "certificate_id": "C6-3F8A9BC1234567890",
      "is_remix": false
    }
  ]
}
```

## Watermark System

### How Watermarks Work

1. **Generation**: Unique watermark created from asset ID + creator + timestamp
   - Format: `C6-{asset_id}-{creator_hash}`
   - Example: `C6-A1B2C3D4-8E7F2A1B`

2. **Injection**: Automatically injected into text-based files as comments
   - Supported: `.py`, `.js`, `.ts`, `.sol`, `.go`, `.rs`, `.java`, `.cpp`, `.c`, `.html`, `.css`, `.md`, `.txt`

3. **Detection**: Can be searched for in suspicious files to verify authenticity

### Example Watermarked File (Python)

```python
# Carbon[6] Watermark: C6-A1B2C3D4-8E7F2A1B
# This file is registered in the Carbon Room IP Registry

def my_function():
    return "Hello World"
```

### Example Watermarked File (Solidity)

```solidity
// SPDX-License-Identifier: MIT
// Carbon[6] Watermark: C6-A1B2C3D4-8E7F2A1B
// This file is registered in the Carbon Room IP Registry

pragma solidity ^0.8.20;

contract MyToken {
    // Contract code
}
```

## Legal Copyright Document

The system generates a comprehensive legal copyright document that includes:

1. **Asset Information**
   - Name, type, version
   - Certificate ID

2. **Creator Information**
   - Primary creator name and company
   - Co-creators list

3. **Registration Details**
   - Registration date and time (UTC)
   - SHA-256 blockchain hash
   - Watermark ID

4. **Remix Attribution** (if applicable)
   - Original asset name
   - Original creator
   - Attribution acknowledgment

5. **Legal Notice**
   - Copyright protection statement
   - Blockchain verification instructions
   - Derivative work requirements
   - Watermark protection notice

6. **Carbon[6] Signature**
   - Certificate hash for verification
   - Issue date
   - Verification URL

## HTML Certificate

The HTML certificate is a beautifully styled, print-ready document featuring:

- **Gradient header** with Carbon Room branding
- **Certificate border** with watermark overlay
- **Structured sections** for easy reading
- **QR code placeholder** for verification (can be added)
- **Print-optimized** CSS
- **Responsive design** for all screen sizes

### Certificate Features

- Professional typography (Georgia serif)
- Color-coded sections
- Monospace hash display
- Remix attribution highlighting
- Legal notice block
- Carbon[6] signature seal

## Remix Attribution Chain

The system tracks derivative works through a linked chain:

```
Original Asset
    ↓ (is_remix: true, original_hash: abc123...)
First Remix
    ↓ (is_remix: true, original_hash: def456...)
Second Generation Remix
    ↓ (is_remix: true, original_hash: ghi789...)
Third Generation Remix
```

Each remix:
- References the original asset's blockchain hash
- Credits the original creator
- Maintains the full chain back to the source
- Can be queried via `/api/attribution/{asset_id}`

## Security Features

### 1. Comprehensive Hashing

The blockchain hash combines:
- File content (SHA-256)
- All metadata (JSON stringified, sorted keys)
- Registration timestamp

This creates an immutable proof that cannot be backdated or tampered with.

### 2. Watermark Protection

- Unique per asset and creator
- Injected into source files
- Detectable via API
- Serves as forensic evidence of authenticity

### 3. Certificate Verification

Certificates can be verified by:
- Full blockchain hash
- Certificate ID (hash prefix)
- Public verification endpoint

### 4. Tamper Evidence

Any modification to:
- File content
- Metadata
- Timestamp

Will result in a completely different hash, making tampering immediately detectable.

## Use Cases

### 1. Smart Contract Registration

```bash
# Register Solidity contract before deployment
curl -X POST http://localhost:8003/api/upload \
  -F "name=UniswapV4Fork" \
  -F "tags=defi,dex,solidity" \
  -F "description=Modified Uniswap V4 implementation" \
  -F "type=code" \
  -F "creator_name=DeFi Developer" \
  -F "creator_company=DeFi Labs" \
  -F "is_remix=true" \
  -F "original_creator=Uniswap Labs" \
  -F "original_asset=Uniswap V4" \
  -F "file=@./UniswapV4Fork.sol"
```

### 2. Music Production (Remix Tracking)

```bash
# Register remix with attribution
curl -X POST http://localhost:8003/api/upload \
  -F "name=Remix_Track_2026" \
  -F "tags=music,remix,edm" \
  -F "description=EDM remix of original track" \
  -F "type=media" \
  -F "creator_name=DJ RemixMaster" \
  -F "is_remix=true" \
  -F "original_creator=Original Artist" \
  -F "original_asset=Original Track Name" \
  -F "original_hash=abc123def456..." \
  -F "file=@./remix_track.mp3"
```

### 3. Design Assets

```bash
# Register design with co-creators
curl -X POST http://localhost:8003/api/upload \
  -F "name=Brand_Logo_2026" \
  -F "tags=design,branding,logo" \
  -F "description=Company rebrand logo design" \
  -F "type=design" \
  -F "creator_name=Lead Designer" \
  -F "creator_company=Design Studio Inc" \
  -F "co_creators=Assistant Designer,Art Director" \
  -F "file=@./logo.svg"
```

### 4. Legal Document Registration

```bash
# Register legal agreement
curl -X POST http://localhost:8003/api/upload \
  -F "name=Partnership_Agreement_2026" \
  -F "tags=legal,contract,partnership" \
  -F "description=Multi-party partnership agreement" \
  -F "type=document" \
  -F "creator_name=Legal Team" \
  -F "creator_company=Law Firm LLP" \
  -F "co_creators=Partner A,Partner B,Partner C" \
  -F "file=@./agreement.pdf"
```

## File Storage Structure

```
global-dataroom/
├── api/
│   └── server.py                          # FastAPI application
├── core/
│   ├── __init__.py
│   └── ip_registry.py                     # IP registry logic
├── vault/
│   └── {asset_id}.enc                     # Encrypted/watermarked files
├── certificates/
│   └── {asset_id}_certificate.html        # HTML certificates
├── documents/
│   └── {asset_id}_copyright.txt           # Legal documents
├── manifest.json                          # Registry database
└── templates/
    ├── admin.html
    └── user.html
```

## Manifest Schema

```json
{
  "protocols": {
    "{asset_id}": {
      "id": "8-char UUID",
      "name": "Asset name",
      "tags": ["tag1", "tag2"],
      "description": "Description",
      "type": "code|document|design|media",
      "filename": "original_filename.ext",
      "created_at": "ISO 8601 timestamp",
      "blockchain_hash": "SHA-256 hex",
      "invocations": 0,
      "creator_name": "Creator name",
      "creator_company": "Company name or null",
      "version": "Semantic version",
      "co_creators": ["name1", "name2"],
      "is_remix": false,
      "original_creator": null,
      "original_asset": null,
      "original_hash": null,
      "watermark": "C6-{asset_id}-{hash}",
      "certificate_id": "C6-{hash_prefix}"
    }
  },
  "stats": {
    "total_invocations": 0,
    "total_creators": 0,
    "total_remixes": 0
  }
}
```

## Production Considerations

### 1. Encryption

Current implementation stores files as-is. For production:

```python
# Encrypt before storing
from cryptography.fernet import Fernet

key = Fernet.generate_key()  # Store securely
cipher = Fernet(key)
encrypted_content = cipher.encrypt(watermarked_content)
vault_file.write_bytes(encrypted_content)
```

### 2. Blockchain Anchoring

For true immutability, anchor hashes on a public blockchain:

```python
# Ethereum example
def anchor_to_blockchain(hash_value):
    # Store hash in smart contract
    contract.functions.registerIP(hash_value).transact()
```

### 3. Rate Limiting

Add rate limiting to prevent abuse:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/upload")
@limiter.limit("10/hour")
async def upload_protocol(...):
    ...
```

### 4. Authentication

Add API key or OAuth authentication:

```python
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

@app.post("/api/upload")
async def upload_protocol(..., api_key: str = Security(api_key_header)):
    if api_key not in valid_api_keys:
        raise HTTPException(403, "Invalid API key")
    ...
```

## Legal Disclaimer

This system provides:
- **Timestamp proof** of registration
- **Content hash** verification
- **Attribution tracking** for derivatives
- **Forensic watermarking** for detection

It does NOT:
- Replace formal copyright registration with government authorities
- Provide legal representation
- Guarantee enforceability in all jurisdictions
- Replace proper legal counsel for IP matters

For full legal protection, consult with an intellectual property attorney and consider:
- USPTO registration (US)
- WIPO registration (International)
- Country-specific copyright/trademark registration

## Support

For issues or questions:
- Check API documentation at `/docs`
- Review error messages in server logs
- Verify manifest.json integrity
- Ensure all directories are writable

## Version History

- **v2.0.0** (2026-01-09): Complete IP registration system with legal documents, watermarks, and attribution chains
- **v1.0.0** (2026-01-09): Initial protocol registry with basic hash generation
