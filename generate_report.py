from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUTPUT = Path("PersonalAgent_Project_Report.pdf")


def page_footer(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D6DEE8"))
    canvas.line(0.7 * inch, 0.55 * inch, 7.55 * inch, 0.55 * inch)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#617083"))
    canvas.drawString(0.7 * inch, 0.35 * inch, "PersonalAgent | Local Research RAG")
    canvas.drawRightString(7.55 * inch, 0.35 * inch, f"Page {document.page}")
    canvas.restoreState()


def make_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=28, leading=33, textColor=colors.HexColor("#17324D"),
        alignment=TA_CENTER, spaceAfter=14,
    ))
    styles.add(ParagraphStyle(
        name="Subtitle", parent=styles["Normal"], fontName="Helvetica",
        fontSize=13, leading=19, textColor=colors.HexColor("#52667A"),
        alignment=TA_CENTER, spaceAfter=26,
    ))
    styles.add(ParagraphStyle(
        name="Section", parent=styles["Heading1"], fontName="Helvetica-Bold",
        fontSize=18, leading=23, textColor=colors.HexColor("#17324D"),
        spaceBefore=12, spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        name="Subsection", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=12.5, leading=17, textColor=colors.HexColor("#1C6E8C"),
        spaceBefore=10, spaceAfter=5,
    ))
    styles.add(ParagraphStyle(
        name="BodyReport", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=9.5, leading=14, textColor=colors.HexColor("#263746"),
        spaceAfter=7,
    ))
    styles.add(ParagraphStyle(
        name="Small", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=8.5, leading=12, textColor=colors.HexColor("#52667A"),
    ))
    styles.add(ParagraphStyle(
        name="Callout", parent=styles["BodyText"], fontName="Helvetica-Bold",
        fontSize=10, leading=15, textColor=colors.HexColor("#17324D"),
        backColor=colors.HexColor("#EAF4F7"), borderColor=colors.HexColor("#9CCBD5"),
        borderWidth=0.8, borderPadding=9, spaceBefore=6, spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name="TableText", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=8.5, leading=11, textColor=colors.HexColor("#263746"),
    ))
    styles.add(ParagraphStyle(
        name="TableHead", parent=styles["BodyText"], fontName="Helvetica-Bold",
        fontSize=8.5, leading=11, textColor=colors.white,
    ))
    return styles


def p(text, style):
    return Paragraph(text, style)


def bullet(text, styles):
    return p(f"&#8226; {text}", styles["BodyReport"])


def code(text, styles):
    return Preformatted(text, styles["Code"])


