import os
from typing import List


def load_kb(kb_path: str = "kb") -> List[str]:
    """
    Load all .md files under kb_path (recursively) as plain text strings.
    Returns a list[str] where each element is the content of one file.

    This handles cases where kb accidentally becomes kb/kb/kb/... or has subfolders.
    """
    if not os.path.exists(kb_path):
        raise FileNotFoundError(f"KB folder not found: {kb_path}")

    texts: List[str] = []

    for root, _, files in os.walk(kb_path):
        for name in sorted(files):
            if not name.lower().endswith(".md"):
                continue

            path = os.path.join(root, name)

            # Guardrail: skip folders / weird artifacts
            if not os.path.isfile(path):
                continue

            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().strip()
                if content:
                    texts.append(content)

    if not texts:
        raise ValueError(f"KB is empty or no valid .md files found under: {kb_path}")

    return texts