# Carbon Room IP Registry - System Architecture

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                               │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   Upload     │  │  Certificate │  │ Verification │             │
│  │     Form     │  │    Viewer    │  │    Portal    │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│         │                 │                 │                       │
└─────────┼─────────────────┼─────────────────┼───────────────────────┘
          │                 │                 │
          │                 │                 │
┌─────────▼─────────────────▼─────────────────▼───────────────────────┐
│                        API LAYER (FastAPI)                           │
│                                                                      │
│  POST /api/upload          GET /api/certificate/{id}                │
│  POST /api/verify-watermark GET /api/document/{id}                  │
│  GET  /api/attribution/{id} GET /api/verify/{hash}                  │
│  GET  /api/asset/{id}       GET /api/protocols                      │
│                                                                      │
│  ┌────────────────────────────────────────────────────────┐        │
│  │              Request Processing Pipeline                │        │
│  │                                                         │        │
│  │  1. Receive Upload                                      │        │
│  │  2. Parse Metadata                                      │        │
│  │  3. Generate Watermark                                  │        │
│  │  4. Inject into File                                    │        │
│  │  5. Calculate Composite Hash                            │        │
│  │  6. Generate Legal Document                             │        │
│  │  7. Generate HTML Certificate                           │        │
│  │  8. Store in Vault                                      │        │
│  │  9. Update Manifest                                     │        │
│  │ 10. Return Response                                     │        │
│  └────────────────────────────────────────────────────────┘        │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               │
┌──────────────────────────────▼───────────────────────────────────────┐
│                      BUSINESS LOGIC LAYER                            │
│                     (core/ip_registry.py)                            │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │  IPRegistry Class                                          │     │
│  │                                                            │     │
│  │  ┌──────────────────────────────────────────────┐         │     │
│  │  │  Document Generation                         │         │     │
│  │  │  • generate_copyright_document()             │         │     │
│  │  │  • generate_certificate_html()               │         │     │
│  │  │  • _generate_certificate_hash()              │         │     │
│  │  └──────────────────────────────────────────────┘         │     │
│  │                                                            │     │
│  │  ┌──────────────────────────────────────────────┐         │     │
│  │  │  Watermark Management                        │         │     │
│  │  │  • generate_watermark()                      │         │     │
│  │  │  • detect_watermark()                        │         │     │
│  │  │  • inject_watermark_comment()                │         │     │
│  │  └──────────────────────────────────────────────┘         │     │
│  │                                                            │     │
│  │  ┌──────────────────────────────────────────────┐         │     │
│  │  │  Attribution Tracking                        │         │     │
│  │  │  • build_attribution_chain()                 │         │     │
│  │  └──────────────────────────────────────────────┘         │     │
│  │                                                            │     │
│  │  ┌──────────────────────────────────────────────┐         │     │
│  │  │  Cryptographic Operations                    │         │     │
│  │  │  • generate_composite_hash()                 │         │     │
│  │  │    - SHA-256(file_content)                   │         │     │
│  │  │    - SHA-256(content + metadata + timestamp) │         │     │
│  │  └──────────────────────────────────────────────┘         │     │
│  └───────────────────────────────────────────────────────────┘     │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               │
┌──────────────────────────────▼───────────────────────────────────────┐
│                       DATA PERSISTENCE LAYER                         │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  manifest.   │  │  vault/      │  │ certificates/│             │
│  │  json        │  │  *.enc       │  │ *.html       │             │
│  │              │  │              │  │              │             │
│  │ Registry DB  │  │ Encrypted    │  │ HTML Certs   │             │
│  │ (JSON)       │  │ Files        │  │              │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│                                                                      │
│  ┌──────────────┐                                                   │
│  │ documents/   │                                                   │
│  │ *_copyright. │                                                   │
│  │ txt          │                                                   │
│  │              │                                                   │
│  │ Legal Docs   │                                                   │
│  └──────────────┘                                                   │
└──────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagrams

### Upload and Registration Flow

