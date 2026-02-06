import os

class Config:
    # Branding
    UNIVERSITY_NAME = "Technische Universität Berlin"
    UNIVERSITY_SHORT_NAME = "TU Berlin"
    PRIMARY_COLOR = "#c50e1f"
    ACCENT_COLOR = "#c50e1f"
    TEXT_COLOR = "#FFFFFF"
    
    # Logos (now in static/img/)
    LOGO_FILENAME = "tub_logo.png"
    HOCHSCHUL_BRANDING_LOGO = "tub_logo_white_red.png"
    MAIN_LOGO_FILENAME = "studentVC-logo-sora-cropped.png"

    # Theme Colors
    THEME_COLORS = {
        'bgColorCard': 'c50e1f',
        'bgColorTop': 'c50e1f',
        'bgColorBot': 'FFFFFF',
        'fgColorTitle': 'FFFFFF',
        'accentColor': 'c50e1f',
        'textColor': 'FFFFFF'
    }

    # Credential Template
    CREDENTIAL_TEMPLATE = {
        "issuer": UNIVERSITY_NAME,
        "issuerDisplayName": UNIVERSITY_SHORT_NAME,
        "credentialSubject": {
            "credentialBranding": {
                "backgroundColor": "#FFFFFF",
                "textColor": "FFFFFF",
                "logo": HOCHSCHUL_BRANDING_LOGO,
                "vcLogo": HOCHSCHUL_BRANDING_LOGO,
                "bgColorCard": "c50e1f",
                "bgColorSectionTop": "c50e1f",
                "bgColorSectionBot": "FFFFFF",
                "fgColorTitle": "FFFFFF"
            }
        }
    }

    # Database
    INSTANCE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance')
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(INSTANCE_PATH, 'studentvc.sqlite')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
