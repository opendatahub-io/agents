import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add the scripts directory to sys.path so test files can import scripts directly.
SCRIPTS_DIR = (
    Path(__file__).parent.parent.parent
    / "rfe-dedup"
    / "skills"
    / "rfe.dedup"
    / "scripts"
)
sys.path.insert(0, str(SCRIPTS_DIR))

# Mock heavy ML dependencies before any script imports them.
# setdefault leaves real installations in place; only fills gaps.
for _mod in ["faiss", "sentence_transformers"]:
    sys.modules.setdefault(_mod, MagicMock())

# Shared sample data used across multiple test modules.
SAMPLE_RFE_A = {
    "key": "RHAIRFE-1234",
    "summary": "Support single sign-on for enterprise users",
    "description": "Enterprise customers need SSO integration with their IdP.",
    "status": "New",
    "priority": "Major",
    "components": ["Auth"],
    "labels": ["sso", "enterprise"],
    "comments": [
        {"author": "Alice", "created": "2024-01-01T00:00:00Z", "body": "This is needed."},
        {"author": "Bob", "created": "2024-01-02T00:00:00Z", "body": "Confirmed by PM."},
    ],
    "links": [],
}

SAMPLE_RFE_B = {
    "key": "RHAIRFE-5678",
    "summary": "Add SAML-based authentication",
    "description": "We need SAML 2.0 support for enterprise login flows.",
    "status": "New",
    "priority": "Minor",
    "components": ["Auth"],
    "labels": ["saml"],
    "comments": [],
    "links": [],
}


def write_rfe(directory, rfe):
    (directory / f"{rfe['key']}.json").write_text(json.dumps(rfe))
