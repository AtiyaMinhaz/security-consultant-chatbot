import os
import textwrap
from typing import List

import requests
import streamlit as st

from kb_loader import load_kb
from retriever import KeywordRetriever, RetrievalResult

# ----------------------------
# Configuration
# ----------------------------
APP_TITLE = "Security Consultant Chatbot"
APP_SUBTITLE = "Practical security policies + standards guidance for new business owners"
KB_ROOT = "kb"

# ----------------------------
# Anthropic Claude API call (Streaming)
# ----------------------------
def call_claude_streaming(api_key: str, model: str, messages: list, system: str, temperature: float = 0.2):
    """Generator that yields text chunks as they stream in."""
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": 2048,
        "temperature": temperature,
        "system": system,
        "messages": messages,
        "stream": True,
    }
    with requests.post(url, headers=headers, json=payload, timeout=60, stream=True) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line:
                continue
            decoded = line.decode("utf-8")
            if decoded.startswith("data: "):
                data_str = decoded[6:]
                if data_str == "[DONE]":
                    break
                try:
                    import json
                    data = json.loads(data_str)
                    if data.get("type") == "content_block_delta":
                        delta = data.get("delta", {})
                        if delta.get("type") == "text_delta":
                            yield delta.get("text", "")
                except Exception:
                    continue


# ----------------------------
# Page Config
# ----------------------------
st.set_page_config(page_title=APP_TITLE, layout="wide", page_icon="🔐")

