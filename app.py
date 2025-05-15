import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
from sentence_transformers import SentenceTransformer
from llama_cpp import Llama
import numpy as np

# --- Custom Wrapper to Make SentenceTransformer Compatible with LangChain ---
class LocalEmbeddingModel(Embeddings):
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts):
        return [np.array(embedding) for embedding in self.model.encode(texts, convert_to_numpy=True)]

    def embed_query(self, text):
        return self.model.encode(text, convert_to_numpy=True)

@st.cache_resource
def load_llama_model():
    return Llama(model_path="./models/llama-2-7b-chat.Q4_K_M.gguf", n_ctx=2048, n_threads=4)

@st.cache_resource
def load_embedding_model():
    return LocalEmbeddingModel()

# --- Updated: Use PyPDF2 Instead of fitz ---
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text

def create_vector_store(text, embed_model):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    docs = splitter.create_documents([text])
    faiss_index = FAISS.from_documents(docs, embed_model)
    return faiss_index, docs

def generate_answer(llm, question, context):
    prompt = f"""### Instruction:
You are an assistant. Use the following context to answer the question.
Context:
{context}

Question: {question}

Answer:"""
    response = llm(prompt, max_tokens=256, stop=["\n\n", "</s>"])
    return response["choices"][0]["text"].strip()

# --- Streamlit UI ---
st.title("🦙 LLaMA-based RAG PDF Chatbot")
uploaded_pdf = st.file_uploader("Upload PDF", type="pdf")
user_query = st.text_input("Ask a question:")

if uploaded_pdf:
    with st.spinner("Processing PDF..."):
        text = extract_text_from_pdf(uploaded_pdf)
        embed_model = load_embedding_model()
        vector_store, docs = create_vector_store(text, embed_model)
        st.success("PDF processed!")

    if user_query:
        with st.spinner("Generating answer..."):
            llama_model = load_llama_model()
            docs = vector_store.similarity_search(user_query, k=3)
            context = "\n".join([doc.page_content for doc in docs])
            answer = generate_answer(llama_model, user_query, context)
            st.markdown("**Answer:**")
            st.write(answer)
