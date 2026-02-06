from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import relationship
import datetime
from sqlalchemy.orm.attributes import flag_modified
import logging


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    password_hash = db.Column(db.String(150))
    creation_date = db.Column(db.DateTime(timezone=True), default=func.now())


class VP_NONCE(db.Model):
    nonce = db.Column(db.String(255), primary_key=True)
    iat = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow())
    used = db.Column(db.Boolean, nullable=False, default=False)

    def mark_used(self):
        self.used = True
        self.used_at = datetime.datetime.utcnow()


class VC_Offer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False)
    issuer_state = db.Column(db.String(36), nullable=False)
    pre_authorized_code = db.Column(db.String(64), nullable=False)
    credential_data = db.Column(JSON, nullable=False)
    theme_data = db.Column(JSON, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())


class VC_Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    expires_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(hours=1),
    )


class VC_AuthorizationCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.String(255), nullable=False)
    code_challenge = db.Column(db.String(255), nullable=True)
    auth_code = db.Column(db.String(255), nullable=True)
    issuer_state = db.Column(db.String(255), nullable=True)
    # Add new fields for better session management
    used = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    used_at = db.Column(db.DateTime(timezone=True), nullable=True)
    expires_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(minutes=10),
    )

    def __str__(self) -> str:
        return f"{self.client_id} - {self.code_challenge} - {self.auth_code} - {self.issuer_state} - used:{self.used}"


class VC_validity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(255), nullable=False, unique=True, index=True)
    credential_data = db.Column(JSON, nullable=False)
    validity = db.Column(db.Boolean, nullable=False, default=True)

    # Enhanced metadata for better VC management
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(
        db.DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )
    revoked_at = db.Column(db.DateTime(timezone=True), nullable=True)
    issuer_did = db.Column(db.String(512), nullable=True)
    subject_did = db.Column(db.String(512), nullable=True)
    credential_type = db.Column(db.String(255), default="StudentIDCard")
    expiry_date = db.Column(db.DateTime(timezone=True), nullable=True)

    # Revocation details
    revocation_reason = db.Column(db.String(255), nullable=True)
    revoked_by = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<VC_validity {self.identifier} valid={self.validity}>"

    def revoke(self, reason=None, revoked_by=None):
        """Revoke this credential"""
        self.validity = False
        self.revoked_at = func.now()
        self.revocation_reason = reason
        self.revoked_by = revoked_by
        self.updated_at = func.now()

    def restore(self):
        """Restore this credential"""
        self.validity = True
        self.revoked_at = None
        self.revocation_reason = None
        self.revoked_by = None
        self.updated_at = func.now()

    def get_status_info(self):
        """Get comprehensive status information"""
        return {
            "identifier": self.identifier,
            "valid": self.validity,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "issuer_did": self.issuer_did,
            "subject_did": self.subject_did,
            "credential_type": self.credential_type,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "revocation_reason": self.revocation_reason,
            "revoked_by": self.revoked_by,
        }


