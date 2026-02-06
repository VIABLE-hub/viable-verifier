"""
Konstanten und Definitionen für den Verifier.
TODO: Add FIELDS_EN and FIELDS_DE for german and english 
"""

# Presentation Definition - Technische Felder
TECHNICAL_FIELDS = [
    "iss", "sub", "exp", "nbf", "jti", "nonce", 
    "signed_nonce", "bbs_dpk", "total_messages", "validity_identifier"
]

# iOS kompatible camelCase Felder
TECHNICAL_FIELDS_CAMEL_CASE = [
    "iss", "sub", "exp", "nbf", "jti", "nonce", 
    "signedNonce", "bbsDPK", "totalMessages", "validityIdentifier"
]

# Feld-Mapping zwischen snake_case und camelCase
FIELD_MAPPINGS = {
    "total_messages": "totalMessages",
    "bbs_dpk": "bbsDPK",
    "signed_nonce": "signedNonce",
    "validity_identifier": "validityIdentifier"
}

# BBS+ Metadatenfelder - diese Felder werden aus dem Message-Vektor ausgeschlossen
BBS_METADATA_FIELDS = {
    'bbs_dpk', 'bbsDPK', 
    'total_messages', 'totalMessages', 
    'signed_nonce', 'signedNonce', 
    'validity_identifier', 'validityIdentifier'
}

# Feld-Erklärungen
FIELD_EXPLANATIONS = {
    # User data field explanations (frontend field names)
    "firstName": "Vorname des Karteninhabers",
    "lastName": "Nachname des Karteninhabers", 
    "studentId": "Eindeutige Studenten-Identifikationsnummer",
    "studentIdPrefix": "Präfix der Studenten-ID zur Organisationsidentifikation",
    "image": "Profilbild des Studenten (Base64-kodiert)",
    
    # User data field explanations (credential path field names)
    "vc.credentialSubject.firstName": "Vorname des Karteninhabers",
    "vc.credentialSubject.lastName": "Nachname des Karteninhabers", 
    "vc.credentialSubject.studentId": "Eindeutige Studenten-Identifikationsnummer",
    "vc.credentialSubject.studentIdPrefix": "Präfix der Studenten-ID zur Organisationsidentifikation",
    "vc.credentialSubject.image": "Profilbild des Studenten (Base64-kodiert)",
    
    # Technical field explanations
    "total_messages": "amount of messages in the whole credential. needed for BBS+ signature verification",
    "bbs_dpk": "BBS+ issuer public key, needed to check if credential was signed by a trusted issuer",
    "iss": "issuer DID, needed to check if credential was signed by a trusted issuer",
    "sub": "holder DID, needed to check if credential was signed by a trusted holder",
    "nonce": "prevents replay attacks, used to verify issuer signature",
    "signed_nonce": "signature of the nonce, used to verify issuer signature",
    "validity_identifier": "unique identifier of the credential, needed to check if credential is valid"
}

# Core Student Fields (selectable for disclosure)
SELECTABLE_USER_FIELDS = [
    "firstName", "lastName", "studentId", "studentIdPrefix"
]

# Visual Elements Fields (selectable for disclosure) 
SELECTABLE_VISUAL_FIELDS = [
    # "image",  # Disabled: Base64 image data too large for BBS+ verification
    # "theme"   # Disabled: Theme data can be complex and cause verification issues
]

# All Selectable Fields (for UI)
ALL_SELECTABLE_FIELDS = SELECTABLE_USER_FIELDS + SELECTABLE_VISUAL_FIELDS

# Extended Credential Fields (available but not typically selected)
EXTENDED_CREDENTIAL_FIELDS = [
    "email", "dateOfBirth", "studyProgram", "faculty",
    "enrollmentDate", "expectedGraduation", "studentStatus", "academicLevel",
    "profileImage", "themeName", "themeIcon", "bgColorCard",
    "fgColorTitle", "accentColor", "textColor",
    "issuanceDate", "expiryDate", "validFrom", "issuer", "credentialSchema", "issuanceCount"
]

# Alle möglichen Credential-Felder
ALL_CREDENTIAL_FIELDS = ALL_SELECTABLE_FIELDS + EXTENDED_CREDENTIAL_FIELDS
