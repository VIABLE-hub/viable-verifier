# Blueprint Structure Documentation

**Last Updated:** November 8, 2025  
**Total Blueprints:** 12 main + dynamic routes  
**Total Routes:** ~196 routes across 34 files  

---

## 📦 Blueprint Registration

All blueprints are registered in `backend/src/__init__.py` via the `register_blueprints()` function.

**Registration Order:**
1. Core blueprints (home, issuer, verifier)
2. Authentication blueprints (auth, vc_auth)
3. Validation blueprints (vcstatus, validate)
4. Settings blueprints (settings, api_settings)
5. Feature blueprints (api_integration, debug, usecases, monitoring)
6. Network API (dynamic registration)

---

## 🏗️ Blueprint Hierarchy

### Core Blueprints

| Blueprint | Prefix | File | Routes | Description |
|-----------|--------|------|--------|-------------|
| `home` | `/` | `home.py` | 1 | Landing page |
| `issuer` | `/` | `issuer/issuer.py` | 38 | Credential issuance |
| `verifier` | `/verifier` | `verifier/main_routes.py` | 28 | Credential verification |

**Nested Blueprints:**
- `verifier` contains:
  - `presentation_bp` (12 routes)
  - `verification_bp` (16 routes)

---

### Authentication Blueprints

| Blueprint | Prefix | File | Routes | Description |
|-----------|--------|------|--------|-------------|
| `auth` | `/` | `auth/__init__.py` | 3 | Flask-Login authentication |
| `vc_auth` | `/auth/vc-login` | `auth/vc_auth.py` | 5 | VC-based authentication |
| `session_auth` | `/` | `simple_auth.py` | 2 | Simple session auth (conditional) |

**Conditional Registration:**
- `session_auth` only registered if `ENABLE_AUTH=true`
- Otherwise, `auth` (Flask-Login) is used

---

### Validation Blueprints

| Blueprint | Prefix | File | Routes | Description |
|-----------|--------|------|--------|-------------|
| `vcstatus` | `/vcstatus` | `validate/vcstatus.py` | 18 | Credential status management |
| `validate_legacy` | `/validate` | `validate/validate.py` | 5 | Legacy validation routes |

---

### Settings Blueprints

| Blueprint | Prefix | File | Routes | Description |
|-----------|--------|------|--------|-------------|
| `settings` | `/` | `settings/__init__.py` | 15 | Settings UI |
| `api_settings` | `/` | `settings/api.py` | 27 | Settings API |

**Settings Sub-Modules:**
- `settings/core.py` - Core settings
- `settings/disclosure.py` - Selective disclosure
- `settings/keys.py` - Key management
- `settings/trust.py` - Trust settings
- `settings/network/` - Network configuration
- `settings/health/` - Health checks
- `settings/database/` - Database management


---

### Feature Blueprints

| Blueprint | Prefix | File | Routes | Description |
|-----------|--------|------|--------|-------------|
| `api_integration` | `/` | `api_integration.py` | 24 | External API integration |
| `debug` | `/debug` | `issuer/debug.py` | 8 | Debug tools |
| `usecases` | `/usecases` | `usecases/usecases.py` | 11 | Use case demonstrations |
| `monitoring` | `/` | `monitoring.py` | 10 | Health and metrics |

---

### Dynamic Routes

| Component | Prefix | File | Routes | Description |
|-----------|--------|------|--------|-------------|
| - | - | - | - | (None currently) |

**Note:** Network API is now integrated into the `settings` blueprint.

---

## 📊 Route Distribution

```
Total Routes: ~196

By Category:
- Settings:     42 routes (21.4%)
- Issuer:       38 routes (19.4%)
- Verifier:     28 routes (14.3%)
- API:          24 routes (12.2%)
- VCStatus:     18 routes (9.2%)
- Auth:         12 routes (6.1%)
- Monitoring:   10 routes (5.1%)
- Other:        24 routes (12.3%)
```

---

## 🔍 Blueprint Details

### Core Blueprints

#### `home` Blueprint
- **File:** `backend/src/home.py`
- **Prefix:** `/`
- **Routes:** 1
- **Purpose:** Landing page redirect

#### `issuer` Blueprint
- **File:** `backend/src/issuer/issuer.py`
- **Prefix:** `/`
- **Routes:** 38
- **Purpose:** Credential issuance
- **Key Routes:**
  - `/issuer` - Main issuer page
  - `/.well-known/openid-credential-issuer` - OID4VC metadata
  - `/issuer/credential-offer` - Credential offer endpoint

#### `verifier` Blueprint
- **File:** `backend/src/verifier/main_routes.py`
- **Prefix:** `/verifier`
- **Routes:** 28 (12 + 16 nested)
- **Purpose:** Credential verification
- **Nested:**
  - `presentation_bp` - Presentation request handling
  - `verification_bp` - Verification processing
- **Key Routes:**
  - `/verifier` - Main verifier page
  - `/verifier/presentation-request` - Presentation request

---

### Authentication Blueprints

#### `auth` Blueprint
- **File:** `backend/src/auth/__init__.py`
- **Prefix:** `/`
- **Routes:** 3
- **Purpose:** Flask-Login authentication
- **Key Routes:**
  - `/login` - Login page
  - `/logout` - Logout endpoint
  - `/register` - User registration (debug only)

