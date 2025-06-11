import os
import boto3
from dotenv import load_dotenv

load_dotenv()

aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
region = "us-east-1"

bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name=region,
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key
)

MODEL_ID = "us.anthropic.claude-3-5-haiku-20241022-v1:0"

def qa_on_comparison(question, text1, text2):
    prompt = f"""
You are a compliance analyst. Based on the following two regulatory documents, answer the user's question:

Document 1 (Older):
{text1[:3000]}

Document 2 (Newer):
{text2[:3000]}

User's question: {question}

Please answer clearly and concisely, focusing only on the differences or changes between the two documents.
"""

    messages = [
        {"role": "user", "content": [{"text": prompt}]}
    ]

    system_message = [
        {"text": "You are a helpful compliance analyst who answers questions about differences between two regulatory documents."}
    ]

    try:
        response = bedrock_runtime.converse(
            modelId=MODEL_ID,
            messages=messages,
            system=system_message,
            inferenceConfig={
                "maxTokens": 512,
                "temperature": 0.3
            }
        )
        return response['output']['message']['content'][0]['text']
    except Exception as e:
        return f"❌ Error answering question on comparison: {e}"
