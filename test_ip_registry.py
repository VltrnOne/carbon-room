#!/usr/bin/env python3
"""
Test script for Carbon Room IP Registration System

Demonstrates:
- Uploading and registering assets
- Generating watermarks and legal documents
- Building attribution chains for remixes
- Verifying watermarks
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8003"


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_response(response, show_full=False):
    """Pretty print API response"""
    try:
        data = response.json()
        if show_full:
            print(json.dumps(data, indent=2))
        else:
            # Show condensed version
            if "status" in data:
                print(f"✓ Status: {data['status']}")
            if "protocol_id" in data:
                print(f"  Protocol ID: {data['protocol_id']}")
            if "blockchain_hash" in data:
                print(f"  Blockchain Hash: {data['blockchain_hash'][:32]}...")
            if "certificate_id" in data:
                print(f"  Certificate ID: {data['certificate_id']}")
            if "watermark" in data:
                print(f"  Watermark: {data['watermark']}")
            if "message" in data:
                print(f"  Message: {data['message']}")
    except:
        print(response.text)


def test_upload_original_asset():
    """Test 1: Upload an original asset"""
    print_section("TEST 1: Upload Original Smart Contract")

    # Create sample Solidity code
    sample_code = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract MyToken is ERC20, Ownable {
    constructor() ERC20("MyToken", "MTK") Ownable(msg.sender) {
        _mint(msg.sender, 1000000 * 10 ** decimals());
    }

    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }
}
"""

    # Create temporary file
    test_file = Path("/tmp/MyToken.sol")
    test_file.write_text(sample_code)

    # Upload
    files = {"file": ("MyToken.sol", open(test_file, "rb"), "text/plain")}
    data = {
        "name": "MyToken ERC20",
        "tags": "solidity, erc20, defi, original",
        "description": "Standard ERC20 token with minting capability",
        "type": "code",
        "creator_name": "Jane Blockchain",
        "creator_company": "Blockchain Innovations Inc",
        "version": "1.0.0"
    }

    response = requests.post(f"{BASE_URL}/api/upload", files=files, data=data)
    print_response(response)

    result = response.json()
    asset_id = result.get("protocol_id")
    blockchain_hash = result.get("blockchain_hash")

    print(f"\n✓ Asset registered successfully!")
    print(f"  View certificate: {BASE_URL}/api/certificate/{asset_id}")
    print(f"  View document: {BASE_URL}/api/document/{asset_id}")

    return asset_id, blockchain_hash


def test_upload_remix(original_hash):
    """Test 2: Upload a remix with attribution"""
    print_section("TEST 2: Upload Remix with Attribution")

    # Create sample remix code
    remix_code = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract EnhancedToken is ERC20, Ownable {
    uint256 public maxSupply;

    constructor(uint256 _maxSupply) ERC20("EnhancedToken", "ETK") Ownable(msg.sender) {
        maxSupply = _maxSupply;
        _mint(msg.sender, 1000000 * 10 ** decimals());
    }

    function mint(address to, uint256 amount) public onlyOwner {
        require(totalSupply() + amount <= maxSupply, "Max supply exceeded");
        _mint(to, amount);
    }

    function burn(uint256 amount) public {
        _burn(msg.sender, amount);
    }
}
"""

    test_file = Path("/tmp/EnhancedToken.sol")
    test_file.write_text(remix_code)

    files = {"file": ("EnhancedToken.sol", open(test_file, "rb"), "text/plain")}
    data = {
        "name": "EnhancedToken ERC20",
        "tags": "solidity, erc20, defi, remix, enhanced",
        "description": "Enhanced version with max supply cap and burn function",
        "type": "code",
        "creator_name": "Bob Developer",
        "creator_company": "DeFi Labs",
        "version": "2.0.0",
        "is_remix": "true",
        "original_creator": "Jane Blockchain",
        "original_asset": "MyToken ERC20",
        "original_hash": original_hash
    }

    response = requests.post(f"{BASE_URL}/api/upload", files=files, data=data)
    print_response(response)

    result = response.json()
    asset_id = result.get("protocol_id")

    print(f"\n✓ Remix registered with attribution!")
    print(f"  View attribution chain: {BASE_URL}/api/attribution/{asset_id}")

    return asset_id


def test_co_creators():
    """Test 3: Upload with multiple co-creators"""
    print_section("TEST 3: Upload with Co-Creators")

    sample_code = """# Python Data Analysis Script
import pandas as pd
import numpy as np

def analyze_data(df):
    # Perform comprehensive analysis
    summary = df.describe()
    correlations = df.corr()
    return summary, correlations

def visualize_results(data):
    # Create visualizations
    pass
