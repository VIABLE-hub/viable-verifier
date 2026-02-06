from . import db
from sqlalchemy.sql import func
from sqlalchemy import JSON
from sqlalchemy.orm.attributes import flag_modified
import logging


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


class VP_NONCE(db.Model):
    __tablename__ = "vp_nonce"

    id = db.Column(db.Integer, primary_key=True)
    nonce = db.Column(db.String(255), nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())

    def mark_used(self):
        self.used = True

    def __repr__(self):
        return f"<VP_NONCE {self.nonce}>"
