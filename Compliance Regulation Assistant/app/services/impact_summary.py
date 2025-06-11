import os
import boto3
import tempfile
from dotenv import load_dotenv
from pypdf import PdfReader
from services.create_vector_store import create_vectorstore_from_pdf

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

def generate_impact_summary_and_vectorstore(pdf_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_file.read())
        tmp_path = tmp.name

    impact_summary = generate_impact_summary_with_citations(tmp_path)

    vectorstore = create_vectorstore_from_pdf(open(tmp_path, "rb"))

    return impact_summary, vectorstore


def generate_impact_summary_with_citations(pdf_path):
    reader = PdfReader(pdf_path)
    full_text = ""
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if text:
            full_text += f"\n--- Page {i} ---\n{text}\n"

    messages = [
        {
            "role": "user",
            "content": [{
                "text": f"""
You are a FinTech Policy Impact Analyst.

Your task is to analyze regulatory or compliance documents and produce a clear, **real-world impact summary** for FinTech judges and stakeholders.

Focus on:
- **How individuals are affected and explain with examples and normal life scenario and use simple english (e.g., retail investors, brokers, compliance officers, etc.)**
- **What behavioral or operational changes** are required
- **Costs, workload, risks**, and **strategic shifts**
- **Translate technical policy into human terms** and **summarize impact in bullet points**
- **For each bullet point, mention the page number where the information can be found** in this format: (Page X)
- **Make it explain to a normal individual who is not very good at high level english and who knows nothing about finance**

Be specific and concrete. Example:
Instead of saying “Margin requirements increase,” say:
“Retail investors will need to deposit more funds upfront. This may reduce the number of trades by small investors & increase compliance workload for brokers.”

Now, analyze the following document and generate an **Impact Summary**:\n\n{full_text}
                """
            }]
        }
    ]

    system_message = [{
        "text": "You are a policy-to-impact translation engine. Your job is to turn regulation text into human-centric bullet points with behavioral, financial, and operational consequences. Add page numbers for each point."
    }]

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
        return f"Error during impact analysis: {e}"
