# 🛡️ Security Consultant Chatbot (Startup Advisory)

A portfolio-ready chatbot that advises new business owners on security policies, standards, and practical controls.
It uses a lightweight knowledge base (`/kb`) and retrieves relevant content to generate structured consultant-style guidance.

## Features
- Streamlit web UI
- TF-IDF retrieval over a local knowledge base
- Offline “consultant mode” response generator
- Optional local LLM support via Ollama (no cloud required)

## Quickstart (local)
```bash
# 1) Create venv
python3 -m venv .venv
source .venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Run the app
streamlit run app.py
