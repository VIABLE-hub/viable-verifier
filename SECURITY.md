# Security policy

## Report privately

For a public repository with GitHub private vulnerability reporting enabled, use
Security → Report a vulnerability. If that option is absent, or for a private
repository, contact your VIABLE maintainer through the established private channel.
External reporters can use https://viable-id.com/contact to request a confidential
reporting channel **without including exploit details, keys or personal data**.

Include affected repository/version, impact, safe reproduction steps and suggested
mitigation once a private channel is established. Never use real customer credentials.

## Support scope

The affected repository must list supported versions and review status. Research and
prototype code is not covered by an implied production SLA or security certification.
Maintainership and a monitored reporting route must be assigned before declaring a
release supported. Coordinate disclosure after impact assessment and mitigation.

Do not commit secrets. If a key is exposed, revoke or rotate it; deleting the visible
file or rewriting Git history alone does not invalidate the key.
