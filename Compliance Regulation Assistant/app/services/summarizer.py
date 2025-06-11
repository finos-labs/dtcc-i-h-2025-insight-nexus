import os
import boto3
from dotenv import load_dotenv
from pypdf import PdfReader
from services.create_vector_store import create_vectorstore_from_pdf
from io import BytesIO

load_dotenv()

aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
region = "us-east-1"

MODEL_ID = "us.anthropic.claude-3-5-haiku-20241022-v1:0"

bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name=region,
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key
)

def summarize_pdf_with_citations(pdf_file):
    reader = PdfReader(pdf_file)
    full_text = ""
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if text:
            full_text += f"\n--- Page {i} ---\n{text}\n"

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "text": f"Please summarize this compliance document in simple, easy language. For each key point, mention the page number where that information is found, like this:\n- [Summary point] (Page X)\n\nDocument:\n{full_text}"
                }
            ]
        }
    ]

    system_message = [
        {
            "text": "You are a compliance expert assistant. Summarize long financial or regulatory documents into clear, concise points without legal jargon. For each point, add the page number where the info appears."
        }
    ]

    try:
        response = bedrock_runtime.converse(
            modelId=MODEL_ID,
            messages=messages,
            system=system_message,
            inferenceConfig={
                "maxTokens": 2048,
                "temperature": 0.7
            }
        )

        return response['output']['message']['content'][0]['text']

    except Exception as e:
        return f"Error during summarization: {e}"


def summarize_pdf_and_create_vectorstore(pdf_file):
    pdf_bytes = pdf_file.read()
    pdf_for_summary = BytesIO(pdf_bytes)
    pdf_for_vectorstore = BytesIO(pdf_bytes)

    summary = summarize_pdf_with_citations(pdf_for_summary)
    vectorstore = create_vectorstore_from_pdf(pdf_for_vectorstore)

    return summary, vectorstore
