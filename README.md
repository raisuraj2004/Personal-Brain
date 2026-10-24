# Our Local Research Agent

A fully local, free RAG (Retrieval-Augmented Generation) assistant that reads your
research papers and answers questions about them — nothing leaves your computer.

<!-- What's inside -->

- `ingest.py` — reads PDFs from `papers/`, chunks them, embeds them, stores them
- `rag.py` — shared search + answer-generation logic (used by app.py)
- `app.py` — a local HTTP server for the browser-based chat interface
- `web/` — the HTML, CSS, and JavaScript interface
- `requirements.txt` — the free Python libraries this depends on

<!-- One-time setup -->

1. **Install Ollama** (the engine that runs the AI model locally):
   Download from https://ollama.com and install it.

2. **Download a model:**
   ```
   ollama pull llama3.1
   ```
   If your machine has less RAM (8GB or under), use a smaller model instead:
   ```
   ollama pull qwen2.5:3b
   ```
   and change `DEFAULT_MODEL` in `rag.py` (or just type the model name into the
   sidebar in the app) to match.

3. **Create a Python virtual environment and install dependencies:**
   ```
   python -m venv venv
   source venv/bin/activate      # on Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

<!-- Using it -->

1. Put your PDF papers into a `papers/` folder (created automatically the first
   time you run `ingest.py`).

2. Build the searchable database:
   ```
   python ingest.py
   ```
   Re-run this any time you add new papers — it only needs to process new files.

3. Launch the chat interface:
   ```
   python app.py
   ```
   Open http://127.0.0.1:8501 in your browser to ask questions and see which
   paper + page number each answer came from. Keep the terminal running while
   you use the app; press Ctrl+C to stop the local server.

 <!-- Notes -->

- Everything runs offline once Ollama and the Python packages are installed —
  no API keys, no cloud calls, no cost.
- Scanned/image-based PDFs are processed with local Tesseract OCR when they
  have no extractable text layer. Install Tesseract separately and ensure its
  executable is on PATH before running `ingest.py`.
- Answer quality depends on the model you choose — bigger models (8B+) reason
  better but need more RAM; smaller models (3B) are faster but less sharp.