class SystemSettings(db.Model):
    __tablename__ = "system_settings"

    id = db.Column(db.Integer, primary_key=True)

    # Settings categories stored as JSONB for flexibility
    disclosure_settings = db.Column(JSON, nullable=False, default=dict)
    network_settings = db.Column(JSON, nullable=False, default=dict)
    key_settings = db.Column(JSON, nullable=False, default=dict)
    trust_settings = db.Column(JSON, nullable=False, default=dict)
    appearance_settings = db.Column(JSON, nullable=False, default=dict)
    notification_settings = db.Column(JSON, nullable=False, default=dict)
    advanced_settings = db.Column(JSON, nullable=False, default=dict)

    # Metadata
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(
        db.DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )
    created_by = db.Column(db.String(255), nullable=True)
    updated_by = db.Column(db.String(255), nullable=True)
    version = db.Column(db.Integer, default=1)

    def __repr__(self):
        return "<SystemSettings>"

    @classmethod
    def get_or_create_default(cls):
        """Get system settings or create with default values"""
        settings = cls.query.first()

        if not settings:
            # Create default settings
            default_disclosure = {
                "firstName": True,
                "lastName": True,
                "email": False,
                "dateOfBirth": False,
                "studentId": True,
                "studentIdPrefix": True,
                "studyProgram": True,
                "issuanceCount": False,
                "profileImage": False,
                "themeName": False,
                "themeIcon": False,
                "bgColorCard": False,
                "fgColorTitle": False,
                "accentColor": False,
                "textColor": False,
                "issuanceDate": False,
                "expiryDate": False,
                "validFrom": False,
                "issuer": False,
                "credentialSchema": False,
            }

            default_network = {
                # Unified NGROK Configuration
                "ngrok_domain": "",  # Single unified NGROK domain (e.g., "your-instance.ngrok.io")
                "use_ngrok": False,  # Boolean flag to enable/disable NGROK
                # Default Address Configuration (used when NGROK is disabled)
                "default_ip": "192.168.178.122",  # Default IP for local access
                "default_port": "8080",  # Default port for local access
                # Legacy/Advanced Settings (maintained for compatibility)
                "use_https": True,  # Always use HTTPS for both NGROK and local
                "auto_discovery": False,  # Auto-discovery feature flag
                "timeout": 30,  # Connection timeout in seconds
            }

            default_keys = {
                "did_method": "did:web",
                "key_type": "Ed25519",
                "auto_rotate": False,
                "rotation_interval_days": 90,
                "x509_cert_path": None,
            }

            default_trust = {
                "trusted_issuers": [],
                "trusted_verifiers": [],
                "strict_mode": True,
                "auto_trust_verified": False,
                "log_untrusted": True,
            }

            default_appearance = {
                "theme": "light",
                "primaryColor": "#18206c",
                "accentColor": "#304a9f",
                "logoUrl": "",
                "customCss": "",
                "displayDensity": "compact",
                "language": "de",
            }

            default_notifications = {
                "emailNotifications": True,
                "credentialExpiry": True,
                "keyRotation": True,
                "securityAlerts": True,
                "digestFrequency": "weekly",
                "webhookUrl": "",
            }

            default_advanced = {
                "autoBackup": True,
                "backupFrequency": "daily",
                "maxBackups": 10,
                "apiAccess": False,
                "debugMode": False,
                "sessionTimeout": 30,
                "ipRestrictions": [],
            }

            settings = cls(
                disclosure_settings=default_disclosure,
                network_settings=default_network,
                key_settings=default_keys,
                trust_settings=default_trust,
                appearance_settings=default_appearance,
                notification_settings=default_notifications,
                advanced_settings=default_advanced,
            )

            db.session.add(settings)
            db.session.commit()

        return settings

    def update_settings(self, category, data, updated_by=None):
        """Update a specific category of settings"""
        if category == "disclosure":
            self.disclosure_settings.update(data)
            flag_modified(self, "disclosure_settings")
        elif category == "network":
            self.network_settings.update(data)
            flag_modified(self, "network_settings")
        elif category == "keys":
            self.key_settings.update(data)
            flag_modified(self, "key_settings")
        elif category == "trust":
            self.trust_settings.update(data)
            flag_modified(self, "trust_settings")
        elif category == "appearance":
            self.appearance_settings.update(data)
            flag_modified(self, "appearance_settings")
        elif category == "notifications":
            self.notification_settings.update(data)
            flag_modified(self, "notification_settings")
        elif category == "advanced":
            self.advanced_settings.update(data)
            flag_modified(self, "advanced_settings")
        else:
            raise ValueError(f"Unknown settings category: {category}")

        self.updated_by = updated_by
        self.version += 1
        self.updated_at = func.now()

        # Commit the changes to database
        db.session.commit()

        # Log the successful update
        logging.info(
            f"Settings updated successfully - Category: {category}, Updated by: {updated_by}"
        )
        logging.info(
            f"New {category} settings: {getattr(self, f'{category}_settings')}"
        )

    def get_all_settings(self):
        """Get all settings as a combined dict"""
        return {
            "disclosure": self.disclosure_settings,
            "network": self.network_settings,
            "keys": self.key_settings,
            "trust": self.trust_settings,
            "appearance": self.appearance_settings,
            "notifications": self.notification_settings,
            "advanced": self.advanced_settings,
            "_meta": {
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None,
                "created_by": self.created_by,
                "updated_by": self.updated_by,
                "version": self.version,
            },
        }


class SystemSettingsBackup(db.Model):
    __tablename__ = "system_settings_backup"

    id = db.Column(db.Integer, primary_key=True)
    backup_data = db.Column(JSON, nullable=False)
    backup_type = db.Column(
        db.String(50), default="manual"
    )  # manual, automatic, pre_update
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    created_by = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<SystemSettingsBackup {self.created_at}>"