def architecture_table(styles):
    rows = [
        [p("Layer", styles["TableHead"]), p("Component", styles["TableHead"]), p("Responsibility", styles["TableHead"])],
        [p("User interface", styles["TableText"]), p("Streamlit / app.py", styles["TableText"]), p("Chat input, model selection, conversation history, and source display.", styles["TableText"])],
        [p("Application logic", styles["TableText"]), p("rag.py", styles["TableText"]), p("Embeddings, similarity search, prompt construction, and Ollama requests.", styles["TableText"])],
        [p("Ingestion", styles["TableText"]), p("ingest.py", styles["TableText"]), p("PDF extraction, page tracking, chunking, embedding, and indexing.", styles["TableText"])],
        [p("Vector storage", styles["TableText"]), p("ChromaDB", styles["TableText"]), p("Persistent collection of vectors, text chunks, and paper/page metadata.", styles["TableText"])],
        [p("Embedding model", styles["TableText"]), p("all-MiniLM-L6-v2", styles["TableText"]), p("Converts both document chunks and questions into comparable numeric vectors.", styles["TableText"])],
        [p("Generation", styles["TableText"]), p("Ollama + llama3.1", styles["TableText"]), p("Runs the language model locally and generates a grounded response.", styles["TableText"])],
    ]
    table = Table(rows, colWidths=[1.15 * inch, 1.65 * inch, 4.05 * inch], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1C6E8C")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C9D5DF")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F7FAFC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F7F9")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def build_story(styles):
    story = []
    story += [Spacer(1, 0.65 * inch), p("PersonalAgent", styles["ReportTitle"]), p("A Technical Guide to the Local Research RAG Assistant", styles["Subtitle"])]
    story += [HRFlowable(width="82%", thickness=1.2, color=colors.HexColor("#1C6E8C"), hAlign="CENTER"), Spacer(1, 24)]
    story += [p("Project purpose", styles["Subsection"]), p("PersonalAgent is a privacy-oriented question-answering application for research papers. It accepts local PDF files, converts their text into searchable vector representations, retrieves the most relevant excerpts for a question, and asks a locally hosted language model to answer using those excerpts. The result is a small but complete Retrieval-Augmented Generation (RAG) system.", styles["BodyReport"])]
    story += [p("The design has two phases: an offline indexing phase handled by <b>ingest.py</b>, and an interactive question-answering phase handled by <b>app.py</b> and <b>rag.py</b>.", styles["Callout"])]
    story += [p("Report scope", styles["Subsection"]), p("This report describes the implementation present in the project files, including its architecture, data flow, technology stack, algorithms, configuration, setup process, privacy model, limitations, and practical improvement opportunities.", styles["BodyReport"]), PageBreak()]

    story += [p("1. Executive Overview", styles["Section"])]
    story += [p("The application behaves like a private research librarian. The user supplies papers, the system builds a local index, and questions are answered from retrieved passages instead of from the language model's general memory alone. This is important because a language model by itself may produce plausible but unsupported answers. RAG adds a document-retrieval step and gives the model a bounded evidence set.", styles["BodyReport"])]
    story += [p("Core capabilities", styles["Subsection"])]
    for item in [
        "Reads text-based PDF research papers from the papers/ directory.",
        "Preserves the source paper name and page number for every indexed chunk.",
        "Uses semantic embeddings rather than exact keyword matching.",
        "Stores the index persistently in the local chroma_db/ directory.",
        "Uses Ollama to generate answers without sending paper content to a cloud API.",
        "Displays retrieved paper and page sources below each answer.",
    ]:
        story.append(bullet(item, styles))
    story += [p("High-level architecture", styles["Subsection"]), architecture_table(styles), Spacer(1, 10), p("The system is intentionally modular: ingestion can be rerun independently, retrieval can be tested independently of the UI, and the UI delegates domain behavior to rag.py.", styles["BodyReport"]), PageBreak()]

    story += [p("2. Architecture and Data Flow", styles["Section"])]
    story += [p("There are two connected pipelines. The first transforms documents into a searchable knowledge base. The second transforms a user question into a grounded answer.", styles["BodyReport"])]
    story += [p("2.1 Indexing pipeline", styles["Subsection"])]
    for item in [
        "File discovery: ingest.py scans papers/ for filenames ending in .pdf.",
        "PDF opening: PyMuPDF opens each document and iterates through its pages.",
        "Text extraction: page.get_text() returns the text layer. Empty pages are discarded.",
        "Chunking: each page is split into groups of 700 words with 100 words of overlap.",
        "Embedding: all-MiniLM-L6-v2 maps each chunk to a dense vector.",
        "Persistence: ChromaDB stores the vector, original text, and metadata under a stable chunk ID.",
    ]:
        story.append(bullet(item, styles))
    story += [p("2.2 Question pipeline", styles["Subsection"])]
    for item in [
        "The user enters a question in Streamlit.",
        "rag.search() embeds the question with the same embedding model.",
        "ChromaDB returns the five nearest document chunks by default.",
        "rag.build_prompt() combines those chunks with strict answer instructions.",
        "requests.post() sends the prompt to Ollama's local HTTP endpoint.",
        "The generated answer and retrieved sources are displayed in the chat interface.",
    ]:
        story.append(bullet(item, styles))
    story += [p("2.3 Storage model", styles["Subsection"]), p("ChromaDB uses a persistent client pointed at chroma_db/. The collection is named papers. Each record contains an ID, an embedding, the original chunk text, and metadata. Because the database is persistent, the application does not need to recreate embeddings every time the chat UI starts.", styles["BodyReport"])]
    story += [p("Example record", styles["Subsection"]), code('ID:      paper.pdf_p4_c2\nText:    retrieved 700-word excerpt\nMetadata: {"paper": "paper.pdf", "page": 4}\nVector:  embedding generated by all-MiniLM-L6-v2', styles)]
    story += [PageBreak()]

    story += [p("3. Technology Stack", styles["Section"])]
    stack = [
        ("Python", "Primary programming language and runtime."),
        ("Streamlit", "Turns app.py into a browser-based chat application without a separate frontend framework."),
        ("PyMuPDF / fitz", "Opens PDFs and extracts their text page by page."),
        ("Sentence Transformers", "Loads the all-MiniLM-L6-v2 embedding model."),
        ("all-MiniLM-L6-v2", "A compact sentence embedding model suitable for local semantic search."),
        ("ChromaDB", "Vector database used to store and query embedded chunks."),
        ("Ollama", "Local model runner exposing an HTTP generation API."),
        ("llama3.1", "Default local generative model, configurable from the sidebar."),
        ("Requests", "Python HTTP client used to call Ollama."),
    ]
    rows = [[p("Technology", styles["TableHead"]), p("Role", styles["TableHead"])]] + [[p(a, styles["TableText"]), p(b, styles["TableText"])] for a, b in stack]
    table = Table(rows, colWidths=[1.75 * inch, 5.1 * inch], repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1C6E8C")), ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C9D5DF")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F7F9")]), ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story += [table, Spacer(1, 12), p("Why this stack works", styles["Subsection"]), p("The components cover the full RAG lifecycle while remaining lightweight. PyMuPDF handles document input, Sentence Transformers handles semantic representation, ChromaDB handles retrieval, and Ollama handles generation. Streamlit provides an immediate usable interface. There is no separate cloud backend, API gateway, frontend build system, or hosted database.", styles["BodyReport"])]
    story += [p("Local versus cloud responsibilities", styles["Subsection"]), p("After installation and model downloads, normal operation can be offline. PDF text, embeddings, questions, prompts, and generated answers remain on the computer. Internet access is still required initially to install Python packages and download the embedding and Ollama models.", styles["Callout"]), PageBreak()]

    story += [p("4. Code Walkthrough", styles["Section"])]
    story += [p("4.1 ingest.py", styles["Subsection"]), p("The constants define the main indexing configuration: PAPERS_FOLDER is papers, DB_FOLDER is chroma_db, CHUNK_SIZE is 700 words, and CHUNK_OVERLAP is 100 words.", styles["BodyReport"]), p("extract_pages(pdf_path) returns (page_number, text) pairs. Page numbers are converted from Python's zero-based index to human-readable numbering by adding one. Pages with only whitespace are excluded.", styles["BodyReport"]), p("chunk_text(text) splits on whitespace, joins words back into strings, and advances by chunk_size - overlap. The overlap helps retain context when an important sentence falls near a chunk boundary.", styles["BodyReport"]), p("main() creates the embedding model, opens a persistent Chroma client, creates or reuses the papers collection, processes every PDF, and calls collection.upsert(). Upsert means rerunning a file with the same generated IDs replaces those records rather than creating exact duplicates.", styles["BodyReport"])]
    story += [p("4.2 rag.py", styles["Subsection"]), p("The module-level variables _embedder and _collection cache expensive resources. _get_embedder() and _get_collection() initialize them only on first use. This avoids repeatedly loading the embedding model or reopening the collection during a Streamlit session.", styles["BodyReport"]), p("search(question, top_k=5) encodes the question, calls ChromaDB query(), and converts the result arrays into a simple list of dictionaries. The result format is deliberately UI-friendly: every item has text, paper, and page keys.", styles["BodyReport"]), p("build_prompt() creates the grounding boundary. It labels each excerpt with its source and instructs the model to answer only from those excerpts, acknowledge missing evidence, and cite claims.", styles["BodyReport"]), p("ask() combines retrieval and generation. It handles an empty database with a friendly message, otherwise posts JSON to Ollama, disables streaming, enforces a five-minute timeout, raises HTTP errors, and returns the generated response with its source chunks.", styles["BodyReport"])]
    story += [p("4.3 app.py", styles["Subsection"]), p("The Streamlit page sets the title, creates a history list in session state, lets the user choose an Ollama model, renders previous messages, accepts a new chat question, calls ask(), and exposes sources in an expander. The session history is temporary and is lost when the session is restarted.", styles["BodyReport"]), PageBreak()]

    story += [p("5. RAG Concepts Used", styles["Section"])]
    story += [p("Embeddings", styles["Subsection"]), p("An embedding is a numeric representation of text. Texts with similar meaning tend to be close together in vector space, even when they do not share the same keywords. The project embeds both paper chunks and questions with the same model so they can be compared.", styles["BodyReport"])]
    story += [p("Semantic retrieval", styles["Subsection"]), p("When a user asks a question, ChromaDB compares the question vector with stored chunk vectors and returns the nearest results. The current implementation retrieves five chunks. This is semantic search, not a full keyword search or a hybrid search.", styles["BodyReport"])]
    story += [p("Grounded generation", styles["Subsection"]), p("The retrieved chunks are inserted into the prompt as excerpts. The model is asked to treat them as the only evidence. This reduces unsupported answers, although prompting alone cannot guarantee perfect citation or factual compliance.", styles["BodyReport"])]
    story += [p("Metadata and citations", styles["Subsection"]), p("Metadata connects each chunk back to its source. The prompt includes paper and page labels, and the UI separately renders those labels. This provides useful traceability even though the application does not validate whether every generated citation is accurate.", styles["BodyReport"])]
    story += [p("Chunking tradeoffs", styles["Subsection"]), p("Larger chunks preserve more context but may dilute retrieval precision and consume more prompt space. Smaller chunks improve precision but can remove the surrounding explanation needed to interpret a result. The fixed 700-word and 100-word settings are reasonable starting points, not universal optimums.", styles["BodyReport"]), PageBreak()]

    story += [p("6. Installation and Operation", styles["Section"])]
    story += [p("Environment setup", styles["Subsection"]), p("The repository currently contains a .venv directory. On Windows, the interpreter can be used directly without activation:", styles["BodyReport"]), code(r'.\.venv\Scripts\python.exe -m pip install -r requirements.txt', styles), p("Ollama must be installed separately. Then download the default model:", styles["BodyReport"]), code("ollama pull llama3.1", styles), p("If system memory is limited, the README suggests qwen2.5:3b and the model name can be entered in the app sidebar.", styles["BodyReport"])]
    story += [p("Index papers", styles["Subsection"]), code(r'New-Item -ItemType Directory -Force papers\nCopy-Item C:\path\to\paper.pdf papers\n.\.venv\Scripts\python.exe ingest.py', styles), p("The first ingestion run may download the embedding model. The generated vector database is stored locally in chroma_db/.", styles["BodyReport"])]
    story += [p("Run the interface", styles["Subsection"]), code(r'.\.venv\Scripts\python.exe -m streamlit run app.py', styles), p("Streamlit prints a local URL, normally http://localhost:8501, and opens the application in a browser. Enter a question, select the desired Ollama model, and expand Sources to inspect retrieved paper pages.", styles["BodyReport"])]
    story += [p("Operational sequence", styles["Subsection"]), p("Whenever papers are added or changed, rerun ingest.py before asking questions. The chat app does not watch the papers folder and does not automatically rebuild the index.", styles["Callout"]), PageBreak()]

    story += [p("7. Limitations, Risks, and Observations", styles["Section"])]
    limitations = [
        ("Scanned PDFs", "Image-only documents have no text layer, so extract_pages() returns no useful text. OCR is not implemented."),
        ("Complex layouts", "Tables, multi-column reading order, equations, headers, and footers may be extracted imperfectly."),
        ("Stale records", "The current ingestion process upserts discovered files but does not remove records for PDFs that were deleted or renamed."),
        ("README mismatch", "The README says only new files need processing, but ingest.py currently loops over every PDF on every run."),
        ("Empty collection", "Searching an unindexed Chroma collection may depend on Chroma's behavior for empty queries; the user-facing empty-database check occurs after search()."),
        ("Model errors", "A missing Ollama model, stopped Ollama service, connection failure, or malformed response raises an error from the request path."),
        ("Citation validation", "The model is instructed to cite sources, but the application does not verify citations against retrieved metadata."),
        ("No tests", "There is no automated test suite, so ingestion, retrieval, prompt behavior, and UI execution are not regression-tested."),
        ("Temporary chat state", "Conversation history is kept in Streamlit session state and is not durable or shared between users."),
    ]
    for title, detail in limitations:
        story += [p(f"<b>{title}:</b> {detail}", styles["BodyReport"])]
    story += [p("Security and privacy model", styles["Subsection"]), p("The design avoids external inference APIs and does not require API keys. The local Ollama HTTP endpoint is unauthenticated by default, so the machine's local security posture still matters. The application should not be exposed to an untrusted network without adding authentication and request controls.", styles["BodyReport"])]
    story += [p("Performance", styles["Subsection"]), p("Embedding is generally the expensive part of indexing, while generation is usually the slowest interactive step. The embedding model is cached in memory by rag.py, and ChromaDB avoids rebuilding the database at app startup. Larger generation models improve reasoning but require more memory and may respond more slowly.", styles["BodyReport"]), PageBreak()]

    story += [p("8. Recommended Improvements", styles["Section"])]
    recommendations = [
        "Fix the Streamlit typo st.markedown to st.markdown and ensure assistant history is appended only after a question is processed.",
        "Use absolute paths based on the project directory so launching the scripts from another working directory still finds papers/ and chroma_db/.",
        "Track file hashes or modification times so unchanged PDFs are skipped and changed PDFs are reindexed deliberately.",
        "Remove stale Chroma records when a source PDF is deleted or renamed.",
        "Add OCR support for scanned PDFs, for example through a configurable OCR preprocessing step.",
        "Add a reranker or hybrid keyword-plus-vector retrieval for better precision on technical terminology.",
        "Make top_k, chunk size, overlap, and model names configurable through a settings file or environment variables.",
        "Add tests for chunk boundaries, page metadata, prompt construction, empty collections, Ollama failures, and source rendering.",
        "Handle request exceptions with a clear UI message instead of exposing a raw traceback.",
        "Validate or post-process generated citations so displayed claims correspond to retrieved sources.",
        "Add document management controls for listing, rebuilding, and deleting indexed papers.",
    ]
    for item in recommendations:
        story.append(bullet(item, styles))
    story += [p("Suggested testing strategy", styles["Subsection"]), p("Unit tests should first cover chunk_text() with short, exact-boundary, and overlapping inputs. Next, test extract_pages() with a small fixture PDF and assert page numbers. Mock SentenceTransformer, ChromaDB, and requests.post() when testing rag.py so tests remain fast and offline. Finally, run a smoke test that starts Streamlit and confirms a question can render with a mocked or local Ollama service.", styles["BodyReport"])]
    story += [p("Future architecture", styles["Subsection"]), p("The current single-process structure is appropriate for a personal tool. A larger version could separate ingestion into a background job, add a document registry, use a reranking stage, stream Ollama tokens to the UI, and persist conversations. Those changes should come after correctness, source cleanup, and test coverage.", styles["BodyReport"]), PageBreak()]

    story += [p("9. Quick Reference", styles["Section"]), p("Project files", styles["Subsection"]), code("app.py          Streamlit user interface\ningest.py       PDF ingestion and vector indexing\nrag.py          Retrieval and Ollama generation\nrequirements.txt Python dependencies\nREADME.md       Setup and usage notes\npapers/         Input PDFs (created on first ingestion)\nchroma_db/      Persistent vector database\n.venv/          Local Python environment", styles), p("Typical command sequence", styles["Subsection"]), code(r'.\.venv\Scripts\python.exe -m pip install -r requirements.txt\nollama pull llama3.1\n.\.venv\Scripts\python.exe ingest.py\n.\.venv\Scripts\python.exe -m streamlit run app.py', styles), p("Final summary", styles["Subsection"]), p("PersonalAgent is a clear demonstration of a local RAG architecture. Its strongest properties are privacy, simple deployment, traceable source metadata, and a small number of understandable components. Its main gaps are production hardening, OCR, stale-index management, test coverage, and a few runtime/documentation inconsistencies. With those addressed, it can serve as a dependable private research-paper assistant.", styles["BodyReport"])]
    return story


def main():
    styles = make_styles()
    document = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4, rightMargin=0.7 * inch, leftMargin=0.7 * inch,
        topMargin=0.65 * inch, bottomMargin=0.75 * inch,
        title="PersonalAgent Project Report", author="PersonalAgent",
    )
    document.build(build_story(styles), onFirstPage=page_footer, onLaterPages=page_footer)
    print(f"Created {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
