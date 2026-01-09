#!/usr/bin/env python3
"""
Carbon Room IP Registry System
Handles legal document generation, watermarking, and remix attribution chains
"""

import hashlib
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path


class IPRegistry:
    """Intellectual Property Registration and Management System"""

    def __init__(self, manifest_path: Path):
        self.manifest_path = manifest_path

    def generate_copyright_document(
        self,
        asset_name: str,
        creator: str,
        timestamp: str,
        hash_value: str,
        creator_company: Optional[str] = None,
        co_creators: Optional[List[str]] = None,
        asset_type: str = "digital asset",
        is_remix: bool = False,
        original_creator: Optional[str] = None,
        original_asset: Optional[str] = None,
        version: str = "1.0"
    ) -> str:
        """
        Generate legal copyright notice document

        @notice Creates a legally-formatted copyright certificate
        @param asset_name Name of the intellectual property
        @param creator Primary creator name
        @param timestamp ISO 8601 registration timestamp
        @param hash_value SHA-256 hash of asset + metadata
        @param creator_company Optional company name
        @param co_creators Optional list of co-creator names
        @param asset_type Type of asset (code, document, design, etc.)
        @param is_remix Whether this is a remix/derivative work
        @param original_creator Original creator for remix attribution
        @param original_asset Original asset name for remix attribution
        @param version Version identifier
        @return Formatted legal document text
        """

        # Parse timestamp for readable date
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            date_str = dt.strftime("%B %d, %Y at %H:%M:%S UTC")
        except:
            date_str = timestamp

        # Build creator attribution
        creator_line = f"Creator: {creator}"
        if creator_company:
            creator_line += f" ({creator_company})"

        # Build co-creators section
        co_creators_section = ""
        if co_creators and len(co_creators) > 0:
            co_creators_section = "\nCo-Creators:\n"
            for cc in co_creators:
                co_creators_section += f"  - {cc}\n"

        # Build remix attribution section
        remix_section = ""
        if is_remix and original_creator:
            remix_section = f"""
DERIVATIVE WORK ATTRIBUTION:
This work is a derivative/remix of:
  Original Asset: {original_asset or 'Not specified'}
  Original Creator: {original_creator}

This derivative work acknowledges and respects the intellectual property
rights of the original creator while asserting independent creative
contributions by the creators listed above.
"""

        # Build main document
        document = f"""
{'='*80}
CERTIFICATE OF INTELLECTUAL PROPERTY REGISTRATION
{'='*80}

ASSET INFORMATION:
  Name: {asset_name}
  Type: {asset_type}
  Version: {version}

CREATOR INFORMATION:
  {creator_line}{co_creators_section}

REGISTRATION DETAILS:
  Registration Date: {date_str}
  Registration Hash: {hash_value}
  Registry: Carbon Room Blockchain IP Registry
  Certificate ID: C6-{hash_value[:16].upper()}
{remix_section}
LEGAL NOTICE:

This document certifies that the above intellectual property was registered
on the Carbon Room blockchain registry on {date_str}.

The SHA-256 hash serves as immutable proof of existence and ownership at the
time of registration. This certificate establishes a verifiable timestamp
for the creation and registration of this intellectual property.

RIGHTS AND PROTECTIONS:

1. COPYRIGHT PROTECTION: This work is protected under applicable copyright
   laws. All rights are reserved by the creator(s) listed above.

2. BLOCKCHAIN VERIFICATION: The registration hash can be independently
   verified on the Carbon Room blockchain registry to confirm authenticity
   and timestamp.

3. DERIVATIVE WORKS: Any derivative works, remixes, or adaptations must
   provide proper attribution to the original creator(s) and maintain
   the attribution chain through the Carbon Room registry.

4. WATERMARK PROTECTION: This asset contains a unique Carbon[6] watermark
   for provenance tracking and unauthorized use detection.

CARBON[6] SIGNATURE:

This certificate is issued by the Carbon[6] Intellectual Property Registry,
a decentralized system for creator rights protection and attribution tracking.

Certificate Hash: {self._generate_certificate_hash(asset_name, creator, timestamp, hash_value)}
Issued: {datetime.utcnow().isoformat()}Z

For verification, visit: https://carbonroom.io/verify/{hash_value[:16]}

{'='*80}
END OF CERTIFICATE
{'='*80}

This is a computer-generated document. No signature is required for validity.
The blockchain registration hash serves as cryptographic proof of authenticity.
"""
        return document

    def generate_certificate_html(self, registration_data: Dict[str, Any]) -> str:
        """
        Generate HTML certificate for web display

        @notice Creates a styled HTML version of the registration certificate
        @param registration_data Full registration metadata dictionary
        @return HTML certificate as string
        """

        asset_name = registration_data.get('name', 'Unnamed Asset')
        creator = registration_data.get('creator_name', 'Unknown Creator')
        creator_company = registration_data.get('creator_company', '')
        timestamp = registration_data.get('created_at', datetime.utcnow().isoformat())
        hash_value = registration_data.get('blockchain_hash', '')
        co_creators = registration_data.get('co_creators', [])
        asset_type = registration_data.get('type', 'digital asset')
        version = registration_data.get('version', '1.0')
        is_remix = registration_data.get('is_remix', False)
        original_creator = registration_data.get('original_creator', '')
        watermark = registration_data.get('watermark', '')

        # Parse timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            date_str = dt.strftime("%B %d, %Y")
            time_str = dt.strftime("%H:%M:%S UTC")
        except:
            date_str = timestamp
            time_str = ""

        # Build co-creators HTML
        co_creators_html = ""
        if co_creators and len(co_creators) > 0:
            co_creators_html = "<div class='co-creators'><h3>Co-Creators</h3><ul>"
            for cc in co_creators:
                co_creators_html += f"<li>{cc}</li>"
            co_creators_html += "</ul></div>"

        # Build remix attribution HTML
        remix_html = ""
        if is_remix and original_creator:
            original_asset = registration_data.get('original_asset', 'Not specified')
            remix_html = f"""
            <div class='remix-attribution'>
                <h3>Derivative Work Attribution</h3>
                <p><strong>Original Asset:</strong> {original_asset}</p>
                <p><strong>Original Creator:</strong> {original_creator}</p>
                <p class='remix-note'>This derivative work acknowledges and respects the intellectual
                property rights of the original creator.</p>
            </div>
            """

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IP Registration Certificate - {asset_name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Georgia', serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px 20px;
            min-height: 100vh;
        }}

        .certificate {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border: 20px solid #2d3748;
            border-image: linear-gradient(45deg, #667eea, #764ba2) 1;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            position: relative;
        }}

        .certificate::before {{
            content: '';
            position: absolute;
            top: 10px;
            left: 10px;
            right: 10px;
            bottom: 10px;
            border: 2px solid #cbd5e0;
            pointer-events: none;
        }}

        .header {{
            text-align: center;
            padding: 40px 40px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}

        .header h1 {{
            font-size: 2rem;
            margin-bottom: 10px;
            letter-spacing: 2px;
        }}

        .header .subtitle {{
            font-size: 1rem;
            opacity: 0.9;
            font-style: italic;
        }}

        .content {{
            padding: 40px 60px;
        }}

        .section {{
            margin-bottom: 30px;
        }}

        .section h2 {{
            color: #667eea;
            font-size: 1.3rem;
            margin-bottom: 15px;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 8px;
        }}

        .section h3 {{
            color: #4a5568;
            font-size: 1.1rem;
            margin-bottom: 10px;
            margin-top: 20px;
        }}

        .info-grid {{
            display: grid;
            grid-template-columns: 200px 1fr;
            gap: 12px;
            margin: 15px 0;
        }}

        .info-label {{
            font-weight: bold;
            color: #4a5568;
        }}

        .info-value {{
            color: #2d3748;
        }}

        .hash-display {{
            font-family: 'Courier New', monospace;
            background: #f7fafc;
            padding: 12px;
            border-left: 4px solid #667eea;
            word-break: break-all;
            font-size: 0.9rem;
            margin: 15px 0;
        }}

        .co-creators ul {{
            list-style: none;
            margin-left: 20px;
        }}

        .co-creators li {{
            padding: 5px 0;
            color: #2d3748;
        }}

        .co-creators li::before {{
            content: '→ ';
            color: #667eea;
            font-weight: bold;
        }}

        .remix-attribution {{
            background: #fff5f5;
            border: 2px solid #fc8181;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}

        .remix-attribution h3 {{
            color: #c53030;
        }}

        .remix-note {{
            font-style: italic;
            color: #4a5568;
            margin-top: 10px;
        }}

        .legal-notice {{
            background: #edf2f7;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            font-size: 0.9rem;
            line-height: 1.6;
        }}

        .signature {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 3px double #cbd5e0;
            text-align: center;
        }}

        .signature .logo {{
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }}

        .signature .date {{
            color: #718096;
            font-style: italic;
        }}

        .watermark {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(-45deg);
            font-size: 5rem;
            color: rgba(102, 126, 234, 0.05);
            pointer-events: none;
            font-weight: bold;
            white-space: nowrap;
        }}

        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .certificate {{
                box-shadow: none;
                max-width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <div class="certificate">
        <div class="watermark">CARBON[6]</div>

        <div class="header">
            <h1>CERTIFICATE OF INTELLECTUAL PROPERTY REGISTRATION</h1>
            <p class="subtitle">Carbon Room Blockchain Registry</p>
        </div>

        <div class="content">
            <div class="section">
                <h2>Asset Information</h2>
                <div class="info-grid">
                    <div class="info-label">Asset Name:</div>
                    <div class="info-value">{asset_name}</div>

                    <div class="info-label">Asset Type:</div>
                    <div class="info-value">{asset_type}</div>

                    <div class="info-label">Version:</div>
                    <div class="info-value">{version}</div>

                    <div class="info-label">Certificate ID:</div>
                    <div class="info-value">C6-{hash_value[:16].upper()}</div>
                </div>
            </div>

            <div class="section">
                <h2>Creator Information</h2>
                <div class="info-grid">
                    <div class="info-label">Primary Creator:</div>
                    <div class="info-value">{creator}</div>

                    {'<div class="info-label">Company:</div>' if creator_company else ''}
                    {'<div class="info-value">' + creator_company + '</div>' if creator_company else ''}
                </div>
                {co_creators_html}
            </div>

            {remix_html}

            <div class="section">
                <h2>Registration Details</h2>
                <div class="info-grid">
                    <div class="info-label">Registration Date:</div>
                    <div class="info-value">{date_str} {time_str}</div>

                    <div class="info-label">Watermark ID:</div>
                    <div class="info-value">{watermark}</div>
                </div>

                <h3>Blockchain Hash (SHA-256)</h3>
                <div class="hash-display">{hash_value}</div>
            </div>

            <div class="legal-notice">
                <h3>Legal Notice</h3>
                <p>
                    This document certifies that the above intellectual property was registered
                    on the Carbon Room blockchain registry on <strong>{date_str}</strong>.
                    The SHA-256 hash serves as immutable proof of existence and ownership at the
                    time of registration.
                </p>
                <p style="margin-top: 10px;">
                    This certificate establishes a verifiable timestamp for the creation and
                    registration of this intellectual property. All rights are reserved by
                    the creator(s) listed above.
                </p>
            </div>

            <div class="signature">
                <div class="logo">CARBON[6]</div>
                <p>Intellectual Property Registry</p>
                <p class="date">Issued: {datetime.utcnow().strftime('%B %d, %Y')}</p>
                <p style="margin-top: 15px; font-size: 0.8rem; color: #718096;">
                    Verify at: carbonroom.io/verify/{hash_value[:16]}
                </p>
            </div>
        </div>
    </div>
</body>
</html>
"""
        return html

    def generate_watermark(
        self,
        asset_id: str,
        creator: str,
        timestamp: str
    ) -> str:
        """
        Generate unique watermark identifier

        @notice Creates a unique, detectable watermark for asset tracking
        @param asset_id Unique asset identifier
        @param creator Creator name
        @param timestamp Registration timestamp
        @return Watermark string in format C6-{asset_id}-{creator_hash}
        """

        # Create creator hash from name + timestamp
        creator_data = f"{creator}:{timestamp}".encode()
        creator_hash = hashlib.sha256(creator_data).hexdigest()[:8]

        watermark = f"C6-{asset_id}-{creator_hash}"
        return watermark.upper()

    def detect_watermark(self, content: str, watermark: str) -> bool:
        """
        Check if content contains the specified watermark

        @notice Searches for watermark in content (case-insensitive)
        @param content Content to search
        @param watermark Watermark to find
        @return True if watermark is present
        """

        if not content or not watermark:
            return False

        return watermark.upper() in content.upper()

    def inject_watermark_comment(
        self,
        content: str,
        watermark: str,
        file_extension: str
    ) -> str:
        """
        Inject watermark as comment into code/document files

        @notice Adds watermark comment header based on file type
        @param content Original file content
        @param watermark Watermark identifier
        @param file_extension File extension (.py, .js, .sol, etc.)
        @return Content with watermark injected
        """

        # Define comment styles by extension
        comment_styles = {
            '.py': f'# Carbon[6] Watermark: {watermark}\n# This file is registered in the Carbon Room IP Registry\n\n',
            '.js': f'// Carbon[6] Watermark: {watermark}\n// This file is registered in the Carbon Room IP Registry\n\n',
            '.ts': f'// Carbon[6] Watermark: {watermark}\n// This file is registered in the Carbon Room IP Registry\n\n',
            '.sol': f'// SPDX-License-Identifier: MIT\n// Carbon[6] Watermark: {watermark}\n// This file is registered in the Carbon Room IP Registry\n\n',
            '.go': f'// Carbon[6] Watermark: {watermark}\n// This file is registered in the Carbon Room IP Registry\n\n',
            '.rs': f'// Carbon[6] Watermark: {watermark}\n// This file is registered in the Carbon Room IP Registry\n\n',
            '.java': f'// Carbon[6] Watermark: {watermark}\n// This file is registered in the Carbon Room IP Registry\n\n',
            '.cpp': f'// Carbon[6] Watermark: {watermark}\n// This file is registered in the Carbon Room IP Registry\n\n',
            '.c': f'// Carbon[6] Watermark: {watermark}\n// This file is registered in the Carbon Room IP Registry\n\n',
            '.html': f'<!-- Carbon[6] Watermark: {watermark} -->\n<!-- This file is registered in the Carbon Room IP Registry -->\n\n',
            '.css': f'/* Carbon[6] Watermark: {watermark} */\n/* This file is registered in the Carbon Room IP Registry */\n\n',
            '.md': f'<!-- Carbon[6] Watermark: {watermark} -->\n<!-- This file is registered in the Carbon Room IP Registry -->\n\n',
        }

        # Get appropriate comment style
        comment = comment_styles.get(file_extension.lower(), f'# Carbon[6] Watermark: {watermark}\n\n')

        # Inject at beginning
        return comment + content

    def build_attribution_chain(self, asset_id: str) -> List[Dict[str, Any]]:
        """
        Build complete remix/derivative attribution chain

        @notice Traces the lineage of remixes back to original asset
        @param asset_id Starting asset ID
        @return List of attribution records from original to current
        """

        # Load manifest
        if not self.manifest_path.exists():
            return []

        manifest = json.loads(self.manifest_path.read_text())
        protocols = manifest.get('protocols', {})

        # Find the asset
        if asset_id not in protocols:
            return []

        chain = []
        current_id = asset_id
        visited = set()  # Prevent infinite loops

        # Walk backwards through remix chain
        while current_id and current_id not in visited:
            visited.add(current_id)

            if current_id not in protocols:
                break

            asset = protocols[current_id]

            # Add to chain
            chain.append({
                'asset_id': current_id,
                'name': asset.get('name', ''),
                'creator': asset.get('creator_name', ''),
                'company': asset.get('creator_company', ''),
                'timestamp': asset.get('created_at', ''),
                'hash': asset.get('blockchain_hash', ''),
                'is_remix': asset.get('is_remix', False),
                'version': asset.get('version', '1.0')
            })

            # Move to original if this is a remix
            if asset.get('is_remix') and asset.get('original_hash'):
                # Find asset by hash
                original_id = None
                for pid, p in protocols.items():
                    if p.get('blockchain_hash') == asset.get('original_hash'):
                        original_id = pid
                        break
                current_id = original_id
            else:
                # End of chain
                break

        # Reverse so original is first
        chain.reverse()
        return chain

    def _generate_certificate_hash(
        self,
        asset_name: str,
        creator: str,
        timestamp: str,
        asset_hash: str
    ) -> str:
        """Generate a unique hash for the certificate itself"""
        combined = f"{asset_name}:{creator}:{timestamp}:{asset_hash}".encode()
        return hashlib.sha256(combined).hexdigest()[:32]

    def generate_composite_hash(
        self,
        file_content: bytes,
        metadata: Dict[str, Any],
        timestamp: str
    ) -> str:
        """
        Generate comprehensive hash of file + metadata + timestamp

        @notice Creates SHA-256 hash combining all registration data
        @param file_content Raw file bytes
        @param metadata Registration metadata dictionary
        @param timestamp ISO 8601 timestamp
        @return SHA-256 hash as hex string
        """

        # Start with file content hash
        content_hash = hashlib.sha256(file_content).hexdigest()

        # Build metadata string (sorted keys for consistency)
        metadata_str = json.dumps(metadata, sort_keys=True)

        # Combine all elements
        combined = f"{content_hash}:{metadata_str}:{timestamp}".encode()

        return hashlib.sha256(combined).hexdigest()