class AuditLog(db.Model):
    """
    Audit-Log für alle Änderungen an kritischen Systemen und Daten
    """

    __tablename__ = "audit_log"

    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(255), nullable=False, index=True)
    timestamp = db.Column(db.DateTime(timezone=True), default=func.now(), index=True)

    # Was wurde getan?
    action = db.Column(
        db.String(50), nullable=False
    )  # create, update, delete, view, login, etc.

    # An welchem Ressourcetyp?
    resource_type = db.Column(
        db.String(50), nullable=False, index=True
    )  # settings, user, credential, etc.
    resource_category = db.Column(
        db.String(50), nullable=True
    )  # Unterkategorie, z.B. "keys" innerhalb "settings"
    resource_id = db.Column(
        db.String(255), nullable=True
    )  # Spezifische ID, falls vorhanden

    # Details der Änderung
    prev_value = db.Column(db.Text, nullable=True)  # Vorheriger Wert (JSON oder Text)
    new_value = db.Column(db.Text, nullable=True)  # Neuer Wert (JSON oder Text)

    # Weitere Metadaten
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    request_id = db.Column(
        db.String(36), nullable=True
    )  # UUID für Korrelation mehrerer Logs

    def __repr__(self):
        return f"<AuditLog {self.action}:{self.resource_type}>"

    @classmethod
    def log(
        cls,
        user_email,
        action,
        resource_type,
        resource_category=None,
        resource_id=None,
        prev_value=None,
        new_value=None,
        ip_address=None,
        user_agent=None,
        request_id=None,
    ):
        """
        Schreibt einen neuen Audit-Log-Eintrag.

        Args:
            user_email: Email des Benutzers
            action: Art der Aktion (create, update, delete, view, etc.)
            resource_type: Art der betroffenen Ressource
            resource_category: Optional: Unterkategorie
            resource_id: Optional: Spezifische Ressourcen-ID
            prev_value: Optional: Vorheriger Wert
            new_value: Optional: Neuer Wert
        """
        try:
            log_entry = cls(
                user_email=user_email,
                action=action,
                resource_type=resource_type,
                resource_category=resource_category,
                resource_id=resource_id,
                prev_value=prev_value,
                new_value=new_value,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
            )
            db.session.add(log_entry)
            db.session.commit()
            logging.info(f"Audit log created: {action}:{resource_type}")
        except Exception as e:
            logging.error(f"Failed to create audit log: {e}")
            db.session.rollback()


