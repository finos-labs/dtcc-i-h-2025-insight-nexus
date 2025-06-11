import tempfile
import boto3

from langchain_community.embeddings import BedrockEmbeddings
from langchain.llms.bedrock import Bedrock
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

bedrock = boto3.client(service_name="bedrock-runtime",region_name="us-east-1")

bedrock_embeddings = BedrockEmbeddings(
    model_id="amazon.titan-embed-text-v2:0", client=bedrock
)

def get_claude_llm():
    return Bedrock(
        model_id="anthropic.claude-v2:1",
        client=bedrock,
        model_kwargs={"max_tokens_to_sample": 512, "temperature": 0.2}
    )

PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are a legal compliance assistant analyzing official SEC documents. Use the context below to answer the user's question professionally and concisely.

Instructions:
- If the answer is clearly stated in the context, provide it confidently and cite relevant page numbers (e.g., "Page 2").
- Only include the fallback line — "This is the only related information found in the document." — if the context provides fewer than 3 distinct points or if the content appears incomplete or ambiguous. If your response contains clearly stated bullet points covering the user's query, do not include any fallback line.
- If the context contains no relevant information, your entire response must be: "The document does not mention anything relevant to your question." Do not include any additional explanation or citations.
- Never make up information or speculate.
- Do not cite pages unless they directly support the answer.
- Keep responses under 100 words unless more detail is truly necessary.

Context:
{context}

Question: {question}

Answer:
"""
)


def process_pdf_and_ask(pdf_file, question):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(pdf_file.read())
        loader = PyPDFLoader(tmp_file.name)
        documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=300)
    docs = splitter.split_documents(documents)
    vectorstore = FAISS.from_documents(docs, bedrock_embeddings)

    qa = RetrievalQA.from_chain_type(
        llm=get_claude_llm(),
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
        return_source_documents=True,  
        chain_type_kwargs={"prompt": PROMPT}
    )

    result = qa({"query": question})
    answer = result["result"]
    source_docs = result["source_documents"]

    answer_clean = answer.strip().lower()

    if "the document does not mention anything relevant to your question" in answer_clean:
        return answer.strip()

    citations = []
    for doc in source_docs:
        metadata = doc.metadata
        page_number = metadata.get("page", None)
        if page_number is not None:
            citations.append(f"Page {page_number + 1}")

    unique_citations = sorted(set(citations))
    citation_text = "📚 Cited from: " + ", ".join(unique_citations) if unique_citations else ""

    return f"{answer.strip()}\n\n{citation_text}"