#### `vc_auth` Blueprint
- **File:** `backend/src/auth/vc_auth.py`
- **Prefix:** `/auth/vc-login`
- **Routes:** 5
- **Purpose:** Verifiable Credential authentication
- **Key Routes:**
  - `/auth/vc-login/initiate` - Start VC login
  - `/auth/vc-login/verify` - Verify VC presentation

#### `session_auth` Blueprint
- **File:** `backend/src/simple_auth.py`
- **Prefix:** `/`
- **Routes:** 2
- **Conditional:** Only if `ENABLE_AUTH=true`
- **Purpose:** Simple password-based authentication

---

### Validation Blueprints

#### `vcstatus` Blueprint
- **File:** `backend/src/validate/vcstatus.py`
- **Prefix:** `/vcstatus`
- **Routes:** 18
- **Purpose:** Credential status management
- **Key Routes:**
  - `/vcstatus` - Status page
  - `/api/credentials` - Credential API
  - `/api/credential/<id>` - Single credential operations

#### `validate_legacy` Blueprint
- **File:** `backend/src/validate/validate.py`
- **Prefix:** `/validate`
- **Routes:** 5
- **Purpose:** Legacy validation routes (backward compatibility)

---

### Settings Blueprints

#### `settings` Blueprint
- **File:** `backend/src/settings/__init__.py`
- **Prefix:** `/`
- **Routes:** 15
- **Purpose:** Settings UI
- **Sub-Modules:**
  - Core settings
  - Selective disclosure
  - Key management
  - Trust settings
  - Network configuration
  - Health checks
  - Database management
  - Server configuration

#### `api_settings` Blueprint
- **File:** `backend/src/settings/api.py`
- **Prefix:** `/`
- **Routes:** 27
- **Purpose:** Settings API endpoints
- **Key Routes:**
  - `/api/settings/*` - All settings API endpoints

---

### Feature Blueprints

#### `api_integration` Blueprint
- **File:** `backend/src/api_integration.py`
- **Prefix:** `/`
- **Routes:** 24
- **Purpose:** External API integration

#### `debug` Blueprint
- **File:** `backend/src/issuer/debug.py`
- **Prefix:** `/debug`
- **Routes:** 8
- **Purpose:** Debug tools (development only)

#### `usecases` Blueprint
- **File:** `backend/src/usecases/usecases.py`
- **Prefix:** `/usecases`
- **Routes:** 11
- **Purpose:** Use case demonstrations

#### `monitoring` Blueprint
- **File:** `backend/src/monitoring.py`
- **Prefix:** `/`
- **Routes:** 10
- **Purpose:** Health checks and metrics

---

## 🔧 Adding a New Blueprint

### Step 1: Create Blueprint File
```python
# backend/src/my_feature/__init__.py
from flask import Blueprint

my_feature_bp = Blueprint('my_feature', __name__, url_prefix='/my-feature')

@my_feature_bp.route('/')
def index():
    return {'message': 'Hello'}
```

### Step 2: Register in `register_blueprints()`
```python
# backend/src/__init__.py
def register_blueprints(app):
    # ... existing blueprints ...
    
    # Add your new blueprint
    from .my_feature import my_feature_bp
    app.register_blueprint(my_feature_bp)
    
    logger.info(f"✅ Registered {len(app.blueprints)} blueprints")
```

### Step 3: Document in This File
Add your blueprint to the appropriate section above.

---

## 📝 Blueprint Registration Order

The order matters for:
1. **Route precedence** - Earlier blueprints take precedence
2. **Middleware order** - Blueprints registered first get middleware first
3. **Error handling** - Order affects error handler registration

**Current Order:**
1. Core (home, issuer, verifier)
2. Auth (auth, vc_auth, session_auth)
3. Validation (vcstatus, validate_legacy)
4. Settings (settings, api_settings)
5. Features (api_integration, debug, usecases, monitoring)
6. Network API (dynamic)

**Recommendation:** Keep this order unless you have a specific reason to change it.

---

## 🐛 Troubleshooting

### Blueprint Not Found
**Error:** `Blueprint 'my_blueprint' is not registered`

**Solution:**
1. Check blueprint is imported in `register_blueprints()`
2. Check blueprint name matches registration
3. Check blueprint is registered before use

### Route Conflict
**Error:** `Route already registered`

**Solution:**
1. Check for duplicate route definitions
2. Check blueprint prefixes don't overlap
3. Use unique route paths

### Blueprint Import Error
**Error:** `Cannot import blueprint`

**Solution:**
1. Check file exists and is in correct location
2. Check blueprint is exported from module
3. Check import path is correct

---

## 📚 Related Documentation

- **Routing Security Audit:** `docs/ROUTING_SECURITY_AUDIT.md`
- **Routing Improvement Plan:** `docs/ROUTING_IMPROVEMENT_PLAN.md`
- **Quick Reference:** `docs/ROUTING_QUICK_REFERENCE.md`

---

**Maintained by:** StudentVC Development Team  
**Last Review:** November 8, 2025

