# VIABLE Credential Verifier

Prototype service for receiving and verifying digital credential presentations.

**Repository:** `viable-verifier`

**Status:** Credential prototype. Source availability does not establish production readiness or certification.

## Purpose and scope

This Flask application provides presentation verification workflows. The project originated in the StudentVC/VERITAS prototypes; those names still occur in historical modules and deployment files. The current product name is VIABLE.

The separate [credential issuer](https://github.com/VIABLE-hub/viable-issuer) and [credential verifier](https://github.com/VIABLE-hub/viable-verifier) have different responsibilities. Do not assume identical endpoints, trust policy or configuration across them.

## Structure

- [backend/](backend/): Flask application, credential logic and crypto adapters.
- [tests/](tests/): repository-level test suites.
- [Makefile](Makefile): setup and local development targets.
- [deploy/](deploy/): deployment definitions requiring review against the actual host.
- [env.example](env.example): configuration names; use fresh local values.

## Local setup

Use Python 3.12, Make and a Rust toolchain where native BBS bindings are required. Linux/macOS or WSL is the documented development path. Inspect the Makefile before running setup: it rebuilds native bindings.

```sh
git submodule status
# Resolve required native-library sources before continuing.
make setup
make dev
```

`make dev` selects port 8888 in the current Makefile. `make start-all` is an alias for this single development instance; it does not launch four tenants. Historical `make dev-tub`, `make dev-fub` and `make dev-root` instructions do not match the current targets.

**Dependency limitation:** `.gitmodules` refers to historical sibling repositories such as `bbs-core`, `android` and `ios`. These are not present under those names in the reviewed VIABLE-hub repository list. A recursive clone is therefore not a reproducible setup guarantee. Ask Adam to identify the intended native-library commit/artifact and record it before building. Do not silently substitute a crypto fallback or test key for a production implementation.

## Validation

From the repository root, after configuring an isolated test environment and dependencies:

```sh
.venv/bin/python -m pytest tests/
```

The test suite includes integration paths; select fixtures and endpoints before running it. Use synthetic credentials and test keys only. Record the command, commit, result and any skipped tests. The historical `make test` changes into `backend/`, while the main suites live under root `tests/`.

## Deployment limitation

The checked-in CI deployment still references the former server, and some lint/test steps suppress failures. Treat an overall green run as insufficient release evidence until those gates and the deployment topology are reconciled. Documentation-only maintenance must not restart live services. Have Adam verify the current host, persistent data, native dependencies, rollback and real test results before a code release.

## Trust and interoperability

Document the exact credential format, proof implementation, issuer trust configuration, nonce/replay handling and status freshness for each tested workflow. A repository description is not eIDAS certification. Offline QR, NFC and BLE require device- and protocol-specific evidence; online DID/status retrieval must be provisioned or bounded explicitly before an offline claim.

## Contributing and support

See [CONTRIBUTING.md](CONTRIBUTING.md) for changes and validation, and [SECURITY.md](SECURITY.md) for private security reporting. Product information: [viable-id.com](https://viable-id.com/).

## Licence

See [LICENSE](LICENSE); existing contributor notices and third-party terms remain applicable.
