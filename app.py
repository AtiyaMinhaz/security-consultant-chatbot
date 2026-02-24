import os
import glob
import textwrap
from dataclasses import dataclass
from typing import List, Tuple

import requests
import streamlit as st

# ----------------------------
# Configuration
# ----------------------------
APP_TITLE = "Security Consultant AI"
APP_SUBTITLE = "AI-powered compliance & security advisor for new businesses"
KB_ROOT = "kb"

# ----------------------------
# KB Loader
# ----------------------------
@dataclass
class KBChunk:
    source: str
    text: str


def load_kb_chunks(kb_root: str = KB_ROOT) -> List[KBChunk]:
    patterns = [
        os.path.join(kb_root, "**", "*.md"),
    ]

    files = []
    for p in patterns:
        files.extend(glob.glob(p, recursive=True))

    chunks: List[KBChunk] = []

    for fp in sorted(set(files)):
        if os.path.isdir(fp):
            continue

        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read().strip()

        if not raw:
            continue

        parts = [p.strip() for p in raw.split("\n\n") if p.strip()]
        for part in parts:
            chunks.append(KBChunk(source=os.path.basename(fp), text=part))

    return chunks


def keyword_retrieve(chunks: List[KBChunk], query: str, top_k: int = 4) -> List[KBChunk]:
    q = query.lower()
    terms = [t for t in q.split() if len(t) > 3]

    scored = []
    for c in chunks:
        score = sum(c.text.lower().count(term) for term in terms)
        if score > 0:
            scored.append((score, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:top_k]]


# ----------------------------
# OpenAI Call
# ----------------------------
def call_openai(api_key: str, messages: list):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "gpt-4.1-mini",
        "messages": messages,
        "temperature": 0.3,
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title=APP_TITLE)
st.title(APP_TITLE)
st.caption(APP_SUBTITLE)

with st.sidebar:
    st.header("Business Context")

    industry = st.selectbox(
        "Industry",
        ["SaaS", "Healthcare", "Finance", "Retail", "Education", "Other"]
    )

    stage = st.selectbox(
        "Company Stage",
        ["Early", "Growth", "Enterprise"]
    )

    data_type = st.selectbox(
        "Data Type",
        ["PII", "PHI", "PCI", "Internal", "Mixed"]
    )

    api_key = st.secrets.get("OPENAI_API_KEY", None)

    if api_key:
        st.success("AI Mode Enabled")
    else:
        st.error("Demo Mode – No API key found")


@st.cache_data
def get_kb():
    return load_kb_chunks()


kb_chunks = get_kb()

if "chat" not in st.session_state:
    st.session_state.chat = []

user_input = st.text_input("Ask your security/compliance question:")

if st.button("Ask") and user_input:
    retrieved = keyword_retrieve(kb_chunks, user_input)

    context = "\n\n".join([c.text for c in retrieved])

    system_prompt = (
        "You are a senior cybersecurity and GRC consultant. "
        "Provide structured, actionable, prioritized guidance. "
        "Include a checklist at the end."
    )

    business_context = f"""
Industry: {industry}
Stage: {stage}
Data: {data_type}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": business_context},
        {"role": "user", "content": context},
        {"role": "user", "content": user_input},
    ]

    st.session_state.chat.append(("You", user_input))

    if api_key:
        try:
            answer = call_openai(api_key, messages)
        except Exception as e:
            answer = f"API Error: {e}"
    else:
        answer = "No API key configured."

    st.session_state.chat.append(("Assistant", answer))

st.subheader("Conversation")

for role, msg in st.session_state.chat:
    st.markdown(f"**{role}:** {msg}")