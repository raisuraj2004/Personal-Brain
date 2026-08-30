# Our Local Research Agent

A fully local, free RAG (Retrieval-Augmented Generation) assistant that reads your
research papers and answers questions about them — nothing leaves your computer.

<!-- What's inside -->

- `ingest.py` — reads PDFs from `papers/`, chunks them, embeds them, stores them
- `rag.py` — shared search + answer-generation logic (used by app.py)
- `app.py` — a Streamlit chat interface to actually use the thing
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
   streamlit run app.py
   ```
   This opens a page in your browser where you can ask questions and see which
   paper + page number each answer came from.

 <!-- Notes -->

- Everything runs offline once Ollama and the Python packages are installed —
  no API keys, no cloud calls, no cost.
- If a PDF is scanned/image-based rather than text-based, `ingest.py` won't be
  able to extract text from it (OCR support can be added later if you need it).
- Answer quality depends on the model you choose — bigger models (8B+) reason
  better but need more RAM; smaller models (3B) are faster but less sharp.
