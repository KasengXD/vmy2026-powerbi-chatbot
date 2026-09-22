import streamlit as st
from openai import OpenAI

# Page configuration for embedding inside Power BI
st.set_page_config(page_title="VMY2026 AI Assistant", layout="centered")

# Custom CSS for Power BI Purple Theme & Clean Layout
# Dashboard-Matched CSS (VMY2026 Theme with Pure Black Font)
st.markdown(
    """
    <style>
        /* Base Canvas Background */
        .stApp, [data-testid="stAppViewContainer"] {
            background-color: #B5A1DB !important;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #000000 !important;
        }

        /* Tighten margins for iframe integration */
        .block-container {
            padding-top: 0.8rem;
            padding-bottom: 1rem;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }

        header, footer { visibility: hidden; }

        /* Force pure black font across all text elements */
        p, span, div, h1, h2, h3, h4, label, input, textarea {
            color: #000000 !important;
        }

        /* Fix Bottom Chat Input Container (Prevents Black Bar in Dark Mode) */
        [data-testid="stBottom"], div[data-testid="stBottom"] > div {
            background-color: #B5A1DB !important;
        }

        /* Header Card - White card with purple border */
        .header-card {
            background-color: #FFFFFF;
            border: 2px solid #502C7C;
            padding: 12px 16px;
            border-radius: 12px;
            margin-bottom: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .header-card h3 {
            margin: 0;
            padding: 0;
            color: #000000 !important;
            font-weight: 700;
            font-size: 1.1rem;
        }
        .header-card p {
            margin: 4px 0 0 0;
            font-size: 0.82rem;
            color: #000000 !important;
        }

        /* Base Chat Message Containers */
        [data-testid="stChatMessage"] {
            border-radius: 12px;
            padding: 10px 14px;
            margin-bottom: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        /* User Message - Soft Lavender Card */
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
            background-color: #E2D9F3 !important;
            border: 1px solid #502C7C !important;
        }

        /* AI Assistant Message - Crisp White Card */
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
            background-color: #FFFFFF !important;
            border: 1px solid #9E87C7 !important;
        }

        /* Chat Input Field Styling */
        [data-testid="stChatInput"] {
            border-radius: 10px;
            background-color: #FFFFFF !important;
            border: 2px solid #502C7C !important;
            box-shadow: 0 2px 8px rgba(80, 44, 124, 0.2);
        }
        [data-testid="stChatInput"] textarea {
            color: #000000 !important;
        }

        /* Hide Streamlit fullscreen button */
        button[title="View fullscreen"] {
            display: none;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# Header Card Markup
st.markdown(
    """
    <div class="header-card">
        <h3>🤖 VMY2026 AI Assistant</h3>
        <p>Ask about arrival forecasts, hotel occupancy, or spending metrics</p>
    </div>
""",
    unsafe_allow_html=True,
)

# Initialize OpenAI/Gonka Client using Streamlit Secrets
GONKA_BASE_URL = "https://api.gonkarouter.io/v1"
GONKA_API_KEY = st.secrets["GONKA_API_KEY"]

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

# Maintain conversation history with an initial greeting
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! I am your VMY2026 AI Assistant. Ask me anything about tourism arrivals, hotel occupancy, or strategy forecasts!",
        }
    ]

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
