"""
Verifier-Modul für die Überprüfung von Verifiable Credentials.

Dieses Modul ist in mehrere logische Teile untergliedert:
- routes.py: Flask-Routen und Endpunkte
- field_extractor.py: Funktionen zum Extrahieren von Feldern aus JWTs und VCs
- bbs_verification.py: Logik zur kryptografischen Verifizierung mit BBS+
- validators.py: Funktionen zur Validierung von Feldern und Daten
- utils.py: Hilfsfunktionen für QR-Codes, Zufallsstrings, usw.
- constants.py: Konstanten und Konfigurationen
- disclosure_validator.py: Validierung der selektiven Offenlegung

Die Hauptfunktionalität wird über den Blueprint 'verifier_bp' bereitgestellt.
"""

# Import the correct blueprint from routes.py
from .main_routes import verifier_bp as verifier

# Disable all other imports to prevent circular import issues
# These modules can be imported directly by other modules when needed

__all__ = [
    'verifier',
]
