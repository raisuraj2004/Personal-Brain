
import os
import pymupdf
import chromadb
from sentence_transformers import SentenceTransformer

PAPERS_FOLDER = "papers"
DB_FOLDER = "chroma_db"
CHUNK_SIZE = 700 
CHUNK_OVERLAP = 100


def extract_pages(pdf_path):
    """Returns a list of (page_number, text) tuples for a PDF """
    doc = pymupdf.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text()
        if text.strip():
            pages.append((i + 1, text))
    doc.close()
    return pages


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Splits text into overlapping word chunks."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def main():
    if not os.path.isdir(PAPERS_FOLDER):
        os.makedirs(PAPERS_FOLDER)
        print(f"Created '{PAPERS_FOLDER}/' — put your PDF papers in there and re-run this script.")
        return

    pdf_files = [f for f in os.listdir(PAPERS_FOLDER) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print(f"No PDFs found in '{PAPERS_FOLDER}/'. Add some and re-run.")
        return

    print("Loading embedding model (first run downloads it, ~90MB)...")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")

    client = chromadb.PersistentClient(path=DB_FOLDER)
    collection = client.get_or_create_collection("papers")

    total_chunks = 0
    for filename in pdf_files:
        path = os.path.join(PAPERS_FOLDER, filename)
        print(f"Processing {filename}...")
        pages = extract_pages(path)

        ids, texts, metadatas = [], [], []
        for page_num, page_text in pages:
            for j, chunk in enumerate(chunk_text(page_text)):
                chunk_id = f"{filename}_p{page_num}_c{j}"
                ids.append(chunk_id)
                texts.append(chunk)
                metadatas.append({
                    "paper": filename,
                    "page": page_num,
                })

        if not texts:
            print(f"  No extractable text in {filename} (it might be scanned/image-based).")
            continue

        embeddings = embedder.encode(texts, show_progress_bar=False).tolist()
        collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
        total_chunks += len(texts)
        print(f"  Added {len(texts)} chunks from {filename}")

    print(f"\nDone. {total_chunks} chunks stored in '{DB_FOLDER}/'.")


if __name__ == "__main__":
    main()
