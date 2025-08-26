from langchain_chroma import Chroma  # Updated import
from langchain_core.documents import Document
from langchain.chains import RetrievalQA
from langchain_community.llms import OpenAI
from langchain_ollama import OllamaLLM  # Updated import
from langchain.prompts import PromptTemplate
from .embeddings import get_embeddings
import os


def get_llm():
    provider = os.getenv("LLM_PROVIDER", "ollama")

    if provider == "openai":
        return OpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    else:
        return OllamaLLM(model=os.getenv("OLLAMA_MODEL", "mistral"))  # Updated class


def generate_embeddings(chunks):
    documents = []
    for chunk in chunks:
        doc = Document(
            page_content=chunk["text"],
            metadata={
                "start_time": chunk["start_time"],
                "end_time": chunk["end_time"]
            }
        )
        documents.append(doc)
    return documents


def store_embeddings(documents, user_id, transcript_id):
    vectorstore = Chroma.from_documents(  # This should now use the updated import
        documents=documents,
        embedding=get_embeddings(),
        persist_directory=os.getenv("CHROMA_DIR", "./data/chroma"),
        collection_name=f"{user_id}_{transcript_id}"
    )
    return vectorstore


def process_query(user_id, transcript_id, query):
    vectorstore = Chroma(
        collection_name=f"{user_id}_{transcript_id}",
        persist_directory=os.getenv("CHROMA_DIR", "./data/chroma"),
        embedding_function=get_embeddings()
    )

    # Create a custom prompt for better results
    prompt_template = """Use the following pieces of context to answer the question at the end. 
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    Include timestamps from the context in your answer where relevant.

    {context}

    Question: {question}
    Answer with timestamps:"""

    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=get_llm(),
        chain_type="stuff",
        retriever=vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4}
        ),
        chain_type_kwargs={"prompt": PROMPT},
        return_source_documents=True
    )

    result = qa_chain.invoke({"query": query})

    # Extract timestamps from source documents
    timestamps = []
    for doc in result["source_documents"]:
        if "start_time" in doc.metadata and "end_time" in doc.metadata:
            timestamps.append({
                "start": doc.metadata["start_time"],
                "end": doc.metadata["end_time"]
            })

    return {
        "answer": result["result"],
        "timestamps": timestamps,
        "source_chunks": [doc.page_content for doc in result["source_documents"]]
    }