# Contributing to VIABLE

Start with the target repository's README, maturity statement and open issues.
Discuss changes to protocols, cryptography or public APIs before implementing them.

1. Open a scoped issue describing the problem, affected component and acceptance criteria.
2. Create a short-lived branch; do not push directly to a protected release branch.
3. Use the repository's documented toolchain and synthetic fixtures. Add meaningful tests.
4. Explain behavior, compatibility and migration impact in the pull request.
5. Run the documented checks and link the results. Keep fixes focused and reviewable.

For cryptographic changes, state the threat model, parameter/library changes, test
vectors and independent review needed. A passing unit test is not a security proof.
Never include real credentials, keys, customer data or secrets in issues, commits or logs.

Retain license notices and contributor attribution. Repository-specific terms govern
contributions; this document adds no blanket license or CLA. Maintainers decide
whether a change fits the roadmap. Communicate respectfully and disclose conflicts.
