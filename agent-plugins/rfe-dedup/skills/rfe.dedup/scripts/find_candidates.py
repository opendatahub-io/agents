#!/usr/bin/env python3
"""Find candidate duplicate pairs using semantic embeddings and FAISS.

Reads individual RFE JSON files from an rfes/ directory one at a time,
embeds each RFE's text (summary + description + comments), indexes them
in FAISS, and finds nearest neighbors above a similarity threshold.
"""

import argparse
import json
import os
import sys
from pathlib import Path

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

try:
    import numpy as np
except ImportError:
    print("Error: 'numpy' required. Install with: pip install numpy", file=sys.stderr)
    sys.exit(1)

try:
    import faiss
except ImportError:
    print(
        "Error: 'faiss-cpu' required. Install with: pip install faiss-cpu",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print(
        "Error: 'sentence-transformers' required. Install with: pip install sentence-transformers",
        file=sys.stderr,
    )
    sys.exit(1)

DEFAULT_MODEL = "ibm-granite/granite-embedding-english-r2"
DEFAULT_THRESHOLD = 0.8
DEFAULT_K = 10
MAX_TEXT_CHARS = 24000
MAX_RFES = 5000


def build_text(issue):
    parts = []

    summary = issue.get("summary", "")
    if summary:
        parts.append(summary)

    description = issue.get("description", "")
    if description:
        parts.append(description)

    core_text = "\n\n".join(parts)

    comments = issue.get("comments", [])
    if comments:
        comment_texts = []
        for c in reversed(comments):
            body = c.get("body", "")
            if body:
                comment_texts.append(body)
        comments_joined = "\n\n".join(comment_texts)

        remaining = MAX_TEXT_CHARS - len(core_text) - 2
        if remaining > 100:
            if len(comments_joined) > remaining:
                comments_joined = comments_joined[:remaining]
            core_text = core_text + "\n\n" + comments_joined

    return core_text


def load_rfes(rfes_dir):
    """Load RFE files one at a time, yielding (key, text) pairs."""
    rfe_files = sorted(rfes_dir.glob("*.json"))
    rfe_files = [f for f in rfe_files if f.name != "_meta.json"]

    for rfe_file in rfe_files:
        try:
            issue = json.loads(rfe_file.read_text())
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error: could not read {rfe_file}: {e}", file=sys.stderr)
            sys.exit(1)
        key = issue["key"]
        text = build_text(issue)
        yield key, text


def find_candidates(rfes_dir, model_name, threshold, k):
    keys = []
    texts = []
    for key, text in load_rfes(rfes_dir):
        keys.append(key)
        texts.append(text)

    n = len(keys)
    print(f"Loaded {n} RFEs from {rfes_dir}/", file=sys.stderr)

    if n > MAX_RFES:
        print(
            f"Error: loaded {n} RFEs, exceeding MAX_RFES={MAX_RFES}. "
            "Narrow your JQL scope.",
            file=sys.stderr,
        )
        sys.exit(1)

    if n < 2:
        print("Need at least 2 RFEs to find duplicates", file=sys.stderr)
        return [], n

    print(f"Loading embedding model {model_name}...", file=sys.stderr)
    model = SentenceTransformer(model_name)

    print(f"Encoding {n} RFEs...", file=sys.stderr)
    embeddings = model.encode(
        texts, batch_size=4, show_progress_bar=False, normalize_embeddings=True
    )
    embeddings = np.array(embeddings, dtype=np.float32)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    search_k = min(k + 1, n)
    print(f"Searching for top-{k} neighbors per RFE...", file=sys.stderr)
    similarities, indices = index.search(embeddings, search_k)

    seen_pairs = set()
    candidates = []

    for i in range(n):
        for j_idx in range(search_k):
            neighbor = indices[i][j_idx]
            if neighbor == i:
                continue
            sim = float(similarities[i][j_idx])
            if sim < threshold:
                continue

            pair_key = tuple(sorted([keys[i], keys[neighbor]]))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            candidates.append(
                {
                    "rfe_a": keys[i],
                    "rfe_b": keys[neighbor],
                    "similarity_score": round(sim, 4),
                }
            )

    candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
    print(
        f"Found {len(candidates)} candidate pairs above threshold {threshold}",
        file=sys.stderr,
    )
    return candidates, n


def main():
    parser = argparse.ArgumentParser(
        description="Find candidate duplicate RFE pairs using embeddings"
    )
    parser.add_argument(
        "--rfes-dir",
        required=True,
        help="Directory with individual RFE JSON files (from fetch_rfes.py)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output JSON file with candidate pairs",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Embedding model name (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help=f"Minimum cosine similarity for candidates (default: {DEFAULT_THRESHOLD})",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=DEFAULT_K,
        help=f"Max neighbors per RFE to consider (default: {DEFAULT_K})",
    )
    args = parser.parse_args()

    if args.k <= 0:
        print(f"Error: --k must be a positive integer, got {args.k}", file=sys.stderr)
        sys.exit(1)

    rfes_dir = Path(args.rfes_dir)
    if not rfes_dir.is_dir():
        print(f"Error: {rfes_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    candidates, total_rfes = find_candidates(
        rfes_dir, args.model, args.threshold, args.k
    )

    result = {
        "model": args.model,
        "threshold": args.threshold,
        "k": args.k,
        "total_rfes": total_rfes,
        "total_candidates": len(candidates),
        "candidates": candidates,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2))
    print(f"Wrote {len(candidates)} candidates to {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
