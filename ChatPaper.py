import streamlit as st
import requests
import base64
import json
import re

# ================= CONFIG =================

st.set_page_config(page_title="ChatPaper", layout="wide")

# ================= CSS =================

st.markdown("""
<style>

/* GLOBAL */
body {
    background-color: #0F172A;
}

/* USER MESSAGE */
.user-msg {
    background-color: #2563EB;
    color: white;
    padding: 14px;
    border-radius: 14px;
    margin-bottom: 12px;
    font-size: 15px;
    width: fit-content;
    max-width: 70%;
    margin-left: auto;
}

/* AI MESSAGE */
.ai-msg {
    background-color: #1E293B;
    color: #E2E8F0;
    padding: 16px;
    border-radius: 14px;
    margin-bottom: 12px;
    font-size: 15px;
    max-width: 75%;
}

/* CHAT INPUT */
.chat-input {
    position: fixed;
    bottom: 20px;
    width: 70%;
}

</style>
""", unsafe_allow_html=True)

API_KEY = "secret123"

api = "https://earline-exchangeable-wei.ngrok-free.dev/"

SUMMARY_API = api+"summary"
QA_API = api+"q&a"
DIAGRAM_API = api+"diagram_explanation"
EQUATIONS_API = api+"equations"


HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# ================= SESSION =================

if "page" not in st.session_state:
    st.session_state.page = "home"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ================= UTILS =================

def encode_pdf(uploaded_file):
    return base64.b64encode(uploaded_file.read()).decode()


def safe_post(url, payload):
    try:
        res = requests.post(url, headers=HEADERS, json=payload, timeout=600)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return None


def clean_text(text):
    if not text:
        return ""

    lines = text.split("\n")
    unique = list(dict.fromkeys(line.strip() for line in lines if line.strip()))
    text = "\n".join(unique)
    text = text.replace("### Summary of Key Results", "")
    return text


def format_summary(summary_dict):
    for key, content in summary_dict.items():
        content = clean_text(content)
        with st.expander(f"📌 {key.title()}", expanded=True):
            st.markdown(content)

# ================= SIDEBAR =================

with st.sidebar:
    st.title("📘 ChatPaper")

    if st.button("🏠 Home", use_container_width=True):
        st.session_state.page = "home"

    if st.button("📄 Summarization", use_container_width=True):
        st.session_state.page = "summary"

    if st.button("📊 Diagram Explanation", use_container_width=True):
        st.session_state.page = "diagram"    

    if st.button("📐 Mathematical Equations", use_container_width=True):
        st.session_state.page = "equations"

    
    if st.button("❓ Question Answering (Chatbot)", use_container_width=True):
        st.session_state.page = "qa"

page = st.session_state.page

# ================= HOME =================

if page == "home":
    st.title("📘 ChatPaper – AI Research Assistant")

    st.markdown("""
    ### Features
    - 📄 Paper Summarization
    - 📊 Diagram Explanation
    - 📐 Equation Extraction & Explanation
    - ❓ Question Answering (Chatbot)

    ### Tech Stack
    FastAPI • Streamlit • LangChain • LLMs
    """)

# ================= SUMMARY PAGE =================

elif page == "summary":

    st.title("📄 Research Paper Summarization")

    
    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None

    if "summary" not in st.session_state:
        st.session_state.summary = None

    file = st.file_uploader("Upload PDF", type="pdf", key="uploader")

    
    if file is not None:
        if st.session_state.uploaded_file != file:
            st.session_state.uploaded_file = file
            st.session_state.summary = None  

    if st.button("Summarize Paper"):

        if not st.session_state.uploaded_file:
            st.warning("Upload a PDF first")
        else:
            payload = {"pdf_file": encode_pdf(st.session_state.uploaded_file)}

            with st.spinner("🤖 AI is reading the paper..."):
                data = safe_post(SUMMARY_API, payload)

            if data:
                st.success("✅ Summary Generated Successfully!")
                st.session_state.summary = data.get("summary", data)

   
    if st.session_state.summary:
        format_summary(st.session_state.summary)


