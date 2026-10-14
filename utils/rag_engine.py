import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

def build_vector_store(text):
    print("Building vector store...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", "|", " "]
    )
    chunks = splitter.split_text(text)
    print(f"Created {len(chunks)} chunks")
    
    embeddings = get_embeddings()
    vector_store = FAISS.from_texts(chunks, embeddings)
    print("Vector store ready!")
    return vector_store, chunks

def retrieve_context(vector_store, query, k=6):
    docs = vector_store.similarity_search(query, k=k)
    context = "\n\n".join([doc.page_content for doc in docs])
    return context

def ask_finwise(vector_store, question, chat_history=None):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    context = retrieve_context(vector_store, question)
    
    history_text = ""
    if chat_history:
        for msg in chat_history[-4:]:
            role = "User" if msg["role"] == "user" else "FinWise"
            history_text += f"{role}: {msg['content']}\n"
    
    system_prompt = """You are FinWise AI — an intelligent financial assistant.
You help users understand their personal finance data including transactions, spending patterns, and budgets.

RULES:
1. Only answer based on the provided financial data context
2. Always cite specific numbers, dates, and amounts when available
3. If asked about something not in the data, say "I don't have that information in your financial data"
4. Format currency as $ with 2 decimal places
5. Be concise, specific, and helpful
6. When identifying trends, reference specific months or categories
7. Never make up financial advice or numbers not in the data
8. When asked about "expenses", "top expenses", or "biggest purchases", look for the highest individual debit transaction amounts in the data
9. Format top expenses as a numbered list with date, description, amount and category
"""
    
    user_message = f"""Financial Data Context:
{context}

{f"Previous conversation:{chr(10)}{history_text}" if history_text else ""}

User Question: {question}

Answer based strictly on the financial data provided above."""
    
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.1,
        max_tokens=800,
    )
    
    return response.choices[0].message.content.strip()