class APIKey(db.Model):
    """
    API Keys for external university system integration
    Secure storage with usage tracking
    """

    __tablename__ = "api_keys"

    id = db.Column(db.Integer, primary_key=True)

    # Key identification
    key_id = db.Column(
        db.String(36), unique=True, nullable=False, index=True
    )  # UUID for external reference
    key_hash = db.Column(
        db.String(255), nullable=False, unique=True
    )  # Hashed API key for security
    key_prefix = db.Column(
        db.String(16), nullable=False
    )  # First 8 chars for display (masked)

    # Key metadata
    name = db.Column(
        db.String(255), nullable=False
    )  # Human-readable name (e.g., "HISinOne Integration")
    description = db.Column(db.Text, nullable=True)  # Description of usage

    # Permissions and scope
    scopes = db.Column(JSON, nullable=False, default=list)  # List of allowed operations
    allowed_ips = db.Column(JSON, nullable=True)  # Optional IP whitelist
    rate_limit_per_hour = db.Column(db.Integer, default=1000)  # Rate limiting

    # Status and lifecycle
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(
        db.DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )
    expires_at = db.Column(
        db.DateTime(timezone=True), nullable=True
    )  # Optional expiration
    last_used_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Usage tracking
    usage_count = db.Column(db.Integer, default=0)
    usage_count_today = db.Column(db.Integer, default=0)
    usage_last_reset = db.Column(db.DateTime(timezone=True), default=func.now())

    # Audit trail
    created_by = db.Column(db.String(255), nullable=False)
    revoked_by = db.Column(db.String(255), nullable=True)
    revoked_at = db.Column(db.DateTime(timezone=True), nullable=True)
    revocation_reason = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<APIKey {self.key_prefix}... ({self.name})>"

    @classmethod
    def generate_new_key(
        cls,
        name,
        description,
        scopes,
        created_by,
        expires_days=None,
        rate_limit_per_hour=1000,
        allowed_ips=None,
    ):
        """
        Generate a new API key with secure random generation
        """
        import secrets
        import hashlib
        import uuid
        from datetime import datetime, timedelta

        # Generate secure random API key
        raw_key = f"stvc_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:12]  # Show first 12 chars for identification
        key_id = str(uuid.uuid4())

        # Calculate expiration
        expires_at = None
        if expires_days:
            expires_at = datetime.now() + timedelta(days=expires_days)

        # Create API key record
        api_key = cls(
            key_id=key_id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=name,
            description=description,
            scopes=scopes if scopes else [],
            allowed_ips=allowed_ips if allowed_ips else [],
            rate_limit_per_hour=rate_limit_per_hour,
            expires_at=expires_at,
            created_by=created_by,
        )

        db.session.add(api_key)
        db.session.commit()

        # Log the creation for audit
        AuditLog.log(
            user_email=created_by,
            action="create",
            resource_type="api_key",
            resource_id=key_id,
            new_value=f"Created API key: {name}",
        )

        return (
            api_key,
            raw_key,
        )  # Return both record and raw key (only time raw key is available)

    @classmethod
    def verify_key(cls, raw_key):
        """
        Verify an API key and return the associated record if valid
        """
        import hashlib

        if not raw_key:
            return None

        # Accept both stvc_ and sk_live_ prefixes
        if not (raw_key.startswith("stvc_") or raw_key.startswith("sk_live_")):
            return None

        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = cls.query.filter_by(key_hash=key_hash, is_active=True).first()

        if api_key:
            # Check expiration
            if api_key.expires_at and api_key.expires_at < datetime.datetime.now():
                return None

            # Update usage tracking
            api_key.usage_count += 1
            api_key.usage_count_today += 1
            api_key.last_used_at = func.now()

            # Reset daily counter if needed
            if api_key.usage_last_reset.date() < datetime.datetime.now().date():
                api_key.usage_count_today = 1
                api_key.usage_last_reset = func.now()

            db.session.commit()

        return api_key

    def revoke(self, revoked_by, reason=None):
        """
        Revoke this API key
        """
        self.is_active = False
        self.revoked_by = revoked_by
        self.revoked_at = func.now()
        self.revocation_reason = reason
        self.updated_at = func.now()

        # Log the revocation
        AuditLog.log(
            user_email=revoked_by,
            action="revoke",
            resource_type="api_key",
            resource_id=self.key_id,
            new_value=f"Revoked API key: {self.name} - Reason: {reason}",
        )

        db.session.commit()

    def has_scope(self, required_scope):
        """
        Check if this API key has the required scope
        """
        return required_scope in self.scopes or "admin" in self.scopes

    def check_rate_limit(self):
        """
        Check if this API key has exceeded its rate limit
        """
        return self.usage_count_today < self.rate_limit_per_hour

    def get_safe_info(self):
        """
        Get safe information about this API key (no sensitive data)
        """
        return {
            "key_id": self.key_id,
            "key_prefix": self.key_prefix + "...",
            "name": self.name,
            "description": self.description,
            "scopes": self.scopes,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used_at": self.last_used_at.isoformat()
            if self.last_used_at
            else None,
            "usage_count": self.usage_count,
            "usage_count_today": self.usage_count_today,
            "rate_limit_per_hour": self.rate_limit_per_hour,
            "created_by": self.created_by,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "revocation_reason": self.revocation_reason,
        }


