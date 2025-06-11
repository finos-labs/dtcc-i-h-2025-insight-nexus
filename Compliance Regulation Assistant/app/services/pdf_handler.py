import fitz  
from typing import Tuple

def extract_text_from_pdf(uploaded_file) -> Tuple[str, str]:
    """
    Extract text from uploaded PDF using PyMuPDF.
    Returns:
        full_text: Cleaned, concatenated text
        status: Message to display to the user
    """
    try:
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        full_text = ""
        for page in doc:
            text = page.get_text().strip()
            if text:
                full_text += text + "\n"
        
        if not full_text.strip():
            return "", "⚠️ No extractable text found. Is it a scanned image PDF?"

        return full_text, "✅ Text extracted successfully!"
    
    except Exception as e:
        return "", f"❌ Error: {str(e)}"
