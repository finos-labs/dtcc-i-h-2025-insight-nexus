import streamlit as st
from components.upload_component import upload_pdf
from components.compare_component import upload_and_extract_two_pdfs
from services.comparator import compare_documents
from services.summarizer import summarize_pdf_and_create_vectorstore
from services.impact_summary import generate_impact_summary_and_vectorstore
from services.chatbot import process_pdf_and_ask
from services.qa_llm import run_qa_on_vectorstore
from services.compare_qa import qa_on_comparison


st.set_page_config(
    page_title="DTCC AI Assistant", layout="wide", initial_sidebar_state="collapsed"
)

st.markdown(
    """
    <style>
    .stApp {
        background: 
            linear-gradient(to bottom right, #0a101b, #020510),
            radial-gradient(at top left, #0a101b, transparent 70%),
            radial-gradient(at top right, #050b14, transparent 70%),
            radial-gradient(at bottom left, #050b14, transparent 70%),
            radial-gradient(at bottom right, #020510, transparent 70%);
        background-blend-mode: screen;
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
        color: #ffffff;
        font-family: Arial, sans-serif;
    }
    .stButton>button {
        background-color: rgb(25 51 83 / 30%);
        color: white;
        border-radius: 8px;
        height: 3em;
        width: 100%;
        margin: 0.25em 0;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #21867a;
        color: white;
        transform: scale(1.02);
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("💼 Compliance Regulation Assistant")

features = {
    "Compliance Regulation Brief": "Summarize a single document and ask questions",
    "CompReg Variance": "Compare two versions of compliance regulation documents",
    "Stakeholder Impact Summary": "Generate impact summary and ask questions",
    "RegDoc QueryTalk": "Chat with the uploaded document directly",
}

st.subheader("📌 Select a Feature")
selected_feature = st.session_state.get("selected_feature", None)
cols = st.columns(len(features))

for i, (feature, desc) in enumerate(features.items()):
    with cols[i]:
        if st.button(
            f"{['📘', '📋', '📊', '💬'][i]} {feature}", use_container_width=True
        ):
            st.session_state.selected_feature = feature
            st.session_state.uploaded_file = None
            st.session_state.uploaded_files = None
            st.session_state.vectorstore = None
            st.session_state.impact_vectorstore = None

selected = st.session_state.get("selected_feature")

if selected:
    st.markdown("---")
    st.subheader("📄 Upload PDF(s)")
    if selected == "Compliance Regulation Brief":
        pdf_file = upload_pdf()
        if pdf_file:
            if st.button("📝 Summarize"):
                with st.spinner("Summarizing..."):
                    summary, vectorstore = summarize_pdf_and_create_vectorstore(
                        pdf_file
                    )
                    st.session_state.vectorstore = vectorstore
                    st.subheader("📄 Summary")
                    st.write(summary)
        if st.session_state.get("vectorstore"):
            question = st.text_input("Ask a question about the document summary")
            if question:
                with st.spinner("Getting answer..."):
                    answer = run_qa_on_vectorstore(
                        question, st.session_state["vectorstore"]
                    )
                    st.subheader("🤖 Answer")
                    st.write(answer)

    elif selected == "CompReg Variance":
        text1, text2 = upload_and_extract_two_pdfs()
        if text1 and text2:
            if st.button("🔍 Compare Documents"):
                with st.spinner("Comparing..."):
                    result = compare_documents(text1, text2)
                    st.subheader("🔁 Key Changes Summary")
                    st.write(result)
                    st.session_state["comparison_done"] = True

            st.markdown("---")

            if st.session_state.get("comparison_done"):
                st.subheader("💬 Ask Questions About Comparison")
                question = st.text_input("Ask your question here")
                if question:
                    with st.spinner("Getting answer..."):
                        response = qa_on_comparison(question, text1, text2)
                        st.markdown("**🤖 Bot's Answer**")
                        st.write(response)
        else:
            st.session_state["comparison_done"] = False

    elif selected == "Stakeholder Impact Summary":
        pdf_file = upload_pdf()
        if pdf_file:
            if st.button("📌 Generate Impact Summary"):
                with st.spinner("Generating impact summary..."):
                    summary, vectorstore = generate_impact_summary_and_vectorstore(
                        pdf_file
                    )
                    st.session_state.impact_vectorstore = vectorstore
                    st.subheader("📌 Impact Summary")
                    st.write(summary)
        if st.session_state.get("impact_vectorstore"):
            question = st.text_input("Ask a question about the impact summary")
            if question:
                with st.spinner("Getting answer..."):
                    answer = run_qa_on_vectorstore(
                        question, st.session_state["impact_vectorstore"]
                    )
                    st.subheader("🤖 Answer")
                    st.write(answer)

    elif selected == "RegDoc QueryTalk":
        pdf_file = st.file_uploader("", type=["pdf"])

        if pdf_file:
            st.success("✅ PDF uploaded. You can now ask your question.")
            question = st.text_input("Ask a question about the uploaded PDF")

            if question:
                with st.spinner("Getting response..."):
                    response = process_pdf_and_ask(pdf_file, question)
                    st.subheader("🤖 Bot's Answer")
                    st.write(response)
        else:
            st.info("📄 Please upload a PDF to begin chatting.")

else:
    st.info("👈 Please select a feature to begin.")