# ================= DIAGRAM PAGE =================

elif page == "diagram":
    st.title("📊 Diagram Explanation")

    if "uploaded_file" not in st.session_state or st.session_state.uploaded_file is None:
        st.warning("⚠️ Please upload a PDF in the Summary page first.")
    else:

        if "figures_data" not in st.session_state:
            st.session_state.figures_data = None

        if st.button("Extract Figures & Explain from uploaded PDF"):

            payload = {"pdf_file": encode_pdf(st.session_state.uploaded_file)}

            with st.spinner("🤖 Extracting figures and generating explanations..."):
                data = safe_post(DIAGRAM_API, payload)

            if data:
                if "figures" in data and len(data["figures"]) > 0:
                    st.success(f"✅ Extracted {len(data['figures'])} figures!")
                    st.session_state.figures_data = data["figures"]
                elif "error" in data:
                    st.error(data["error"])
                else:
                    st.error("No figures returned from API.")
            else:
                st.error("API request failed completely.")

        if st.session_state.figures_data:
            for fig in st.session_state.figures_data:
                fig_num = fig["figure_number"]
                fig_image = fig["figure_image"]
                explanation = fig["explanation"]

                st.image(base64.b64decode(fig_image), caption=f"Figure {fig_num}", width="stretch" )
                st.markdown(f"**Explanation for Figure {fig_num}:**\n{explanation}")
                st.divider()

# ================= EQUATION PAGE =================

elif page == "equations":
    st.title("📐 Equation Extraction & Explanation")

    if "uploaded_file" not in st.session_state or st.session_state.uploaded_file is None:
        st.warning("⚠️ Please upload a PDF in the Summary page first.")
    else:

        if "equations_data" not in st.session_state:
            st.session_state.equations_data = None

        if st.button("Extract Equations & Generate LaTeX/Explanation"):

            payload = {"pdf_file": encode_pdf(st.session_state.uploaded_file)}

            with st.spinner("🤖 Extracting equations and generating explanations..."):
                data = safe_post("https://earline-exchangeable-wei.ngrok-free.dev/equation_explanation", payload)

            if data:
                if "equations" in data and len(data["equations"]) > 0:
                    st.success(f"✅ Extracted {len(data['equations'])} equations!")
                    st.session_state.equations_data = data["equations"]
                elif "error" in data:
                    st.error(data["error"])
                else:
                    st.error("No equations returned from API.")
            else:
                st.error("API request failed completely.")

       
        if st.session_state.equations_data:
            for idx, eq in enumerate(st.session_state.equations_data, 1):
                st.markdown(f"**Equation {idx} (Page {eq['page_number']}):**")
                
                # Render LaTeX
                if eq.get("latex"):
                    st.latex(eq["latex"])
                else:
                    st.write(eq["equation_text"])

                # Show explanation
                st.markdown(f"**Explanation:** {eq['explanation']}")
                st.divider()

# ================= QA PAGE ================= 

elif page == "qa":

    st.title("💬 Ask Questions About Paper")

    # ===== INIT STATES =====
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # ===== FUNCTION SEND =====
    def send_message():
        question = st.session_state.input_question.strip()

        if not question:
            return

        # Call API
        response = safe_post(QA_API, {"question": question})
        answer = response.get("answer", "No answer returned") if response else "Error occurred"

        # Store question-answer pair as a single entry
        st.session_state.chat_history.append({"question": question, "answer": answer})

        # Clear input
        st.session_state.input_question = ""

    # ===== DISPLAY CHAT =====
    for qa in st.session_state.chat_history:
        st.markdown(f'<div class="user-msg"><b>Question:</b> {qa["question"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="ai-msg"><b>Answer:</b> {qa["answer"]}</div>', unsafe_allow_html=True)

    st.divider()

    # ===== INPUT AREA =====
    col1, col2 = st.columns([6,1])

    with col1:
        st.text_input(
            "Type your question",
            key="input_question",
            placeholder="Ask anything about the paper...",
            on_change=send_message   
        )

    with col2:
        st.button("Send", on_click=send_message)