```
┌─────────┐
│  Client │
└────┬────┘
     │
     │ 1. POST /api/upload
     │    (file + metadata)
     ▼
┌────────────────┐
│  API Server    │
└────┬───────────┘
     │
     │ 2. Parse form data
     │    Extract fields
     ▼
┌────────────────┐
│  IPRegistry    │
│                │
│ 3. Generate    │──────┐
│    watermark   │      │
└────┬───────────┘      │
     │                  │
     │ 4. Inject        │ Format: C6-{id}-{hash}
     │    watermark     │
     │    into file     │
     ▼                  │
┌────────────────┐      │
│  File Content  │◄─────┘
│  (watermarked) │
└────┬───────────┘
     │
     │ 5. Generate composite hash
     │    SHA-256(content + metadata + timestamp)
     ▼
┌────────────────┐
│  Blockchain    │
│  Hash          │
└────┬───────────┘
     │
     │ 6. Generate legal document
     ▼
┌────────────────┐
│  Copyright     │──┐
│  Document      │  │
│  (plain text)  │  │
└────────────────┘  │
                    │
     │ 7. Generate HTML certificate
     ▼              │
┌────────────────┐  │
│  HTML          │  │
│  Certificate   │  │
└────┬───────────┘  │
     │              │
     │ 8. Store all artifacts
     ▼              │
┌────────────────┐  │
│  vault/        │  │
│  {id}.enc      │  │
└────────────────┘  │
                    │
┌────────────────┐  │
│  certificates/ │◄─┤
│  {id}_cert.html│  │
└────────────────┘  │
                    │
┌────────────────┐  │
│  documents/    │◄─┘
│  {id}_copy.txt │
└────┬───────────┘
     │
     │ 9. Update manifest.json
     ▼
┌────────────────┐
│  manifest.json │
│  + new entry   │
└────┬───────────┘
     │
     │ 10. Return response
     ▼
┌────────────────┐
│  Client        │
│  (success +    │
│   metadata)    │
└────────────────┘
```

### Attribution Chain Resolution Flow

```
Client requests: /api/attribution/{remix_id}
         │
         ▼
┌────────────────────────┐
│ Load manifest.json     │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│ Find asset by ID       │
└────────┬───────────────┘
         │
         ▼
    ┌────────────────────────┐
    │ Is this a remix?        │
    │ (is_remix: true)        │
    └────┬────────────────────┘
         │
         │ YES
         ▼
    ┌────────────────────────┐
    │ Get original_hash      │
    └────┬────────────────────┘
         │
         ▼
    ┌────────────────────────┐
    │ Find asset with        │
    │ matching hash          │
    └────┬────────────────────┘
         │
         │ Found
         ▼
    ┌────────────────────────┐
    │ Add to chain           │
    │ Move to original       │
    └────┬────────────────────┘
         │
         │ Repeat until original found
         ▼
    ┌────────────────────────┐
    │ Reverse chain          │
    │ (original → current)   │
    └────┬────────────────────┘
         │
         ▼
    ┌────────────────────────┐
    │ Return chain to client │
    └────────────────────────┘

Example Chain:

[0] Original Asset
    ├─ creator: Jane
    ├─ hash: abc123...
    └─ is_remix: false
        │
        ▼
[1] First Remix
    ├─ creator: Bob
    ├─ hash: def456...
    ├─ is_remix: true
    └─ original_hash: abc123...
        │
        ▼
[2] Second Remix (current)
    ├─ creator: Alice
    ├─ hash: ghi789...
    ├─ is_remix: true
    └─ original_hash: def456...
```

### Watermark Verification Flow

```
Client provides:
  • content (file or text)
  • watermark (C6-{id}-{hash})
         │
         ▼
┌────────────────────────┐
│ Normalize both strings │
│ (uppercase)            │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│ Search for watermark   │
│ in content             │
└────────┬───────────────┘
         │
         ├─────────────────────┐
         │                     │
    FOUND                  NOT FOUND
         │                     │
         ▼                     ▼
┌────────────────────┐  ┌──────────────────┐
│ Return:            │  │ Return:          │
│ detected: true     │  │ detected: false  │
│ message: "Found"   │  │ message: "Not    │
└────────────────────┘  │          found"  │
                        └──────────────────┘

Use Cases:
1. Verify authenticity of source code
2. Detect unauthorized use
3. Prove ownership in disputes
4. Track file provenance
```

## Component Responsibilities

### API Server (api/server.py)

**Responsibilities:**
- HTTP request/response handling
- Form data parsing
- File upload management
- Error handling
- Response formatting
- Static file serving