class KeyRegistry(db.Model):
    """
    Registry for all cryptographic keys used in the system.
    Maintains history of public keys for verification continuity.
    """

    __tablename__ = "key_registry"

    id = db.Column(db.Integer, primary_key=True)

    # Key identification and type
    key_type = db.Column(
        db.String(50), nullable=False, index=True
    )  # 'bbs_issuer', 'jwt_signing', 'domain_cert'
    key_fingerprint = db.Column(
        db.String(128), unique=True, nullable=False, index=True
    )  # SHA256 fingerprint
    key_identifier = db.Column(
        db.String(255), nullable=True
    )  # DID, KID, or certificate CN

    # Key data
    public_key_data = db.Column(
        db.Text, nullable=False
    )  # PEM or base64 encoded public key
    private_key_path = db.Column(
        db.String(512), nullable=True
    )  # Path to private key file (for active keys)
    algorithm = db.Column(
        db.String(50), nullable=False
    )  # 'BBS+', 'ES256', 'RSA2048', etc.

    # Lifecycle status
    status = db.Column(
        db.String(20), nullable=False, default="active", index=True
    )  # 'active', 'retired', 'revoked', 'expired'
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    activated_at = db.Column(db.DateTime(timezone=True), nullable=True)
    deactivated_at = db.Column(db.DateTime(timezone=True), nullable=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Usage tracking
    usage_count = db.Column(db.Integer, default=0)
    last_used_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Additional metadata (DID, KID, certificate info, etc.)
    key_metadata = db.Column(JSON, nullable=False, default=dict)

    # Audit trail
    created_by = db.Column(db.String(255), nullable=True)
    deactivated_by = db.Column(db.String(255), nullable=True)
    deactivation_reason = db.Column(db.String(255), nullable=True)

    # Relationships for key rotation history
    parent_key_id = db.Column(db.Integer, ForeignKey("key_registry.id"), nullable=True)
    parent_key = relationship("KeyRegistry", remote_side=[id], backref="child_keys")

    def __repr__(self):
        return f"<KeyRegistry {self.key_type}:{self.key_fingerprint[:12]}... status={self.status}>"

    @classmethod
    def get_active_key(cls, key_type):
        """Get the currently active key for a specific type"""
        return cls.query.filter_by(key_type=key_type, status="active").first()

    @classmethod
    def get_key_history(cls, key_type):
        """Get all keys for a specific type (active and historical)"""
        return (
            cls.query.filter_by(key_type=key_type).order_by(cls.created_at.desc()).all()
        )

    @classmethod
    def get_public_keys_for_verification(cls, key_type):
        """Get all public keys that can be used for verification (active + retired)"""
        return (
            cls.query.filter(
                cls.key_type == key_type, cls.status.in_(["active", "retired"])
            )
            .order_by(cls.created_at.desc())
            .all()
        )

    def activate(self, activated_by=None):
        """Activate this key and deactivate others of the same type"""
        # Deactivate other active keys of the same type
        active_keys = KeyRegistry.query.filter_by(
            key_type=self.key_type, status="active"
        ).all()

        for key in active_keys:
            key.deactivate(activated_by, "Replaced by new key")

        # Activate this key
        self.status = "active"
        self.activated_at = func.now()
        if activated_by:
            self.key_metadata = self.key_metadata or {}
            self.key_metadata["activated_by"] = activated_by

        db.session.commit()
        return True

    def deactivate(self, deactivated_by=None, reason=None):
        """Deactivate this key (retire it for verification purposes)"""
        self.status = "retired"
        self.deactivated_at = func.now()
        self.deactivated_by = deactivated_by
        self.deactivation_reason = reason
        return True

    def revoke(self, revoked_by=None, reason=None):
        """Revoke this key (completely invalidate it)"""
        self.status = "revoked"
        self.deactivated_at = func.now()
        self.deactivated_by = revoked_by
        self.deactivation_reason = reason
        return True

    def increment_usage(self):
        """Increment usage counter"""
        self.usage_count += 1
        self.last_used_at = func.now()
        flag_modified(self, "usage_count")
        flag_modified(self, "last_used_at")

    def get_status_info(self):
        """Get comprehensive status information"""
        return {
            "id": self.id,
            "key_type": self.key_type,
            "key_fingerprint": self.key_fingerprint,
            "key_identifier": self.key_identifier,
            "algorithm": self.algorithm,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "activated_at": self.activated_at.isoformat()
            if self.activated_at
            else None,
            "deactivated_at": self.deactivated_at.isoformat()
            if self.deactivated_at
            else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "usage_count": self.usage_count,
            "last_used_at": self.last_used_at.isoformat()
            if self.last_used_at
            else None,
            "key_metadata": self.key_metadata,
            "created_by": self.created_by,
            "deactivated_by": self.deactivated_by,
            "deactivation_reason": self.deactivation_reason,
            "has_parent": self.parent_key_id is not None,
            "child_count": len(self.child_keys) if self.child_keys else 0,
        }
