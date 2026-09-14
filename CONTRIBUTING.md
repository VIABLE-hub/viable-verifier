# Contributing to VIABLE

## Make a focused change

1. Read the README, relevant interface/protocol documents and any applicable `AGENTS.md`.
2. Link the problem and acceptance criteria to an issue or the team project. Work on a focused branch and open a pull request.
3. Keep credentials, private keys, personal credential data and production exports out of commits and issue attachments. Use synthetic fixtures.
4. Run the applicable commands from the README. Record the commit, environment, results and any checks that could not run. Do not report a suppressed failure as a passing test.
5. For API, proof, schema or native-binding changes, identify consumers and update contracts, fixtures and documentation together.
6. For deployment changes, record configuration, migration, backup/rollback and a smoke check before release.

## Review responsibilities

- **Mateusz: Product Owner & Testing.** Priorities, acceptance criteria and test evidence.
- **Adam: Development & Operations.** Implementation, dependencies, deployment and recovery.
- **Patrick Herbke: CEO.** Company priorities and business commitments.
- **Florian Wehner: CBO.** Buyer requirements and customer-facing claims.

These responsibilities do not change GitHub permissions or imply that one person has already reviewed a change. Preserve contributor attribution and existing licence notices. Specialist cryptography/interoperability work needs an appropriately qualified reviewer.

## Names and evidence

Use the VIABLE product name and lowercase `viable-` repository names. Preserve package IDs, protocol identifiers, native targets and deployed directories unless their consumers are migrated together. Keep the `viable-dfi-*` family consistent within the Witness research track.

Distinguish implemented code, passing tests, integrated demonstrations and production evidence. Do not claim eIDAS certification, universal offline transport support, guaranteed privacy or measured performance without scoped evidence.
