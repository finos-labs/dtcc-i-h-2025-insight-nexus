import os
import boto3
import json
from dotenv import load_dotenv

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

def compare_documents(text1, text2):
    messages = [
        {
            "role": "user",
            "content": [
                {"text": f"""Compare the following two regulatory documents and summarize the key changes in bullet points:

Document 1 (Older):
{text1[:3000]}

Document 2 (Newer):
{text2[:3000]}

Avoid unnecessary details. Focus on policy, numbers, dates, names, or clauses that changed.
"""}
            ]
        }
    ]

    system_message = [
        {
            "text": "You are a compliance analyst helping identify critical updates between two government or corporate circulars."
        }
    ]

    try:
        response = bedrock_runtime.converse(
            modelId=MODEL_ID,
            messages=messages,
            system=system_message,
            inferenceConfig={
                "maxTokens": 1024,
                "temperature": 0.3
            }
        )

        return response['output']['message']['content'][0]['text']

    except Exception as e:
        return f"❌ Error comparing documents: {e}"
