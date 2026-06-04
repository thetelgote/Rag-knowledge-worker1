# from langchain_community.vectorstores import FAISS
# from langchain_huggingface import HuggingFaceEmbeddings
# from pathlib import Path
# import ollama

# embeddings = HuggingFaceEmbeddings(
#     model_name="sentence-transformers/all-MiniLM-L6-v2"
# )

# BASE_DIR = Path(__file__).resolve().parent.parent

# db = FAISS.load_local(
#     str(BASE_DIR / "faiss_index"),
#     embeddings,
#     allow_dangerous_deserialization=True
# )


# def answer_question(question, history=None):

#     if history is None:
#         history = []

#     # 🔥 Step 1: Get many docs
#     docs = db.similarity_search(question, k=10)

#     question_lower = question.lower()

#     # 🔥 Step 2: PRIORITY MATCH (company name in filename)
#     priority_docs = [
#         d for d in docs
#         if any(word in d.metadata.get("filename", "")
#                for word in question_lower.split())
#     ]

#     # 🔥 Step 3: CONTENT MATCH (fallback)
#     content_docs = [
#         d for d in docs
#         if question_lower in d.page_content.lower()
#     ]

#     # 🔥 Final selection
#     if priority_docs:
#         docs = priority_docs[:5]
#     elif content_docs:
#         docs = content_docs[:5]
#     else:
#         docs = docs[:3]

#     context_text = "\n\n".join([d.page_content for d in docs])

#     prompt = f"""
# You are an AI assistant.

# STRICT RULES:
# - Answer ONLY from context
# - If company name is mentioned, prioritize that company
# - Do NOT use unrelated data
# - If not found, say "I don't know"

# Context:
# {context_text}

# Question:
# {question}
# """

#     response = ollama.chat(
#         model="phi3",
#         messages=[{"role": "user", "content": prompt}]
#     )

#     answer = response["message"]["content"]

#     return answer, docs

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def answer_question(question, history=None):

    if history is None:
        history = []

    # Load only when user asks a question
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    db = FAISS.load_local(
        str(BASE_DIR / "faiss_index"),
        embeddings,
        allow_dangerous_deserialization=True
    )

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0
    )

    docs = db.similarity_search(question, k=10)

    question_lower = question.lower()

    priority_docs = [
        d for d in docs
        if any(
            word in d.metadata.get("filename", "")
            for word in question_lower.split()
        )
    ]

    content_docs = [
        d for d in docs
        if question_lower in d.page_content.lower()
    ]

    if priority_docs:
        docs = priority_docs[:5]
    elif content_docs:
        docs = content_docs[:5]
    else:
        docs = docs[:3]

    context_text = "\n\n".join(
        [d.page_content for d in docs]
    )

    prompt = f"""
You are an AI assistant.

STRICT RULES:
- Answer ONLY from the provided context.
- If company name is mentioned, prioritize that company.
- Do NOT use outside knowledge.
- If answer is unavailable, say "I don't know".

Context:
{context_text}

Question:
{question}
"""

    response = llm.invoke(prompt)

    answer = response.content

    return answer, docs
