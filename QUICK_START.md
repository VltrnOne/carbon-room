# Carbon Room IP Registry - Quick Start Guide

## Installation (30 seconds)

```bash
cd /Users/Morpheous/vltrndataroom/global-dataroom

# Install dependencies
pip install fastapi uvicorn python-multipart requests

# Start server
python api/server.py
```

Server will start at **http://localhost:8003**

## Test the System (2 minutes)

In a new terminal:

```bash
# Run comprehensive test suite
python test_ip_registry.py
```

This will:
- Upload original smart contract
- Upload remix with attribution
- Upload asset with co-creators
- Generate certificates and documents
- Test watermark detection
- Verify attribution chains

## Basic Usage

### 1. Register an Asset

```bash
curl -X POST "http://localhost:8003/api/upload" \
  -F "name=MyContract" \
  -F "tags=solidity,blockchain" \
  -F "description=My smart contract" \
  -F "type=code" \
  -F "creator_name=Your Name" \
  -F "creator_company=Your Company" \
  -F "file=@./path/to/contract.sol"
```

### 2. View Certificate

Visit: `http://localhost:8003/api/certificate/{asset_id}`

Or save to file:
```bash
curl http://localhost:8003/api/certificate/{asset_id} > certificate.html
open certificate.html
```

### 3. Get Copyright Document

```bash
curl http://localhost:8003/api/document/{asset_id}
```

### 4. Verify by Hash

```bash
curl http://localhost:8003/api/verify/{hash_prefix}
```

## API Documentation

Interactive API docs at: **http://localhost:8003/docs**

## Key Features

✓ Legal copyright document generation
✓ Automatic watermark injection (code files)
✓ HTML certificates (print-ready)
✓ Remix attribution chains
✓ Public hash verification
✓ SHA-256 blockchain hashing

## Next Steps

1. Read full documentation: `IP_REGISTRY_README.md`
2. Explore API at `/docs` endpoint
3. View admin dashboard at `/admin`
4. Check manifest.json for registry data

## Production Checklist

Before deploying to production:

- [ ] Add encryption to vault storage
- [ ] Implement API authentication
- [ ] Add rate limiting
- [ ] Configure HTTPS/TLS
- [ ] Set up database backup
- [ ] Add blockchain anchoring
- [ ] Enable audit logging
- [ ] Review legal compliance

## Support

For questions or issues:
- Check server logs
- Review manifest.json
- Test with `test_ip_registry.py`
- Verify directories are writable
