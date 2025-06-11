import streamlit as st
import fitz  

def upload_and_extract_two_pdfs():
    col1, col2 = st.columns(2)

    with col1:
        pdf1 = st.file_uploader("Upload First PDF (Older)", type=["pdf"], key="pdf1")
    with col2:
        pdf2 = st.file_uploader("Upload Second PDF (Newer)", type=["pdf"], key="pdf2")

    text1, text2 = None, None

    if pdf1 and pdf2:
        try:
            text1 = ""
            with fitz.open(stream=pdf1.read(), filetype="pdf") as doc1:
                for page in doc1:
                    text1 += page.get_text()

            text2 = ""
            with fitz.open(stream=pdf2.read(), filetype="pdf") as doc2:
                for page in doc2:
                    text2 += page.get_text()

        except Exception as e:
            st.error(f"Error reading PDFs: {e}")

    return text1.strip() if text1 else None, text2.strip() if text2 else None
