#!/usr/bin/env python3
"""
Carbon Room Database Initialization Script
==========================================
Initialize database, run migrations, and migrate existing manifest data.
"""

import argparse
import json
import hashlib
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import settings
from core.database import (
    init_db, drop_db, reset_db, get_db_session,
    apply_migrations, get_applied_migrations,
    Protocol, Creator, ProtocolCreator, Certificate, Watermark,
    ProtocolRepository, CreatorRepository, CertificateRepository,
    ProtocolType, CreatorRole
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent
MANIFEST_FILE = BASE_DIR / "manifest.json"
CERTIFICATES_DIR = settings.CERTIFICATE_DIR
DOCUMENTS_DIR = BASE_DIR / "documents"


def create_admin_user(db_session, name: str = "admin", email: str = "admin@carbonroom.io"):
    """Create an admin user if it doesn't exist."""
    creator_repo = CreatorRepository(db_session)

    existing = creator_repo.get_by_email(email)
    if existing:
        logger.info(f"Admin user already exists: {existing.name}")
        return existing

    admin = creator_repo.create(
        name=name,
        email=email,
        company="Carbon Room",
        verified=True
    )
    logger.info(f"Created admin user: {admin.name} ({admin.email})")
    return admin


def migrate_manifest_data(db_session, manifest_path: Path = MANIFEST_FILE, force: bool = False):
    """
    Migrate existing manifest.json data to database.

    Args:
        db_session: Database session
        manifest_path: Path to manifest.json
        force: If True, migrate even if database has data
    """
    if not manifest_path.exists():
        logger.warning(f"Manifest file not found: {manifest_path}")
        return {"migrated": 0, "skipped": 0, "failed": 0}

    # Check if database already has data
    protocol_repo = ProtocolRepository(db_session)
    existing_count = len(protocol_repo.list_all(limit=1))

    if existing_count > 0 and not force:
        logger.info("Database already has data. Use --force to migrate anyway.")
        return {"migrated": 0, "skipped": existing_count, "failed": 0}

    logger.info(f"Migrating manifest from: {manifest_path}")

    manifest = json.loads(manifest_path.read_text())
    protocols = manifest.get("protocols", {})

    creator_repo = CreatorRepository(db_session)
    cert_repo = CertificateRepository(db_session)

    results = {"migrated": 0, "skipped": 0, "failed": 0}

    for pid, p in protocols.items():
        try:
            # Check if already exists
            existing = protocol_repo.get_by_short_id(pid)
            if existing:
                logger.info(f"Protocol {pid} already exists, skipping")
                results["skipped"] += 1
                continue

            # Get or create creator
            creator = creator_repo.get_or_create(
                name=p.get("creator_name", "Unknown"),
                company=p.get("creator_company")
            )

            # Map type string to enum
            type_str = p.get("type", "document").lower()
            try:
                protocol_type = ProtocolType(type_str)
            except ValueError:
                protocol_type = ProtocolType.DOCUMENT

            # Generate watermark if missing
            watermark = p.get("watermark")
            if not watermark:
                watermark = f"C6-{pid.upper()}-LEGACY"

            # Generate blockchain hash if missing
            blockchain_hash = p.get("blockchain_hash")
            if not blockchain_hash:
                blockchain_hash = hashlib.sha256(
                    f"{pid}:{p.get('name', '')}:{p.get('created_at', '')}".encode()
                ).hexdigest()

            # Create protocol
            protocol = protocol_repo.create(
                short_id=pid,
                name=p.get("name", "Unknown"),
                blockchain_hash=blockchain_hash,
                watermark=watermark,
                creator_id=creator.id,
                description=p.get("description"),
                type=protocol_type,
                filename=p.get("filename"),
                version=p.get("version", "1.0"),
                tags=p.get("tags", []),
                is_remix=p.get("is_remix", False),
                original_hash=p.get("original_hash")
            )

            # Update invocation count
            invocations = p.get("invocations", 0)
            if invocations > 0:
                db_session.query(Protocol).filter(
                    Protocol.id == protocol.id
                ).update({Protocol.invocation_count: invocations})

            # Add co-creators
            for cc_name in p.get("co_creators", []):
                cc_creator = creator_repo.get_or_create(name=cc_name)
                db_session.add(ProtocolCreator(
                    protocol_id=protocol.id,
                    creator_id=cc_creator.id,
                    role=CreatorRole.CO_CREATOR
                ))

            # Migrate certificate if exists
            cert_id = p.get("certificate_id")
            if cert_id:
                cert_file = CERTIFICATES_DIR / f"{pid}_certificate.html"
                doc_file = DOCUMENTS_DIR / f"{pid}_copyright.txt"

                cert_html = ""
                doc_text = ""

                if cert_file.exists():
                    cert_html = cert_file.read_text()
                if doc_file.exists():
                    doc_text = doc_file.read_text()

                if cert_html:
                    cert_repo.create(
                        protocol_id=protocol.id,
                        certificate_id=cert_id,
                        certificate_html=cert_html,
                        document_text=doc_text,
                        certificate_hash=hashlib.sha256(cert_html.encode()).hexdigest()[:32]
                    )

            db_session.commit()
            results["migrated"] += 1
            logger.info(f"Migrated: {pid} - {p.get('name')}")

        except Exception as e:
            logger.error(f"Failed to migrate {pid}: {e}")
            db_session.rollback()
            results["failed"] += 1

    return results


def show_database_info(db_session):
    """Display database information."""
    from sqlalchemy import func

    print("\n" + "=" * 60)
    print("DATABASE INFORMATION")
    print("=" * 60)

    print(f"\nConnection: {settings.DATABASE_URL[:50]}...")
    print(f"Environment: {settings.ENV}")
    print(f"Type: {'PostgreSQL' if settings.is_postgres else 'SQLite'}")

    # Count records
    protocol_count = db_session.query(Protocol).count()
    creator_count = db_session.query(Creator).count()
    cert_count = db_session.query(Certificate).count()
    total_invocations = db_session.query(func.sum(Protocol.invocation_count)).scalar() or 0

    print(f"\nRecords:")
    print(f"  Protocols: {protocol_count}")
    print(f"  Creators: {creator_count}")
    print(f"  Certificates: {cert_count}")
    print(f"  Total Invocations: {total_invocations}")

    # Show migrations
    migrations = get_applied_migrations(db_session)
    print(f"\nApplied Migrations: {len(migrations)}")
    for m in migrations:
        print(f"  - {m}")

    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Carbon Room Database Initialization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize database and migrate manifest
  python scripts/init_db.py

  # Reset database (WARNING: deletes all data)
  python scripts/init_db.py --reset

  # Force re-migration of manifest
  python scripts/init_db.py --migrate --force

  # Show database info only
  python scripts/init_db.py --info

  # Create admin user
  python scripts/init_db.py --create-admin --admin-email admin@example.com
        """
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset database (drop and recreate all tables)"
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Migrate manifest.json to database"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force migration even if database has data"
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show database information"
    )
    parser.add_argument(
        "--create-admin",
        action="store_true",
        help="Create admin user"
    )
    parser.add_argument(
        "--admin-name",
        default="admin",
        help="Admin user name (default: admin)"
    )
    parser.add_argument(
        "--admin-email",
        default="admin@carbonroom.io",
        help="Admin user email (default: admin@carbonroom.io)"
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=MANIFEST_FILE,
        help=f"Path to manifest.json (default: {MANIFEST_FILE})"
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("CARBON ROOM DATABASE INITIALIZATION")
    print("=" * 60)
    print(f"\nDatabase: {settings.DATABASE_URL[:50]}...")
    print(f"Environment: {settings.ENV}")
    print()

    # Handle reset
    if args.reset:
        confirm = input("WARNING: This will DELETE ALL DATA. Type 'yes' to confirm: ")
        if confirm.lower() == "yes":
            logger.info("Resetting database...")
            reset_db()
            logger.info("Database reset complete")
        else:
            logger.info("Reset cancelled")
            return

    # Initialize database
    logger.info("Initializing database schema...")
    init_db()
    logger.info("Database schema initialized")

    # Apply migrations
    with get_db_session() as db:
        logger.info("Checking for pending migrations...")
        applied = apply_migrations(db)
        if applied:
            logger.info(f"Applied migrations: {applied}")
        else:
            logger.info("No pending migrations")

        # Create admin user if requested
        if args.create_admin:
            create_admin_user(db, args.admin_name, args.admin_email)

        # Migrate manifest if requested or if it's first run
        if args.migrate or not args.info:
            results = migrate_manifest_data(db, args.manifest, args.force)
            logger.info(
                f"Migration complete: {results['migrated']} migrated, "
                f"{results['skipped']} skipped, {results['failed']} failed"
            )

        # Show info
        if args.info or not (args.reset or args.migrate or args.create_admin):
            show_database_info(db)

    logger.info("Database initialization complete!")


if __name__ == "__main__":
    main()
