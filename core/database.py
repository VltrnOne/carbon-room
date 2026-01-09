"""
Carbon Room Database Layer
==========================
SQLAlchemy ORM with support for SQLite (dev) and PostgreSQL (production).
Includes models, migrations, and connection management.
"""

import json
import logging
from datetime import datetime
from typing import Optional, List, Generator, Dict, Any
from contextlib import contextmanager
from enum import Enum

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Index,
    UniqueConstraint,
    Enum as SQLEnum,
    event,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (
    sessionmaker,
    Session,
    relationship,
    scoped_session,
)
from sqlalchemy.pool import StaticPool

from .config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create base class for declarative models
Base = declarative_base()


# ============================================================================
# Enums
# ============================================================================

class ProtocolType(str, Enum):
    """Types of protocols/assets that can be registered."""
    CODE = "code"
    CONFIG = "config"
    AGENT = "agent"
    DOCUMENT = "document"
    DESIGN = "design"
    MEDIA = "media"


class CreatorRole(str, Enum):
    """Roles a creator can have for a protocol."""
    OWNER = "owner"
    CO_CREATOR = "co_creator"
    REMIX_SOURCE = "remix_source"


# ============================================================================
# Models
# ============================================================================

class Creator(Base):
    """
    Creator entity - represents individuals or organizations that create IP.
    """
    __tablename__ = "creators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    company = Column(String(255), nullable=True)
    verified = Column(Boolean, default=False)
    api_key_hash = Column(String(64), nullable=True)  # For API authentication
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    protocols = relationship(
        "ProtocolCreator",
        back_populates="creator",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Creator(id={self.id}, name='{self.name}')>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "company": self.company,
            "verified": self.verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Protocol(Base):
    """
    Protocol/Asset entity - represents registered intellectual property.
    """
    __tablename__ = "protocols"

    id = Column(Integer, primary_key=True, autoincrement=True)
    short_id = Column(String(8), unique=True, nullable=False, index=True)  # UUID prefix
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    type = Column(SQLEnum(ProtocolType), nullable=False, default=ProtocolType.DOCUMENT)
    filename = Column(String(255), nullable=True)
    version = Column(String(20), default="1.0")

    # Blockchain/Hash data
    file_hash = Column(String(64), nullable=True)  # SHA-256 of file content
    blockchain_hash = Column(String(64), unique=True, nullable=False, index=True)  # Combined hash
    watermark = Column(String(50), unique=True, nullable=False, index=True)

    # Tags stored as JSON array
    tags = Column(JSON, default=list)

    # Remix/Derivative tracking
    is_remix = Column(Boolean, default=False)
    original_protocol_id = Column(Integer, ForeignKey("protocols.id"), nullable=True)
    original_hash = Column(String(64), nullable=True)

    # Stats
    invocation_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creators = relationship(
        "ProtocolCreator",
        back_populates="protocol",
        cascade="all, delete-orphan"
    )
    invocations = relationship(
        "Invocation",
        back_populates="protocol",
        cascade="all, delete-orphan"
    )
    certificates = relationship(
        "Certificate",
        back_populates="protocol",
        cascade="all, delete-orphan"
    )
    original = relationship(
        "Protocol",
        remote_side=[id],
        backref="remixes"
    )

    # Indexes
    __table_args__ = (
        Index("ix_protocols_type_created", "type", "created_at"),
        Index("ix_protocols_tags", "tags", postgresql_using="gin"),
    )

    def __repr__(self):
        return f"<Protocol(id={self.id}, short_id='{self.short_id}', name='{self.name}')>"

    def to_dict(self, include_creators: bool = True) -> Dict[str, Any]:
        result = {
            "id": self.short_id,
            "name": self.name,
            "description": self.description,
            "type": self.type.value if self.type else None,
            "filename": self.filename,
            "version": self.version,
            "blockchain_hash": self.blockchain_hash,
            "watermark": self.watermark,
            "tags": self.tags or [],
            "is_remix": self.is_remix,
            "original_hash": self.original_hash,
            "invocations": self.invocation_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        if include_creators:
            owner = next(
                (pc.creator for pc in self.creators if pc.role == CreatorRole.OWNER),
                None
            )
            co_creators = [
                pc.creator.name for pc in self.creators
                if pc.role == CreatorRole.CO_CREATOR
            ]
            if owner:
                result["creator_name"] = owner.name
                result["creator_company"] = owner.company
            result["co_creators"] = co_creators

        return result


class ProtocolCreator(Base):
    """
    Junction table linking protocols to creators with roles.
    """
    __tablename__ = "protocol_creators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    protocol_id = Column(Integer, ForeignKey("protocols.id"), nullable=False)
    creator_id = Column(Integer, ForeignKey("creators.id"), nullable=False)
    role = Column(SQLEnum(CreatorRole), nullable=False, default=CreatorRole.OWNER)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    protocol = relationship("Protocol", back_populates="creators")
    creator = relationship("Creator", back_populates="protocols")

    __table_args__ = (
        UniqueConstraint("protocol_id", "creator_id", "role", name="uq_protocol_creator_role"),
        Index("ix_protocol_creators_role", "role"),
    )

    def __repr__(self):
        return f"<ProtocolCreator(protocol_id={self.protocol_id}, creator_id={self.creator_id}, role='{self.role}')>"


class Invocation(Base):
    """
    Invocation record - tracks when protocols are invoked/used.
    """
    __tablename__ = "invocations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    protocol_id = Column(Integer, ForeignKey("protocols.id"), nullable=False)
    user_id = Column(String(255), nullable=True, index=True)  # External user ID
    user_ip = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    telemetry = Column(JSON, default=dict)  # Additional telemetry data
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    protocol = relationship("Protocol", back_populates="invocations")

    __table_args__ = (
        Index("ix_invocations_protocol_date", "protocol_id", "created_at"),
    )

    def __repr__(self):
        return f"<Invocation(id={self.id}, protocol_id={self.protocol_id})>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "protocol_id": self.protocol_id,
            "user_id": self.user_id,
            "telemetry": self.telemetry,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Certificate(Base):
    """
    Certificate record - stores generated legal certificates.
    """
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    protocol_id = Column(Integer, ForeignKey("protocols.id"), nullable=False)
    certificate_id = Column(String(30), unique=True, nullable=False, index=True)  # C6-{hash[:16]}
    certificate_html = Column(Text, nullable=False)
    document_text = Column(Text, nullable=True)  # Plain text version
    certificate_hash = Column(String(64), nullable=True)  # Hash of certificate content
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    protocol = relationship("Protocol", back_populates="certificates")

    def __repr__(self):
        return f"<Certificate(id={self.id}, certificate_id='{self.certificate_id}')>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "protocol_id": self.protocol_id,
            "certificate_id": self.certificate_id,
            "certificate_hash": self.certificate_hash,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Watermark(Base):
    """
    Watermark registry - tracks watermark usage and detection.
    """
    __tablename__ = "watermarks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    watermark = Column(String(50), unique=True, nullable=False, index=True)
    protocol_id = Column(Integer, ForeignKey("protocols.id"), nullable=False)
    detection_count = Column(Integer, default=0)
    last_detected_at = Column(DateTime, nullable=True)
    last_detected_url = Column(String(2000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Index for detection queries
    __table_args__ = (
        Index("ix_watermarks_detection", "detection_count", "last_detected_at"),
    )

    def __repr__(self):
        return f"<Watermark(id={self.id}, watermark='{self.watermark}')>"


class Migration(Base):
    """
    Schema migration tracking table.
    """
    __tablename__ = "migrations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    applied_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Migration(version='{self.version}', name='{self.name}')>"


# ============================================================================
# Database Engine and Session Management
# ============================================================================

# Global engine instance
_engine = None
_SessionFactory = None


def get_engine():
    """
    Get or create the database engine.

    Returns:
        sqlalchemy.engine.Engine: Database engine instance
    """
    global _engine

    if _engine is None:
        engine_args = settings.get_db_engine_args()

        # Special handling for SQLite in-memory or testing
        if settings.DATABASE_URL == "sqlite:///:memory:":
            engine_args["poolclass"] = StaticPool

        _engine = create_engine(settings.DATABASE_URL, **engine_args)

        # SQLite-specific optimizations
        if settings.is_sqlite:
            @event.listens_for(_engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        logger.info(f"Database engine created: {settings.DATABASE_URL[:50]}...")

    return _engine


def get_session_factory() -> sessionmaker:
    """
    Get or create the session factory.

    Returns:
        sessionmaker: Session factory
    """
    global _SessionFactory

    if _SessionFactory is None:
        engine = get_engine()
        _SessionFactory = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    return _SessionFactory


def get_db() -> Generator[Session, None, None]:
    """
    Get database session as a generator (for FastAPI dependency injection).

    Yields:
        Session: Database session

    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Get database session as a context manager.

    Yields:
        Session: Database session

    Usage:
        with get_db_session() as db:
            protocols = db.query(Protocol).all()
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize the database by creating all tables.

    Note: This uses SQLAlchemy's create_all which is idempotent.
    For production, consider using Alembic migrations.
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def drop_db() -> None:
    """
    Drop all database tables. USE WITH CAUTION.
    """
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped")


def reset_db() -> None:
    """
    Reset database by dropping and recreating all tables.
    """
    drop_db()
    init_db()
    logger.info("Database reset complete")


# ============================================================================
# Migration System
# ============================================================================

MIGRATIONS = [
    {
        "version": "001",
        "name": "initial_schema",
        "up": None,  # Handled by init_db()
    },
    {
        "version": "002",
        "name": "add_certificate_hash",
        "up": "ALTER TABLE certificates ADD COLUMN certificate_hash VARCHAR(64)",
    },
    {
        "version": "003",
        "name": "add_watermarks_table",
        "up": None,  # Already in schema
    },
]


def get_applied_migrations(session: Session) -> List[str]:
    """Get list of applied migration versions."""
    try:
        migrations = session.query(Migration.version).all()
        return [m[0] for m in migrations]
    except Exception:
        return []


def apply_migrations(session: Session) -> List[str]:
    """
    Apply pending migrations.

    Returns:
        List[str]: List of applied migration versions
    """
    applied = get_applied_migrations(session)
    newly_applied = []

    for migration in MIGRATIONS:
        if migration["version"] not in applied:
            try:
                if migration["up"]:
                    session.execute(migration["up"])

                # Record migration
                session.add(Migration(
                    version=migration["version"],
                    name=migration["name"]
                ))
                session.commit()

                newly_applied.append(migration["version"])
                logger.info(f"Applied migration: {migration['version']} - {migration['name']}")

            except Exception as e:
                session.rollback()
                logger.error(f"Migration {migration['version']} failed: {e}")
                raise

    return newly_applied


# ============================================================================
# Repository Classes (Data Access Layer)
# ============================================================================

class ProtocolRepository:
    """Repository for Protocol CRUD operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        short_id: str,
        name: str,
        blockchain_hash: str,
        watermark: str,
        creator_id: int,
        **kwargs
    ) -> Protocol:
        """Create a new protocol."""
        protocol = Protocol(
            short_id=short_id,
            name=name,
            blockchain_hash=blockchain_hash,
            watermark=watermark,
            **kwargs
        )
        self.session.add(protocol)
        self.session.flush()

        # Add owner relationship
        protocol_creator = ProtocolCreator(
            protocol_id=protocol.id,
            creator_id=creator_id,
            role=CreatorRole.OWNER
        )
        self.session.add(protocol_creator)
        self.session.commit()

        return protocol

    def get_by_id(self, protocol_id: int) -> Optional[Protocol]:
        """Get protocol by internal ID."""
        return self.session.query(Protocol).filter(Protocol.id == protocol_id).first()

    def get_by_short_id(self, short_id: str) -> Optional[Protocol]:
        """Get protocol by short ID."""
        return self.session.query(Protocol).filter(Protocol.short_id == short_id).first()

    def get_by_hash(self, blockchain_hash: str) -> Optional[Protocol]:
        """Get protocol by blockchain hash."""
        return self.session.query(Protocol).filter(
            Protocol.blockchain_hash == blockchain_hash
        ).first()

    def get_by_watermark(self, watermark: str) -> Optional[Protocol]:
        """Get protocol by watermark."""
        return self.session.query(Protocol).filter(Protocol.watermark == watermark).first()

    def search_by_tags(self, tags: List[str]) -> List[Protocol]:
        """Search protocols by tags (any match)."""
        # For SQLite, use JSON contains
        if settings.is_sqlite:
            results = []
            for protocol in self.session.query(Protocol).all():
                if protocol.tags and any(tag in protocol.tags for tag in tags):
                    results.append(protocol)
            return results
        else:
            # PostgreSQL with JSONB
            from sqlalchemy import cast, func
            from sqlalchemy.dialects.postgresql import ARRAY, TEXT
            return self.session.query(Protocol).filter(
                Protocol.tags.op("?|")(cast(tags, ARRAY(TEXT)))
            ).all()

    def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        type_filter: Optional[ProtocolType] = None
    ) -> List[Protocol]:
        """List all protocols with pagination."""
        query = self.session.query(Protocol)

        if type_filter:
            query = query.filter(Protocol.type == type_filter)

        return query.order_by(Protocol.created_at.desc()).offset(skip).limit(limit).all()

    def increment_invocations(self, protocol_id: int) -> None:
        """Increment invocation count."""
        self.session.query(Protocol).filter(Protocol.id == protocol_id).update(
            {Protocol.invocation_count: Protocol.invocation_count + 1}
        )
        self.session.commit()

    def delete(self, protocol_id: int) -> bool:
        """Delete a protocol."""
        protocol = self.get_by_id(protocol_id)
        if protocol:
            self.session.delete(protocol)
            self.session.commit()
            return True
        return False


class CreatorRepository:
    """Repository for Creator CRUD operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, name: str, email: Optional[str] = None, **kwargs) -> Creator:
        """Create a new creator."""
        creator = Creator(name=name, email=email, **kwargs)
        self.session.add(creator)
        self.session.commit()
        return creator

    def get_by_id(self, creator_id: int) -> Optional[Creator]:
        """Get creator by ID."""
        return self.session.query(Creator).filter(Creator.id == creator_id).first()

    def get_by_email(self, email: str) -> Optional[Creator]:
        """Get creator by email."""
        return self.session.query(Creator).filter(Creator.email == email).first()

    def get_by_name(self, name: str) -> Optional[Creator]:
        """Get creator by name."""
        return self.session.query(Creator).filter(Creator.name == name).first()

    def get_or_create(
        self,
        name: str,
        email: Optional[str] = None,
        company: Optional[str] = None
    ) -> Creator:
        """Get existing creator or create new one."""
        creator = None

        if email:
            creator = self.get_by_email(email)

        if not creator:
            creator = self.get_by_name(name)

        if not creator:
            creator = self.create(name=name, email=email, company=company)

        return creator

    def list_all(self, skip: int = 0, limit: int = 100) -> List[Creator]:
        """List all creators with pagination."""
        return self.session.query(Creator).offset(skip).limit(limit).all()


class InvocationRepository:
    """Repository for Invocation operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        protocol_id: int,
        user_id: Optional[str] = None,
        telemetry: Optional[Dict] = None,
        **kwargs
    ) -> Invocation:
        """Record a new invocation."""
        invocation = Invocation(
            protocol_id=protocol_id,
            user_id=user_id,
            telemetry=telemetry or {},
            **kwargs
        )
        self.session.add(invocation)
        self.session.commit()
        return invocation

    def get_by_protocol(
        self,
        protocol_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Invocation]:
        """Get invocations for a protocol."""
        return self.session.query(Invocation).filter(
            Invocation.protocol_id == protocol_id
        ).order_by(Invocation.created_at.desc()).offset(skip).limit(limit).all()

    def count_by_protocol(self, protocol_id: int) -> int:
        """Count invocations for a protocol."""
        return self.session.query(Invocation).filter(
            Invocation.protocol_id == protocol_id
        ).count()


class CertificateRepository:
    """Repository for Certificate operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        protocol_id: int,
        certificate_id: str,
        certificate_html: str,
        document_text: Optional[str] = None,
        certificate_hash: Optional[str] = None
    ) -> Certificate:
        """Create a new certificate."""
        certificate = Certificate(
            protocol_id=protocol_id,
            certificate_id=certificate_id,
            certificate_html=certificate_html,
            document_text=document_text,
            certificate_hash=certificate_hash
        )
        self.session.add(certificate)
        self.session.commit()
        return certificate

    def get_by_id(self, certificate_id: str) -> Optional[Certificate]:
        """Get certificate by certificate ID."""
        return self.session.query(Certificate).filter(
            Certificate.certificate_id == certificate_id
        ).first()

    def get_by_protocol(self, protocol_id: int) -> List[Certificate]:
        """Get all certificates for a protocol."""
        return self.session.query(Certificate).filter(
            Certificate.protocol_id == protocol_id
        ).all()
