
import streamlit as st
from llama_cpp import Llama

st.title("RAG PDF Chatbot")

llm = Llama(model_path="/mnt/models/llama/TinyLlama-1.1B-Chat-v1.0-GGUF")

def generate_answer(query):
    response = llm(prompt=query, max_tokens=256)
    return response["choices"][0]["text"]

user_input = st.text_input("Ask a question:")
if user_input:
    answer = generate_answer(user_input)
    st.write(answer)
