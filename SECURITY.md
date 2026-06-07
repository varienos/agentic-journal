# Security Policy

## Supported Versions

Agentic Journal is pre-1.0. Security fixes are applied to the `main` branch.

## Reporting Security Issues

Please do not open a public issue for secrets exposure, token leakage, or
privacy-sensitive behavior.

Report security concerns privately through GitHub Security Advisories for this
repository, or contact the repository owner from the GitHub profile.

## Security Expectations

Agentic Journal is designed to avoid prompt transcript capture by default. Event
writers should not record full prompts, full file contents, API keys, bearer
tokens, passwords, or other secrets.

The normalization path redacts common secret-looking values, but callers are
still responsible for avoiding sensitive payloads.
