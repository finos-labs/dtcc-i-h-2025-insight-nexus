import boto3
from langchain.chains import RetrievalQA
from langchain.llms.bedrock import Bedrock
from langchain.prompts import PromptTemplate

bedrock = boto3.client(service_name="bedrock-runtime", region_name="us-east-1")
PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are a legal compliance assistant analyzing official SEC documents. Use the context below to answer the user's question professionally and concisely.

Instructions:
- If the answer is clearly stated in the context, provide it confidently and cite relevant page numbers (e.g., "Page 2").
- Only include the fallback line — "This is the only related information found in the document." — if the context provides fewer than 3 distinct points or if the content appears incomplete or ambiguous. If your response contains clearly stated bullet points covering the user's query, do not include any fallback line.
- If the context contains no relevant information, your entire response must be: "The document does not mention anything relevant to your question." Do not include any additional explanation or citations.
- If you say the answer is not available, do not include any citations or unnecessary explanation.
- Never make up information or speculate.
- Do not cite pages unless they directly support the answer.
- Keep responses under 100 words unless more detail is truly necessary.

Context:
{context}

Question: {question}

Answer:
"""
)

def get_claude_llm():
    return Bedrock(
        model_id="anthropic.claude-v2:1",
        client=bedrock,
        model_kwargs={"max_tokens_to_sample": 512, "temperature": 0.2}
    )

def run_qa_on_vectorstore(question, vectorstore, with_citations=True):
    qa = RetrievalQA.from_chain_type(
        llm=get_claude_llm(),
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 10}),
        return_source_documents=with_citations,
        chain_type_kwargs={"prompt": PROMPT}
    )
    result = qa(question)
    answer = result['result']
    
    if with_citations:
        if "the document does not mention anything relevant to your question" in answer.strip().lower():
            return answer.strip()

        
        sources = result['source_documents']
        pages = set()
        for doc in sources:
            page = doc.metadata.get("page")
            if page is not None:
                pages.add(f"Page {int(page)+1}")

        if pages:
            answer += f"\n\n(Citations from pages: {', '.join(sorted(pages))})"
    
    return answer