**Does NOT:**
- Hash generation (delegates to IPRegistry)
- Document generation (delegates to IPRegistry)
- Watermark injection (delegates to IPRegistry)
- Attribution tracking (delegates to IPRegistry)

### IP Registry Core (core/ip_registry.py)

**Responsibilities:**
- Legal document generation
- HTML certificate generation
- Watermark generation and detection
- Watermark injection into files
- Attribution chain building
- Composite hash generation
- Certificate hash generation

**Does NOT:**
- HTTP handling (API server's job)
- File storage (API server's job)
- Manifest updates (API server's job)

### Manifest Database (manifest.json)

**Structure:**
```json
{
  "protocols": {
    "{asset_id}": {
      // Asset metadata
    }
  },
  "stats": {
    "total_invocations": 0,
    "total_creators": 0,
    "total_remixes": 0
  },
  "schema": {
    // Schema definition
  }
}
```

**Responsibilities:**
- Store all asset metadata
- Track usage statistics
- Maintain schema definition
- Enable searches and lookups

### File Storage

**vault/**
- Stores watermarked files
- Encrypted-ready (AES-256-GCM)
- Named: `{asset_id}.enc`

**certificates/**
- Stores HTML certificates
- Web-viewable format
- Named: `{asset_id}_certificate.html`

**documents/**
- Stores legal copyright documents
- Plain text format
- Named: `{asset_id}_copyright.txt`

## Security Architecture

### Hashing Strategy

```
Input: File + Metadata + Timestamp
         │
         ▼
┌──────────────────────┐
│ SHA-256(file_content)│
│ → content_hash       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────┐
│ Stringify metadata           │
│ (JSON, sorted keys)          │
│ → metadata_str               │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│ Combine:                                 │
│ {content_hash}:{metadata_str}:{timestamp}│
└──────────┬───────────────────────────────┘
           │
           ▼
┌──────────────────────┐
│ SHA-256(combined)    │
│ → blockchain_hash    │
└──────────────────────┘

Properties:
✓ Deterministic
✓ Collision-resistant
✓ Tamper-evident
✓ Non-reversible
✓ Fast to compute
✓ Impossible to backdate
```

### Watermark Strategy

```
Generation:
  asset_id = "a1b2c3d4"
  creator = "Jane Developer"
  timestamp = "2026-01-09T00:00:00Z"

  creator_data = "{creator}:{timestamp}"
  creator_hash = SHA-256(creator_data)[:8]

  watermark = "C6-{asset_id}-{creator_hash}"
           = "C6-A1B2C3D4-8E7F2A1B"

Injection:
  Python:    # Carbon[6] Watermark: C6-A1B2C3D4-8E7F2A1B
  Solidity:  // Carbon[6] Watermark: C6-A1B2C3D4-8E7F2A1B
  HTML:      <!-- Carbon[6] Watermark: C6-A1B2C3D4-8E7F2A1B -->

Detection:
  1. Normalize content and watermark (uppercase)
  2. Search for watermark in content
  3. Return boolean result

Properties:
✓ Unique per asset + creator
✓ Embedded in source
✓ Detectable via API
✓ Survives copying
✓ Forensic evidence
```

### Certificate Verification

```
Public Endpoint: /api/verify/{hash_prefix}

Flow:
  1. Client provides hash prefix (min 8 chars)
  2. Server searches manifest for matches
  3. Returns public metadata (NO file content)
  4. Client verifies legitimacy

Example:
  Input:  3f8a9bc
  Output: {
    "verified": true,
    "matches": [
      {
        "name": "MyContract",
        "creator": "Jane Developer",
        "company": "Blockchain Labs",
        "registered": "2026-01-09T00:00:00Z",
        "certificate_id": "C6-3F8A9BC1234567890",
        "is_remix": false
      }
    ]
  }

Use Cases:
  • Verify certificate authenticity
  • Check registration status
  • Confirm creator identity
  • Validate timestamp claims
```

## Scalability Considerations

### Current Architecture (JSON File)

**Pros:**
- Simple
- No database dependency
- Easy backup
- Version control friendly

**Cons:**
- Single file bottleneck
- No concurrent write safety
- Limited query performance
- Memory constraints at scale

**Limits:**
- ~10,000 assets (reasonable)
- ~100,000 assets (slow)
- 1M+ assets (needs DB)

### Migration to Database

**Recommended for Production:**

```sql
-- PostgreSQL Schema
CREATE TABLE assets (
  id VARCHAR(8) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  creator_name VARCHAR(255) NOT NULL,
  creator_company VARCHAR(255),
  blockchain_hash VARCHAR(64) UNIQUE NOT NULL,
  watermark VARCHAR(50) NOT NULL,
  certificate_id VARCHAR(50) NOT NULL,
  version VARCHAR(50) NOT NULL,
  is_remix BOOLEAN DEFAULT FALSE,
  original_hash VARCHAR(64),
  created_at TIMESTAMP NOT NULL,
  metadata JSONB
);

CREATE INDEX idx_blockchain_hash ON assets(blockchain_hash);
CREATE INDEX idx_creator_name ON assets(creator_name);
CREATE INDEX idx_created_at ON assets(created_at DESC);
CREATE INDEX idx_watermark ON assets(watermark);

CREATE TABLE co_creators (
  asset_id VARCHAR(8) REFERENCES assets(id),
  co_creator_name VARCHAR(255),
  PRIMARY KEY (asset_id, co_creator_name)
);

CREATE TABLE tags (
  asset_id VARCHAR(8) REFERENCES assets(id),
  tag VARCHAR(100),
  PRIMARY KEY (asset_id, tag)
);
```

### Caching Strategy

**For High Traffic:**

```python
from functools import lru_cache
import redis

# In-memory cache for certificates
@lru_cache(maxsize=1000)
def get_certificate_cached(asset_id):
    return load_certificate(asset_id)

# Redis for distributed caching
redis_client = redis.Redis()

def get_asset_cached(asset_id):
    cached = redis_client.get(f"asset:{asset_id}")
    if cached:
        return json.loads(cached)

    asset = load_from_db(asset_id)
    redis_client.setex(f"asset:{asset_id}", 3600, json.dumps(asset))
    return asset
```

## API Rate Limiting

**Recommended Implementation:**

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/upload")
@limiter.limit("10/hour")  # 10 uploads per hour per IP
async def upload_protocol(...):
    pass

@app.get("/api/certificate/{asset_id}")
@limiter.limit("100/minute")  # 100 views per minute
async def get_certificate(...):
    pass

@app.post("/api/verify-watermark")
@limiter.limit("50/minute")  # 50 verifications per minute
async def verify_watermark(...):
    pass
```

## Monitoring and Observability

**Recommended Metrics:**

```python
from prometheus_client import Counter, Histogram

upload_counter = Counter('uploads_total', 'Total uploads')
upload_duration = Histogram('upload_duration_seconds', 'Upload processing time')

certificate_views = Counter('certificate_views_total', 'Certificate views')
verification_requests = Counter('verifications_total', 'Verification requests')

watermark_detections = Counter(
    'watermark_detections_total',
    'Watermark detection results',
    ['detected']
)
```

**Health Check Endpoint:**

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "checks": {
            "manifest": manifest_file_exists(),
            "vault": vault_directory_writable(),
            "certificates": certificates_directory_writable(),
            "documents": documents_directory_writable()
        }
    }
```

## Deployment Architecture

```
                    Internet
                       │
                       ▼
              ┌────────────────┐
              │  Load Balancer │
              │   (nginx)      │
              └────────┬───────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
         ▼             ▼             ▼
   ┌─────────┐   ┌─────────┐   ┌─────────┐
   │  App    │   │  App    │   │  App    │
   │ Server 1│   │ Server 2│   │ Server 3│
   └────┬────┘   └────┬────┘   └────┬────┘
        │             │             │
        └─────────────┼─────────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
         ▼            ▼            ▼
   ┌─────────┐   ┌─────────┐   ┌─────────┐
   │ Redis   │   │PostgreSQL│   │  S3/    │
   │ Cache   │   │  (RDS)  │   │ Storage │
   └─────────┘   └─────────┘   └─────────┘
```

## Summary

This architecture provides:

✅ **Separation of Concerns**: API layer, business logic, data persistence
✅ **Scalability**: Can migrate from JSON to database
✅ **Security**: Immutable hashing, watermarking, public verification
✅ **Maintainability**: Clear component responsibilities
✅ **Extensibility**: Easy to add new features
✅ **Performance**: Optimized for common operations
✅ **Reliability**: Error handling, validation, testing

Production-ready with clear upgrade paths for scaling.
