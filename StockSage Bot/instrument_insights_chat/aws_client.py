import boto3
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

# Initializing AWS Bedrock client
bedrock = boto3.client(
    "bedrock-runtime",
    region_name="us-east-1",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)