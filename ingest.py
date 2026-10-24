
import os

import pymupdf
import chromadb
from PIL import Image
import pytesseract
from sentence_transformers import SentenceTransformer

PAPERS_FOLDER = "papers"
DB_FOLDER = "chroma_db"
CHUNK_SIZE = 700 
CHUNK_OVERLAP = 100
OCR_DPI = 200
OCR_LANGUAGE = "eng"
TESSERACT_CMD = os.environ.get(
    "TESSERACT_CMD",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
)


def _ocr_page(page):
    """Extract text from an image-only PDF page with local Tesseract OCR."""
    if TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

    pixmap = page.get_pixmap(
        matrix=pymupdf.Matrix(OCR_DPI / 72, OCR_DPI / 72),
        alpha=False,
    )
    image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
    try:
        return pytesseract.image_to_string(image, lang=OCR_LANGUAGE).strip()
    except pytesseract.TesseractNotFoundError as error:
        raise RuntimeError(
            "OCR requires Tesseract. Install Tesseract and add it to PATH, "
            "or set the TESSERACT_CMD environment variable to its executable."
        ) from error


def extract_pages(pdf_path):
    """Return page text, using OCR when a page has no text layer."""
    doc = pymupdf.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text()
        if not text.strip():
            text = _ocr_page(page)
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
