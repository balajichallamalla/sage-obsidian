#!/usr/bin/env python3
"""Read the vault's _system/config.json (written by sage-obsidian setup).

Import from other tools:  from vault_config import load, is_owner, owner_emails
Env override (tests): VAULT_ROOT
"""
import json
import os
from pathlib import Path


def root():
    return Path(os.environ.get("VAULT_ROOT") or Path(__file__).resolve().parents[2])


def load():
    p = root() / "_system/config.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def owner_match():
    owner = load().get("owner", {})
    names = owner.get("match") or [owner.get("first_name", "")]
    return [str(n).lower() for n in names if str(n).strip()]


def is_owner(value):
    """True when a frontmatter value (assignee, author, link) names the vault owner."""
    text = str(value or "").lower()
    return any(m in text for m in owner_match())


def owner_emails():
    return {str(e).lower() for e in load().get("owner", {}).get("emails", [])}


def module_on(name):
    return bool(load().get("modules", {}).get(name))
