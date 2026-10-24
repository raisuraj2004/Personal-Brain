"""
rag.py — Shared functions for searching your paper database and asking the
local LLM (via Ollama) to answer using the retrieved chunks.
"""

import requests
import chromadb
from sentence_transformers import SentenceTransformer

DB_FOLDER = "chroma_db"
OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3.1"

_embedder = None
_collection = None

GENERAL_QUESTION_PREFIXES = (
    "what is ",
    "what are ",
    "who is ",
    "who was ",
    "where is ",
    "when is ",
    "when was ",
    "why is ",
    "how do i ",
    "how can i ",
    "what should i ",
    "what is the best ",
)
PAPER_TERMS = (
    "paper", "papers", "document", "documents", "pdf", "excerpt",
    "source", "sources", "research", "study", "article", "according to",
    "from the paper", "in the paper", "in the document", "in my pdf",
    "in my paper", "from my document", "from the document", "page ", "pages",
    "finding", "findings", "result", "results", "methodology", "conclusion",
    "quote", "quoted", "mentioned in", "cited in"
)


def _get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=DB_FOLDER)
        _collection = client.get_or_create_collection("papers")
    return _collection


def search(question, top_k=3):
    """Returns the top_k most relevant chunks for a question, with sources."""
    embedder = _get_embedder()
    collection = _get_collection()

    query_embedding = embedder.encode([question]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=top_k)

    chunks = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    for text, meta in zip(docs, metas):
        chunks.append({"text": text, "paper": meta["paper"], "page": meta["page"]})
    return chunks


def build_prompt(question, chunks):
    context = "\n\n".join(
        f"[Source: {c['paper']}, page {c['page']}]\n{c['text']}" for c in chunks
    )
    return f"""You are a helpful research assistant. Answer every part of the question.
For claims about the uploaded papers, use the excerpts below and cite the paper and page number.
If the excerpts do not contain a document-specific answer, say so honestly instead of guessing.
If the user also asks a general-knowledge or recommendation question, answer that part using your
general knowledge and clearly label it as general information rather than pretending it came from a paper.

Use concise headings when the question has both a paper-specific part and a general part.

EXCERPTS:
{context}

QUESTION: {question}

ANSWER:"""


def is_general_question(question):
    """Returns True for short questions that do not need the paper database."""
    normalized = " ".join(question.lower().split())
    return (
        len(normalized.split()) <= 18
        and normalized.endswith("?")
        and normalized.startswith(GENERAL_QUESTION_PREFIXES)
        and not any(term in normalized for term in PAPER_TERMS)
    )


def question_needs_papers(question):
    """Returns True when the wording asks for information from uploaded documents."""
    normalized = " ".join(question.lower().split())

    if any(term in normalized for term in PAPER_TERMS):
        return True

    if any(phrase in normalized for phrase in (
        "what does the paper say",
        "summarize this paper",
        "summarize the paper",
        "key findings in the document",
        "what are the findings",
        "explain the results",
    )):
        return True

    return False


def ask_general_question(question, model):
    prompt = f"""Answer this general knowledge question accurately and concisely.
If it is subjective, say that clearly and give a few useful examples.
Do not mention papers, excerpts, or this prompt.
Question: {question}
Answer:"""
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "10m",
            "options": {
                "num_predict": 96,
                "temperature": 0.1,
            },
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["response"].strip()


def ask(question, model=DEFAULT_MODEL, top_k=3):
    """Routes simple questions to the model and document questions to retrieval.
    Returns (answer_text, list_of_source_chunks)."""
    if not question or not question.strip():
        return "Please ask a question.", []

    normalized = " ".join(question.lower().split())
    if not question_needs_papers(normalized):
        return ask_general_question(question, model), []

    collection = _get_collection()
    if collection.count() == 0:
        return ask_general_question(
            f"{question} (Answer from general knowledge if no uploaded papers are available.)",
            model,
        ), []

    chunks = search(question, top_k=top_k)
    if not chunks:
        return ask_general_question(question, model), []

    prompt = build_prompt(question, chunks)
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "10m",
            "options": {
                "num_predict": 256,
                "temperature": 0.2,
            },
        },
        timeout=300,
    )
    response.raise_for_status()
    answer = response.json()["response"]
    return answer, chunks