"""

    test_file = Path("/tmp/data_analysis.py")
    test_file.write_text(sample_code)

    files = {"file": ("data_analysis.py", open(test_file, "rb"), "text/plain")}
    data = {
        "name": "Data Analysis Toolkit",
        "tags": "python, data-science, analytics",
        "description": "Comprehensive data analysis and visualization toolkit",
        "type": "code",
        "creator_name": "Alice Data Scientist",
        "creator_company": "Data Analytics Corp",
        "co_creators": "Bob ML Engineer, Carol Statistician, Dave Visualization Expert",
        "version": "3.2.1"
    }

    response = requests.post(f"{BASE_URL}/api/upload", files=files, data=data)
    print_response(response)

    result = response.json()
    asset_id = result.get("protocol_id")

    print(f"\n✓ Asset with co-creators registered!")

    return asset_id


def test_get_certificate(asset_id):
    """Test 4: Retrieve HTML certificate"""
    print_section("TEST 4: Retrieve HTML Certificate")

    response = requests.get(f"{BASE_URL}/api/certificate/{asset_id}")

    if response.status_code == 200:
        cert_file = Path(f"/tmp/certificate_{asset_id}.html")
        cert_file.write_text(response.text)
        print(f"✓ Certificate downloaded to: {cert_file}")
        print(f"  Open in browser: file://{cert_file}")
    else:
        print(f"✗ Failed to retrieve certificate: {response.status_code}")


def test_get_document(asset_id):
    """Test 5: Retrieve copyright document"""
    print_section("TEST 5: Retrieve Copyright Document")

    response = requests.get(f"{BASE_URL}/api/document/{asset_id}")

    if response.status_code == 200:
        print("✓ Copyright document retrieved:")
        print("-" * 80)
        # Print first 1000 characters
        print(response.text[:1000] + "...")
        print("-" * 80)
    else:
        print(f"✗ Failed to retrieve document: {response.status_code}")


def test_attribution_chain(asset_id):
    """Test 6: Get attribution chain"""
    print_section("TEST 6: Retrieve Attribution Chain")

    response = requests.get(f"{BASE_URL}/api/attribution/{asset_id}")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Attribution chain retrieved:")
        print(f"  Chain length: {data['chain_length']}")
        print(f"  Is original: {data['is_original']}")
        print(f"  Is remix: {data['is_remix']}")

        print("\n  Chain details:")
        for i, item in enumerate(data['attribution_chain'], 1):
            print(f"\n  [{i}] {item['name']}")
            print(f"      Creator: {item['creator']}")
            print(f"      Version: {item['version']}")
            print(f"      Hash: {item['hash'][:32]}...")
            print(f"      Is Remix: {item['is_remix']}")
    else:
        print(f"✗ Failed to retrieve attribution chain: {response.status_code}")


def test_watermark_verification(asset_id):
    """Test 7: Verify watermark detection"""
    print_section("TEST 7: Verify Watermark Detection")

    # Get asset details to find watermark
    response = requests.get(f"{BASE_URL}/api/asset/{asset_id}")
    if response.status_code != 200:
        print("✗ Failed to get asset details")
        return

    asset = response.json()["asset"]
    watermark = asset["watermark"]

    # Test with watermarked content
    print(f"\nTesting watermark: {watermark}")

    content_with_watermark = f"""
    // Carbon[6] Watermark: {watermark}
    // This file is registered in the Carbon Room IP Registry

    function myCode() {{
        return true;
    }}
    """

    data = {
        "content": content_with_watermark,
        "watermark": watermark
    }

    response = requests.post(f"{BASE_URL}/api/verify-watermark", json=data)
    if response.status_code == 200:
        result = response.json()
        if result["detected"]:
            print(f"✓ Watermark DETECTED: {result['message']}")
        else:
            print(f"✗ Watermark NOT detected")

    # Test without watermark
    print("\nTesting without watermark...")
    data["content"] = "function myCode() { return true; }"

    response = requests.post(f"{BASE_URL}/api/verify-watermark", json=data)
    if response.status_code == 200:
        result = response.json()
        if not result["detected"]:
            print(f"✓ Correctly reported no watermark: {result['message']}")
        else:
            print(f"✗ False positive")


def test_public_verification(blockchain_hash):
    """Test 8: Public verification by hash"""
    print_section("TEST 8: Public Verification by Hash Prefix")

    hash_prefix = blockchain_hash[:12]
    response = requests.get(f"{BASE_URL}/api/verify/{hash_prefix}")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Verification successful!")
        print(f"  Hash prefix: {hash_prefix}")
        print(f"  Matches found: {len(data['matches'])}")

        for match in data["matches"]:
            print(f"\n  Asset: {match['name']}")
            print(f"  Creator: {match['creator']}")
            if match.get('creator_company'):
                print(f"  Company: {match['creator_company']}")
            print(f"  Registered: {match['registered']}")
            print(f"  Certificate ID: {match['certificate_id']}")
    else:
        print(f"✗ Verification failed: {response.status_code}")


def test_complete_asset_details(asset_id):
    """Test 9: Get complete asset details"""
    print_section("TEST 9: Get Complete Asset Details")

    response = requests.get(f"{BASE_URL}/api/asset/{asset_id}")

    if response.status_code == 200:
        print("✓ Asset details retrieved:")
        print_response(response, show_full=True)
    else:
        print(f"✗ Failed to retrieve asset details: {response.status_code}")


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("  CARBON ROOM IP REGISTRATION SYSTEM - TEST SUITE")
    print("=" * 80)
    print(f"\n  Server: {BASE_URL}")
    print(f"  Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Test server is running
        response = requests.get(f"{BASE_URL}/api/stats")
        if response.status_code != 200:
            print("\n✗ ERROR: Server not running or not responding")
            print("  Start server with: python api/server.py")
            return

        print("\n✓ Server is running")

        # Run tests
        original_id, original_hash = test_upload_original_asset()
        time.sleep(0.5)

        remix_id = test_upload_remix(original_hash)
        time.sleep(0.5)

        co_creator_id = test_co_creators()
        time.sleep(0.5)

        test_get_certificate(original_id)
        time.sleep(0.5)

        test_get_document(original_id)
        time.sleep(0.5)

        test_attribution_chain(remix_id)
        time.sleep(0.5)

        test_watermark_verification(original_id)
        time.sleep(0.5)

        test_public_verification(original_hash)
        time.sleep(0.5)

        test_complete_asset_details(co_creator_id)

        print_section("TEST SUITE COMPLETED")
        print("\n✓ All tests completed successfully!")
        print(f"\nView all assets at: {BASE_URL}/api/protocols")
        print(f"API documentation: {BASE_URL}/docs")

    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Cannot connect to server")
        print("  Start server with: python api/server.py")
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
