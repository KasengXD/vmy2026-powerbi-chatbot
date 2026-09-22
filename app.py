import streamlit as st
from openai import OpenAI

# Page configuration for embedding inside Power BI
st.set_page_config(page_title="VMY2026 AI Assistant", layout="centered")

# Custom CSS for Power BI Purple Theme & Clean Layout
st.markdown(
    """
    <style>
        /* Reduce padding to maximize space inside the Power BI iframe */
        .block-container { 
            padding-top: 0.5rem; 
            padding-bottom: 0.5rem; 
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
        
        /* Hide default Streamlit header & footer */
        header { visibility: hidden; }
        footer { visibility: hidden; }
        
        /* Match Power BI canvas purple background */
        .stApp {
            background-color: #B5A1DB;
        }

        /* Clean white chat bubbles */
        [data-testid="stChatMessage"] {
            background-color: #FFFFFF;
            border-radius: 10px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        /* Clean chat input box */
        [data-testid="stChatInput"] {
            border-radius: 8px;
            background-color: #FFFFFF;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# Visible Title inside the Chatbot Frame
st.markdown("### 🤖 VMY2026 AI Assistant")
st.caption("Ask questions about arrivals, hotel occupancy, or tourism spending.")

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