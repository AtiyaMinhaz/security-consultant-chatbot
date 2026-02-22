import os
from typing import List


def load_kb(kb_path: str = "kb") -> List[str]:
    """
    Load all .md files from kb/ as plain text strings.
    Returns a list[str] where each element is the content of one file.
    """
    if not os.path.exists(kb_path):
        raise FileNotFoundError(f"KB folder not found: {kb_path}")

    texts: List[str] = []

    for name in sorted(os.listdir(kb_path)):
        if not name.endswith(".md"):
            continue

        path = os.path.join(kb_path, name)

        # Guardrail: skip folders accidentally named *.md
        if not os.path.isfile(path):
            continue

        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                texts.append(content)

    if not texts:
        raise ValueError("KB is empty or no valid .md files found in kb/")

    return texts