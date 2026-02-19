from __future__ import annotations
import streamlit as st

from kb_loader import load_kb
from retriever import TfidfRetriever
from consultant import (
    build_discovery_questions,
    parse_profile,
    consultant_response,
)

st.set_page_config(page_title="Security Consultant Chatbot", page_icon="🛡️", layout="centered")

st.title("🛡️ Security Consultant Chatbot")
st.caption("Advises new business owners on security policies, standards, and practical controls.")

# Sidebar configuration
st.sidebar.header("Configuration")
use_local_llm = st.sidebar.toggle("Use local LLM (Ollama)", value=False)
ollama_model = st.sidebar.text_input("Ollama model name", value="llama3")
top_k = st.sidebar.slider("KB results (top_k)", 2, 6, 4)

st.sidebar.divider()
st.sidebar.subheader("Consultant Discovery (optional but recommended)")

if "discovery" not in st.session_state:
    st.session_state.discovery = {
        "industry": "",
        "geography": "",
        "pii": "yes",
        "payments": "no",
        "employees": "no",
        "cloud": "yes",
        "stage": "idea/MVP",
    }

# Discovery form
with st.sidebar.form("discovery_form"):
    st.session_state.discovery["industry"] = st.text_input("Industry", st.session_state.discovery["industry"])
    st.session_state.discovery["geography"] = st.text_input("Geography", st.session_state.discovery["geography"])

    st.session_state.discovery["pii"] = st.selectbox("Collect PII?", ["yes", "no"], index=0 if st.session_state.discovery["pii"]=="yes" else 1)
    st.session_state.discovery["payments"] = st.selectbox("Process payments?", ["yes", "no"], index=0 if st.session_state.discovery["payments"]=="yes" else 1)
    st.session_state.discovery["employees"] = st.selectbox("Employees/contractors?", ["yes", "no"], index=0 if st.session_state.discovery["employees"]=="yes" else 1)
    st.session_state.discovery["cloud"] = st.selectbox("Use cloud?", ["yes", "no"], index=0 if st.session_state.discovery["cloud"]=="yes" else 1)

    st.session_state.discovery["stage"] = st.text_input("Stage (idea/MVP/launch/growing)", st.session_state.discovery["stage"])
    saved = st.form_submit_button("Save profile")

if saved:
    st.sidebar.success("Profile saved.")

# Load KB + retriever
@st.cache_resource
def init_retriever():
    chunks = load_kb("kb")
    return TfidfRetriever(chunks)

retriever = init_retriever()

# Chat state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Tell me what you’re building, and I’ll provide a security policy + standards roadmap like a consultant."}
    ]

# Render history
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Input
user_input = st.chat_input("Ask a security/compliance question (e.g., 'What policies do I need for a SaaS app?')")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Build profile
    profile = parse_profile(st.session_state.discovery)

    # Retrieve relevant KB content
    results = retriever.search(user_input, top_k=top_k)

    # Generate response
    reply = consultant_response(
        user_message=user_input,
        profile=profile,
        retrieved=results,
        use_local_llm=use_local_llm,
        ollama_model=ollama_model.strip() or "llama3",
    )

    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)

    # Optional: show retrieved sources for transparency
    with st.expander("See what internal references were used"):
        for r in results:
            st.markdown(f"**{r.source}** — score {r.score:.3f}")
            st.markdown(r.text[:1200] + ("..." if len(r.text) > 1200 else ""))
            st.divider()
