"""
Key Management Service for StudentVC
Handles cryptographic key lifecycle, rotation, and registry management.
"""

import os
import hashlib
import logging
import base64
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from flask import current_app

from .. import db
from ..models import KeyRegistry, SystemSettings, AuditLog

# Import existing key generation modules
from ..issuer.key_generator import load_or_generate_keys, load_or_generate_bbs_keys, generate_did, generate_kid

logger = logging.getLogger(__name__)


class KeyManagementService:
    """Central service for all key management operations"""
    
    def __init__(self):


    
    def get_key_fingerprint(self, key_data: str) -> str:
        """Generate SHA256 fingerprint for a key"""
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def register_existing_keys(self) -> Dict[str, bool]:
        """Register currently existing keys from filesystem into the registry"""
        results = {"bbs_issuer": False, "jwt_signing": False}
        
        try:
            # Register BBS+ keys
            bbs_secret, bbs_dpk = load_or_generate_bbs_keys()
            if bbs_secret and bbs_dpk:
                bbs_public_b64 = base64.b64encode(bbs_dpk).decode('utf-8')
                fingerprint = self.get_key_fingerprint(bbs_public_b64)
                
                # Check if already registered
                existing = KeyRegistry.query.filter_by(
                    
                    key_fingerprint=fingerprint
                ).first()
                
                if not existing:
                    bbs_key = KeyRegistry(
                        
                        key_type='bbs_issuer',
                        key_fingerprint=fingerprint,
                        key_identifier='bbs-issuer-key',
                        public_key_data=bbs_public_b64,
                        private_key_path=os.path.join(current_app.config['INSTANCE_FOLDER_PATH'], 'bbs_private.pem'),
                        algorithm='BBS+',
                        status='active',
                        activated_at=datetime.utcnow(),
                        metadata={
                            'source': 'existing_filesystem',
                            'dpk_length': len(bbs_dpk),
                            'secret_length': len(bbs_secret)
                        }
                    )
                    db.session.add(bbs_key)
                    results["bbs_issuer"] = True
                    logger.info(f"Registered existing BBS+ key with fingerprint: {fingerprint[:16]}...")
                else:
                    logger.info("BBS+ key already registered")
                    results["bbs_issuer"] = True
            
            # Register JWT signing keys
            jwt_private, jwt_public = load_or_generate_keys()
            if jwt_private and jwt_public:
                fingerprint = self.get_key_fingerprint(jwt_public)
                
                # Check if already registered
                existing = KeyRegistry.query.filter_by(
                    
                    key_fingerprint=fingerprint
                ).first()
                
                if not existing:
                    # Generate DID and KID
                    issuer_did = generate_did(jwt_public)
                    issuer_kid = generate_kid(issuer_did)
                    
                    jwt_key = KeyRegistry(
                        
                        key_type='jwt_signing',
                        key_fingerprint=fingerprint,
                        key_identifier=issuer_did,
                        public_key_data=jwt_public,
                        private_key_path=os.path.join(current_app.config['INSTANCE_FOLDER_PATH'], 'private.pem'),
                        algorithm='ES256',
                        status='active',
                        activated_at=datetime.utcnow(),
                        metadata={
                            'source': 'existing_filesystem',
                            'did': issuer_did,
                            'kid': issuer_kid,
                            'curve': 'SECP256R1'
                        }
                    )
                    db.session.add(jwt_key)
                    results["jwt_signing"] = True
                    logger.info(f"Registered existing JWT key with fingerprint: {fingerprint[:16]}...")
                else:
                    logger.info("JWT signing key already registered")
                    results["jwt_signing"] = True
            
            db.session.commit()
            return results
            
        except Exception as e:
            logger.error(f"Error registering existing keys: {e}")
            db.session.rollback()
            return results
    
    def get_keys_overview(self) -> Dict:
        """Get comprehensive overview of all keys"""
        try:
            # Ensure existing keys are registered
            self.register_existing_keys()
            
            overview = {
                "bbs_issuer": self._get_key_type_info("bbs_issuer"),
                "jwt_signing": self._get_key_type_info("jwt_signing"),
                "domain_cert": self._get_key_type_info("domain_cert"),
                "verification_registry": self._get_verification_registry_info(),
                "summary": self._get_summary_stats()
            }
            
            return overview
            
        except Exception as e:
            logger.error(f"Error getting keys overview: {e}")
            return {"error": str(e)}
    
    def _get_key_type_info(self, key_type: str) -> Dict:
        """Get detailed information for a specific key type"""
        active_key = KeyRegistry.get_active_key(key_type)
        key_history = KeyRegistry.get_key_history(key_type)
        
        if not active_key and key_type in ["bbs_issuer", "jwt_signing"]:
            # Try to register existing keys if no active key found
            self.register_existing_keys()
            active_key = KeyRegistry.get_active_key(key_type)
        
        info = {
            "active_key": active_key.get_status_info() if active_key else None,
            "key_count": len(key_history),
            "history": [key.get_status_info() for key in key_history[:5]],  # Last 5 keys
            "verification_keys_count": len([k for k in key_history if k.status in ['active', 'retired']]),
            "last_rotation": key_history[1].created_at.isoformat() if len(key_history) > 1 else None,
            "next_rotation": self._calculate_next_rotation(active_key) if active_key else None
        }
        
        return info
    
    def _get_verification_registry_info(self) -> Dict:
        """Get information about verification registry"""
        all_verification_keys = KeyRegistry.query.filter(
            
            KeyRegistry.status.in_(['active', 'retired'])
        ).all()
        
        return {
            "total_trusted_keys": len(all_verification_keys),
            "bbs_keys": len([k for k in all_verification_keys if k.key_type == 'bbs_issuer']),
            "jwt_keys": len([k for k in all_verification_keys if k.key_type == 'jwt_signing']),
            "domain_keys": len([k for k in all_verification_keys if k.key_type == 'domain_cert']),
            "last_verification": max([k.last_used_at for k in all_verification_keys if k.last_used_at], default=None)
        }
    
    def _get_summary_stats(self) -> Dict:
        """Get summary statistics"""
        all_keys = KeyRegistry.query.filter_by().all()
        
        return {
            "total_keys": len(all_keys),
            "active_keys": len([k for k in all_keys if k.status == 'active']),
            "retired_keys": len([k for k in all_keys if k.status == 'retired']),
            "revoked_keys": len([k for k in all_keys if k.status == 'revoked']),
            "total_usage": sum([k.usage_count for k in all_keys]),
            "last_activity": max([k.last_used_at for k in all_keys if k.last_used_at], default=None)
        }
    
    def _calculate_next_rotation(self, key: KeyRegistry) -> Optional[str]:
        """Calculate next rotation date based on settings"""
        try:
            settings = SystemSettings.get_or_create_default()
            key_settings = settings.key_settings or {}
            
            if key_settings.get('auto_rotate', False):
                rotation_days = key_settings.get('rotation_interval_days', 90)
                next_rotation = key.created_at + timedelta(days=rotation_days)
                return next_rotation.isoformat()
            
            return None
        except Exception:
            return None
    
    def rotate_key(self, key_type: str, rotated_by: str = "system") -> Dict:
        """Rotate a key safely with verification continuity"""
        try:
            logger.info(f"Starting key rotation for type: {key_type}")
            
            # Get current active key
            current_key = KeyRegistry.get_active_key(key_type)
            
            if key_type == "bbs_issuer":
                return self._rotate_bbs_key(current_key, rotated_by)
            elif key_type == "jwt_signing":
                return self._rotate_jwt_key(current_key, rotated_by)
            elif key_type == "domain_cert":
                return self._rotate_domain_cert(current_key, rotated_by)
            else:
                return {"success": False, "message": f"Unsupported key type: {key_type}"}
                
        except Exception as e:
            logger.error(f"Error rotating key {key_type}: {e}")
            return {"success": False, "message": str(e)}
    
    def _rotate_bbs_key(self, current_key: Optional[KeyRegistry], rotated_by: str) -> Dict:
        """Rotate BBS+ issuer key"""
        try:
            # Generate new BBS+ key pair
            from ..issuer.key_generator import generate_bbs_keys
            new_secret, new_dpk = generate_bbs_keys()
            
            # Create new registry entry
            public_b64 = base64.b64encode(new_dpk).decode('utf-8')
            fingerprint = self.get_key_fingerprint(public_b64)
            
            new_key = KeyRegistry(
                
                key_type='bbs_issuer',
                key_fingerprint=fingerprint,
                key_identifier='bbs-issuer-key',
                public_key_data=public_b64,
                private_key_path=os.path.join(current_app.config['INSTANCE_FOLDER_PATH'], 'bbs_private.pem'),
                algorithm='BBS+',
                status='active',
                activated_at=datetime.utcnow(),
                created_by=rotated_by,
                parent_key_id=current_key.id if current_key else None,
                metadata={
                    'rotation_reason': 'manual_rotation',
                    'dpk_length': len(new_dpk),
                    'secret_length': len(new_secret)
                }
            )
            
            db.session.add(new_key)
            
            # Retire old key (keep for verification)
            if current_key:
                current_key.deactivate(rotated_by, "Replaced by key rotation")
            
            db.session.commit()
            
            # Log audit
            AuditLog.log(
                
                user_email=rotated_by,
                action='rotate',
                resource_type='key',
                resource_category='bbs_issuer',
                resource_id=new_key.key_fingerprint,
                new_value=f"Rotated BBS+ issuer key"
            )
            
            return {
                "success": True,
                "message": "BBS+ key rotated successfully",
                "new_key": new_key.get_status_info(),
                "previous_key": current_key.get_status_info() if current_key else None
            }
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def _rotate_jwt_key(self, current_key: Optional[KeyRegistry], rotated_by: str) -> Dict:
        """Rotate JWT signing key"""
        try:
            # Generate new JWT key pair
            from ..issuer.key_generator import generate_keys
            new_private, new_public = generate_keys()
            
            # Generate new DID and KID
            issuer_did = generate_did(new_public)
            issuer_kid = generate_kid(issuer_did)
            
            # Create new registry entry
            fingerprint = self.get_key_fingerprint(new_public)
            
            new_key = KeyRegistry(
                
                key_type='jwt_signing',
                key_fingerprint=fingerprint,
                key_identifier=issuer_did,
                public_key_data=new_public,
                private_key_path=os.path.join(current_app.config['INSTANCE_FOLDER_PATH'], 'private.pem'),
                algorithm='ES256',
                status='active',
                activated_at=datetime.utcnow(),
                created_by=rotated_by,
                parent_key_id=current_key.id if current_key else None,
                metadata={
                    'rotation_reason': 'manual_rotation',
                    'did': issuer_did,
                    'kid': issuer_kid,
                    'curve': 'SECP256R1'
                }
            )
            
            db.session.add(new_key)
            
            # Retire old key (keep for verification)
            if current_key:
                current_key.deactivate(rotated_by, "Replaced by key rotation")
            
            db.session.commit()
            
            # Log audit
            AuditLog.log(
                
                user_email=rotated_by,
                action='rotate',
                resource_type='key',
                resource_category='jwt_signing',
                resource_id=new_key.key_fingerprint,
                new_value=f"Rotated JWT signing key with DID: {issuer_did}"
            )
            
            return {
                "success": True,
                "message": "JWT signing key rotated successfully",
                "new_key": new_key.get_status_info(),
                "previous_key": current_key.get_status_info() if current_key else None
            }
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def _rotate_domain_cert(self, current_key: Optional[KeyRegistry], rotated_by: str) -> Dict:
        """Rotate domain certificate (placeholder for future implementation)"""
        return {
            "success": False,
            "message": "Domain certificate rotation not yet implemented"
        }
    
    def get_verification_registry(self) -> List[Dict]:
        """Get all public keys available for verification"""
        verification_keys = KeyRegistry.query.filter(
            
            KeyRegistry.status.in_(['active', 'retired'])
        ).order_by(KeyRegistry.created_at.desc()).all()
        
        return [key.get_status_info() for key in verification_keys]
    
    def increment_key_usage(self, key_type: str, key_fingerprint: Optional[str] = None):
        """Increment usage counter for a key"""
        try:
            if key_fingerprint:
                key = KeyRegistry.query.filter_by(
                    
                    key_fingerprint=key_fingerprint
                ).first()
            else:
                key = KeyRegistry.get_active_key(key_type)
            
            if key:
                key.increment_usage()
                db.session.commit()
                
        except Exception as e:
            logger.error(f"Error incrementing key usage: {e}")