# ----------------------------
# Custom CSS for proper chat UI
# ----------------------------
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #0f1117; }

    /* Title styling */
    h1 { color: #00d4ff !important; font-size: 2rem !important; }

    /* Chat bubbles */
    .user-bubble {
        background: #1e3a5f;
        border-radius: 18px 18px 4px 18px;
        padding: 12px 18px;
        margin: 8px 0 8px 15%;
        color: #ffffff !important;
        font-size: 0.95rem;
        line-height: 1.5;
        border: 1px solid #2a5080;
    }
    .assistant-bubble {
        background: #1a1f2e;
        border-radius: 18px 18px 18px 4px;
        padding: 14px 20px;
        margin: 8px 15% 8px 0;
        color: #ffffff !important;
        font-size: 0.95rem;
        line-height: 1.6;
        border: 1px solid #2a3a4a;
        border-left: 3px solid #00d4ff;
    }
    /* Force all markdown text to be bright white */
    .stMarkdown p, .stMarkdown li, .stMarkdown h1,
    .stMarkdown h2, .stMarkdown h3, .stMarkdown h4,
    .stMarkdown strong, .stMarkdown em, .stMarkdown code {
        color: #f0f4f8 !important;
    }
    .chat-label-user {
        text-align: right;
        font-size: 0.75rem;
        color: #4a90d9;
        margin-right: 4px;
        margin-bottom: 2px;
        font-weight: 600;
    }
    .chat-label-assistant {
        font-size: 0.75rem;
        color: #00d4ff;
        margin-left: 4px;
        margin-bottom: 2px;
        font-weight: 600;
    }
    .chat-container {
        max-height: 520px;
        overflow-y: auto;
        padding: 10px;
        border: 1px solid #1e2d3d;
        border-radius: 12px;
        background: #0d1117;
        margin-bottom: 16px;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0d1117;
        border-right: 1px solid #1e2d3d;
    }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #00d4ff !important;
    }

    /* Selectbox and sliders */
    .stSelectbox label, .stSlider label { color: #8baab8 !important; }

    /* Status badges */
    .status-live {
        background: #0d2b1d;
        border: 1px solid #00c851;
        color: #00c851;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
    .status-demo {
        background: #2b1a0d;
        border: 1px solid #ff9500;
        color: #ff9500;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }

    /* Input box */
    .stTextInput input {
        background: #1a1f2e !important;
        border: 1px solid #2a3a4a !important;
        color: #e8f4fd !important;
        border-radius: 8px !important;
    }

    /* Primary button */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0077b6, #00b4d8) !important;
        border: none !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.5rem 2rem !important;
    }
    .stButton > button[kind="secondary"] {
        background: transparent !important;
        border: 1px solid #2a3a4a !important;
        color: #8baab8 !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------
# Header
# ----------------------------
st.markdown("# 🔐 Security Consultant Chatbot")
st.markdown(f"<span style='color:#8baab8;font-size:0.95rem'>{APP_SUBTITLE}</span>", unsafe_allow_html=True)
st.divider()

# ----------------------------
# Sidebar
# ----------------------------
with st.sidebar:
    st.markdown("## 🏢 Business Context")
    st.markdown("<span style='color:#8baab8;font-size:0.8rem'>Customize advice to your situation</span>", unsafe_allow_html=True)
    st.markdown("")

    industry = st.selectbox(
        "Industry",
        ["SaaS", "Healthcare", "Finance", "Retail/eCommerce", "Education", "Manufacturing", "Other"],
        index=0,
    )
    stage = st.selectbox("Company Stage", ["Early-stage", "Growth", "Enterprise"], index=0)
    hosting = st.selectbox("Hosting", ["Cloud", "On-prem", "Hybrid"], index=0)
    data_handled = st.selectbox(
        "Data Handled",
        ["PII", "PHI", "PCI", "Financial", "Internal-only", "Mixed"],
        index=0
    )

    st.divider()
    st.markdown("## ⚙️ AI Settings")

    # --- FIX: Fetch API key FIRST, then use it ---
    api_key = ""
    model = "claude-sonnet-4-5"

    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        pass

    api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")

    try:
        model = st.secrets.get("ANTHROPIC_MODEL", model)
    except Exception:
        pass
    model = os.getenv("ANTHROPIC_MODEL", model)

    temperature = st.slider("Response Temperature", 0.0, 1.0, 0.2, 0.1,
                            help="Lower = more precise, Higher = more creative")

    st.markdown("")
    if api_key:
        st.markdown('<span class="status-live">🟢 AI Mode: Live</span>', unsafe_allow_html=True)
        st.markdown(f"<span style='color:#8baab8;font-size:0.75rem'>Model: {model}</span>", unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-demo">🟡 Demo Mode: No API Key</span>', unsafe_allow_html=True)
        with st.expander("How to enable AI"):
            st.markdown("""
**Streamlit Cloud:**
1. Go to your app → **Settings → Secrets**
2. Add:
```
ANTHROPIC_API_KEY = "sk-ant-..."
ANTHROPIC_MODEL = "claude-sonnet-4-5"
```
3. Reboot the app
            """)

    st.divider()
    if st.button("🗑️ Clear Chat", type="secondary"):
        st.session_state.chat = []
        st.rerun()

    st.markdown("")
    st.markdown("<span style='color:#4a5568;font-size:0.75rem'>Powered by Claude (Anthropic)</span>", unsafe_allow_html=True)
    st.markdown("<span style='color:#4a5568;font-size:0.75rem'>KB: NIST CSF • ISO 27001 • CIS Controls • SOC2 • GDPR</span>", unsafe_allow_html=True)


# ----------------------------
# KB + Retriever (cached)
# ----------------------------
@st.cache_data(show_spinner="Loading security knowledge base...")
def get_retriever() -> KeywordRetriever:
    kb_texts: List[str] = load_kb(KB_ROOT)
    return KeywordRetriever(kb_texts)


retriever = get_retriever()


# ----------------------------
# System Prompt
# ----------------------------
def build_system_prompt(industry, stage, hosting, data_handled):
    return f"""You are an elite senior security consultant with 15+ years of experience advising businesses on cybersecurity, compliance, and risk management. You specialize in practical, actionable guidance — not generic advice.

BUSINESS CONTEXT FOR THIS SESSION:
- Industry: {industry}
- Company Stage: {stage}
- Hosting Environment: {hosting}
- Data Handled: {data_handled}

YOUR RESPONSE MUST ALWAYS FOLLOW THIS STRUCTURE:

## 🎯 Top 5 Priority Actions
Numbered list of the most critical security actions for this specific business context. Be specific — reference their industry and data type.

## ⚠️ Risks If Ignored
What happens if they don't act? Include regulatory, financial, and reputational risks relevant to their industry.

## ✅ Implementation Checklist
A concrete checklist they can act on today. Use checkboxes (- [ ] format).

## 📅 30 / 60 / 90 Day Roadmap
- **Days 1-30 (Foundation):** Quick wins and critical gaps
- **Days 31-60 (Structure):** Policies, tools, and controls
- **Days 61-90 (Maturity):** Audits, training, and ongoing monitoring

## 📋 Relevant Standards
Which specific frameworks apply (NIST CSF, ISO 27001, CIS Controls, SOC 2, GDPR, HIPAA, PCI-DSS) and WHY for their context.

TONE: Professional but clear. Avoid jargon without explanation. This person may be a business owner, not a security expert.
IMPORTANT: Always tailor advice to the specific industry ({industry}) and data type ({data_handled}). Never give generic responses."""


# ----------------------------
# Chat State
# ----------------------------
if "chat" not in st.session_state:
    st.session_state.chat = []

# ----------------------------
# Chat Display
# ----------------------------
chat_placeholder = st.empty()

def render_chat():
    with chat_placeholder.container():
        if not st.session_state.chat:
            st.markdown("""
<div style='text-align:center; padding: 40px; color: #4a5568;'>
    <div style='font-size:3rem'>🔐</div>
    <div style='font-size:1.1rem; color:#8baab8; margin-top:10px'>Ask any security or compliance question</div>
    <div style='font-size:0.85rem; margin-top:8px'>e.g. "What security policies do I need for a healthcare SaaS startup?"</div>
    <div style='font-size:0.85rem; color:#4a5568; margin-top:4px'>e.g. "How do I become SOC 2 compliant as an early-stage company?"</div>
</div>
""", unsafe_allow_html=True)
        else:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            for m in st.session_state.chat:
                if m["role"] == "user":
                    st.markdown(f'<div class="chat-label-user">You</div><div class="user-bubble">{m["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-label-assistant">🔐 Security Consultant</div>', unsafe_allow_html=True)
                    # Use st.markdown for proper markdown rendering inside expander
                    with st.container():
                        st.markdown(m["content"])
            st.markdown('</div>', unsafe_allow_html=True)

render_chat()

# ----------------------------
# Input Area
# ----------------------------
col1, col2 = st.columns([5, 1])
with col1:
    user_q = st.text_input(
        "Your question:",
        placeholder="e.g. What security controls do I need for a cloud-based SaaS handling PII?",
        label_visibility="collapsed",
        key="user_input"
    )
with col2:
    ask_clicked = st.button("Ask →", type="primary", use_container_width=True)

# ----------------------------
# Suggested Questions
# ----------------------------
st.markdown("<span style='color:#4a5568;font-size:0.8rem'>Quick questions:</span>", unsafe_allow_html=True)
q_col1, q_col2, q_col3 = st.columns(3)

suggested_q = None
with q_col1:
    if st.button("🛡️ What policies do I need first?", use_container_width=True):
        suggested_q = "What are the most important security policies I need to create first for my business?"
with q_col2:
    if st.button("📋 SOC 2 compliance steps", use_container_width=True):
        suggested_q = "How do I achieve SOC 2 compliance? What are the steps and how long does it take?"
with q_col3:
    if st.button("🔒 Data encryption basics", use_container_width=True):
        suggested_q = "What data encryption do I need for my business and how do I implement it?"

# Use suggested question if clicked
final_q = suggested_q or (user_q.strip() if ask_clicked and user_q.strip() else None)

# ----------------------------
# Process Query
# ----------------------------
if final_q:
    # Retrieve KB context
    results: List[RetrievalResult] = retriever.search(final_q, top_k=4)
    context_block = "\n\n".join([
        f"[KB: {textwrap.shorten(r.text, width=1200, placeholder='...')}]"
        for r in results
    ]) if results else "No specific KB snippets found — respond from expertise."

    system_msg = build_system_prompt(industry, stage, hosting, data_handled)

    # Build messages
    messages = []
    messages.append({
        "role": "user",
        "content": f"[CONTEXT FROM KNOWLEDGE BASE]\n{context_block}\n\n[END CONTEXT]\n\nPlease use the above knowledge base excerpts to inform your answer where relevant."
    })
    messages.append({
        "role": "assistant",
        "content": "Understood. I've reviewed the knowledge base. I'm ready to provide expert security guidance tailored to your business context. What's your question?"
    })
    for m in st.session_state.chat[-8:]:
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": final_q})

    # Store user question
    st.session_state.chat.append({"role": "user", "content": final_q})

    # Stream or demo
    if api_key:
        try:
            # Show user bubble immediately
            st.markdown(f'<div class="chat-label-user">You</div><div class="user-bubble">{final_q}</div>', unsafe_allow_html=True)
            st.markdown('<div class="chat-label-assistant">🔐 Security Consultant</div>', unsafe_allow_html=True)

            # Stream response word by word using st.write_stream
            stream = call_claude_streaming(
                api_key=api_key,
                model=model,
                messages=messages,
                system=system_msg,
                temperature=temperature
            )
            answer = st.write_stream(stream)

        except Exception as e:
            answer = f"⚠️ **API Error:** {str(e)}\n\nPlease check your API key in Streamlit Secrets."
            st.error(answer)
    else:
        answer = f"""## 🔐 Demo Mode — AI Not Connected

To enable real AI responses:
1. Go to Streamlit Cloud → your app → **Settings → Secrets**
2. Add: `ANTHROPIC_API_KEY = "sk-ant-your-key-here"`
3. Reboot the app
"""
        st.info(answer)

    st.session_state.chat.append({"role": "assistant", "content": answer})
    st.rerun()