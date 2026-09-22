import streamlit as st
from openai import OpenAI

# Page configuration for embedding inside Power BI
st.set_page_config(page_title="VMY2026 AI Assistant", layout="centered")

# Hide default headers/footers to save screen space inside Power BI iframe
st.markdown(
    """
    <style>
        .block-container { padding-top: 1rem; padding-bottom: 1rem; }
        header { visibility: hidden; }
        footer { visibility: hidden; }
    </style>
""",
    unsafe_allow_html=True,
)

# Initialize OpenAI/Gonka Client using Streamlit Secrets
GONKA_BASE_URL = "https://api.gonkarouter.io/v1"
GONKA_API_KEY = st.secrets["sk-XZaLbHmWNsuQUN8ZKEhQYLJn4PcgM2gsfujpcpblX4m3zau0"]

client = OpenAI(
    base_url=GONKA_BASE_URL,
    api_key=GONKA_API_KEY,
)

SYSTEM_PROMPT = """You are the official AI Assistant for the Visit Malaysia Year (VMY2026/2027) Power BI Dashboard.
Key metrics:
- Total Arrivals: 165M | Total Hotels: 37K | Expenditure: RM 445.21M | Avg Stay: 4.34 days
- Transport: Land borders drive 65.32% of total entries (76.11M). Singapore is #1 market (~40M).
- Accommodation: Hotel occupancy is 42.66%. Domestic market accounts for 77.2%.
- Strategy: ML forecasts show steady arrival growth leading into Dec 2027."""

# Maintain conversation history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# User Input Box
if prompt := st.chat_input("Ask about VMY2026 metrics..."):
    # Display user input
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Call Gonka Router API
    with st.chat_message("assistant"):
        try:
            # Build full message payload including system prompt and prior chat
            api_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ]

            response = client.chat.completions.create(
                model="deepseek-ai/deepseek-v4-flash-0731",
                messages=api_messages,
                temperature=0.2,
            )

            reply = response.choices[0].message.content
            st.write(reply)

            # Store assistant response in history
            st.session_state.messages.append(
                {"role": "assistant", "content": reply}
            )

        except Exception as e:
            st.error(f"Gonka API Error: {str(e)}")