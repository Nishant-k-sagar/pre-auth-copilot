# AGENTS.md

## Purpose

This document defines the engineering rules, coding standards, safety constraints, and operational expectations for all AI agents, contributors, and automation systems working on this repository.

All generated, modified, or reviewed code MUST follow these instructions strictly.

---

# Core Principles

- Write production-grade code only.
- Prioritize correctness, maintainability, readability, security, and scalability.
- Never produce placeholder-quality implementations unless explicitly requested.
- Never put the hard-coded things to pass the requirements. Never.
- Think through edge cases before implementation.
- Avoid techical debt or Minimize technical debt.
- Avoid unnecessary abstractions and overengineering.
- Prefer explicitness over implicit behavior.
- Keep changes minimal, isolated, and reversible.

---

# Code Quality Standards

## General Rules

- Follow PEP 8.
- Use type hints everywhere possible.
- Prefer composition over inheritance.
- Avoid global mutable state.
- Keep functions small and single-purpose.
- Use meaningful variable and function names.
- Avoid magic numbers and hardcoded constants.
- Use constants/configuration files where appropriate.
- Avoid duplicated logic.
- Write deterministic code whenever possible.
- Never use direct end points, use .env standards.
- Do not use or generate emojies in code snippets or anywhere.

---

# Production Grade Requirements

Every implementation MUST:
- Again, avoid hardcoded and unnecessary placeholders.
- Handle failures gracefully.
- Include proper error handling.
- Include logging where necessary.
- Validate all external inputs.
- Handle invalid states safely.
- Consider concurrency issues if applicable.
- Avoid memory leaks and resource leaks.
- Clean up opened resources properly.
- Avoid race conditions.
- Be resilient to partial failures.
- Avoid blocking operations unless necessary.
- Use async patterns correctly where applicable.
- Fail loudly for developer errors.
- Fail safely for user errors.

---

# Edge Case Requirements

Always consider:

- Null/None values
- Empty inputs
- Large inputs
- Invalid types
- Unicode handling
- Encoding issues
- Timezone handling
- File permission issues
- Network failures
- Partial writes
- Duplicate requests
- Retry scenarios
- Floating-point precision
- Overflow/underflow
- Thread safety
- Process termination
- Resource exhaustion
- Rate limiting
- API timeout handling
- Corrupted files/data
- Backward compatibility

Never assume ideal input conditions.

---

# Security Rules

## Critical Restrictions

### NEVER:

- Read `.env` files
- Modify `.env` files
- Print environment variables
- Log secrets
- Expose credentials
- Commit secrets
- Access forbidden paths
- Modify deployment secrets
- Disable security checks
- Store plaintext secrets
- Hardcode API keys/tokens/passwords

---

# Forbidden Files & Paths

Agents MUST NEVER read, modify, overwrite, move, delete, or expose:

```text
.env
.env.*
*.pem
*.key
*.crt
*.p12
*.pfx
id_rsa
id_ed25519
secrets.*
credentials.*