class KeyRotationService:
    """Specialized service for key rotation operations"""
    
    def __init__(self):
        self.key_mgmt = KeyManagementService()
    
    def schedule_rotation(self, key_type: str, days_from_now: int) -> Dict:
        """Schedule a key rotation"""
        # This would integrate with a task scheduler like Celery
        # For now, just return a success message
        return {
            "success": True,
            "message": f"Key rotation scheduled for {key_type} in {days_from_now} days",
            "scheduled_date": (datetime.utcnow() + timedelta(days=days_from_now)).isoformat()
        }
    
    def emergency_rotation(self, reason: str, rotated_by: str) -> Dict:
        """Perform emergency rotation of all keys"""
        results = {}
        
        for key_type in ["bbs_issuer", "jwt_signing"]:
            try:
                result = self.key_mgmt.rotate_key(key_type, rotated_by)
                results[key_type] = result
                
                # Log emergency rotation
                AuditLog.log(
                    
                    user_email=rotated_by,
                    action='emergency_rotate',
                    resource_type='key',
                    resource_category=key_type,
                    new_value=f"Emergency rotation: {reason}"
                )
                
            except Exception as e:
                results[key_type] = {"success": False, "message": str(e)}
        
        return {
            "success": all(r.get("success", False) for r in results.values()),
            "results": results,
            "reason": reason
        }


# Global instances
key_management = KeyManagementService()
key_rotation = KeyRotationService() 