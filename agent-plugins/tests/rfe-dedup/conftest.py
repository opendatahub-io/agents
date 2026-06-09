import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest

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


class FakeIndex:
    """Mimics faiss.IndexFlatIP: brute-force inner-product search via numpy."""

    def __init__(self, dim):
        self.dim = dim
        self.vectors = None

    def add(self, vectors):
        self.vectors = np.array(vectors, dtype=np.float32)

    def search(self, queries, k):
        scores = queries @ self.vectors.T
        k = min(k, scores.shape[1])
        indices = np.argsort(-scores, axis=1)[:, :k].astype(np.int64)
        similarities = np.take_along_axis(scores, indices, axis=1)
        return similarities, indices


@pytest.fixture
def patch_embedding_pipeline(monkeypatch):
    """Patch find_candidates to use fake embeddings and FAISS index.

    Returns a callable: ``configure(embeddings_array)`` where
    *embeddings_array* is a 2-D numpy array (one row per RFE, in the
    order they will be loaded).  SentenceTransformer.encode() will
    return this array, and faiss.IndexFlatIP will use FakeIndex.
    """
    import find_candidates

    def configure(embeddings):
        embeddings = np.array(embeddings, dtype=np.float32)

        class _FakeST:
            def __init__(self, model_name):
                pass

            def encode(self, texts, **kwargs):
                return embeddings

        class _FakeFaiss:
            IndexFlatIP = FakeIndex

        monkeypatch.setattr(find_candidates, "SentenceTransformer", _FakeST)
        monkeypatch.setattr(find_candidates, "faiss", _FakeFaiss())

    return configure

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
