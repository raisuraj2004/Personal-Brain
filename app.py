import base64
import json
import mimetypes
import os
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

from ingest import main as ingest_papers
from rag import ask, DEFAULT_MODEL

ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"
CHAT_HISTORY_FILE = ROOT / "chat_history.json"
PAPERS_DIR = ROOT / "papers"


def load_chats():
    if not CHAT_HISTORY_FILE.exists():
        return []
    try:
        with CHAT_HISTORY_FILE.open("r", encoding="utf-8") as file:
            chats = json.load(file)
    except (json.JSONDecodeError, OSError):
        return []

    if not isinstance(chats, list):
        return []

    cleaned = []
    for chat in chats:
        if not isinstance(chat, dict):
            continue
        messages = chat.get("messages", [])
        if not isinstance(messages, list):
            continue
        cleaned.append(
            {
                "id": chat.get("id") or os.urandom(8).hex(),
                "title": chat.get("title") or "New chat",
                "messages": messages,
                "pinned": bool(chat.get("pinned", False)),
            }
        )
    return cleaned


def save_chats(chats):
    with CHAT_HISTORY_FILE.open("w", encoding="utf-8") as file:
        json.dump(chats, file, indent=2)


def title_from_question(question):
    title = " ".join(question.split())
    return title if len(title) <= 45 else f"{title[:42].rstrip()}..."


def parse_json_body(handler):
    content_length = handler.headers.get("Content-Length")
    if content_length is None:
        return {}
    try:
        raw = handler.rfile.read(int(content_length))
    except ValueError:
        return {}
    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def send_json(handler, status_code, payload):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status_code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def serve_file(handler, relative_path):
    relative_path = relative_path.lstrip("/")
    if not relative_path:
        relative_path = "index.html"

    candidate = (WEB_DIR / relative_path).resolve()
    try:
        candidate.relative_to(WEB_DIR.resolve())
    except ValueError:
        send_json(handler, 403, {"error": "Forbidden"})
        return

    if candidate.is_dir():
        candidate = WEB_DIR / "index.html"

    if not candidate.exists() or not candidate.is_file():
        send_json(handler, 404, {"error": "Not found"})
        return

    content = candidate.read_bytes()
    content_type, _ = mimetypes.guess_type(str(candidate))
    if content_type is None:
        content_type = "application/octet-stream"

    handler.send_response(200)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(content)))
    handler.end_headers()
    handler.wfile.write(content)


class PersonalBrainHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/chats":
            send_json(self, 200, {"chats": load_chats()})
            return

        if path.startswith("/api/"):
            send_json(self, 404, {"error": "API endpoint not found"})
            return

        serve_file(self, path)

    def do_POST(self):
        parsed = urlparse(self.path)
        payload = parse_json_body(self)

        if parsed.path == "/api/chats":
            chats = payload.get("chats", [])
            save_chats(chats if isinstance(chats, list) else [])
            send_json(self, 200, {"ok": True})
            return

        if parsed.path == "/api/upload":
            files = payload.get("files", [])
            if not isinstance(files, list):
                send_json(self, 400, {"error": "No files provided."})
                return

            PAPERS_DIR.mkdir(parents=True, exist_ok=True)
            saved = []
            for item in files:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name") or "").strip()
                encoded = item.get("data")
                if not name or not encoded:
                    continue
                if not name.lower().endswith(".pdf"):
                    continue

                data = base64.b64decode(encoded)
                destination = PAPERS_DIR / name
                if destination.exists():
                    stem = destination.stem
                    suffix = destination.suffix
                    counter = 1
                    while destination.exists():
                        destination = PAPERS_DIR / f"{stem}_{counter}{suffix}"
                        counter += 1

                with destination.open("wb") as file_obj:
                    file_obj.write(data)
                saved.append(destination.name)

            try:
                ingest_papers()
            except Exception as error:
                send_json(self, 500, {"error": f"Indexing failed: {error}"})
                return

            send_json(self, 200, {"message": f"Indexed {len(saved)} paper(s).", "count": len(saved)})
            return

        if parsed.path == "/api/ask":
            question = str(payload.get("question", "")).strip()
            if not question:
                send_json(self, 400, {"error": "Question is required."})
                return
            try:
                answer, sources = ask(question, model=DEFAULT_MODEL)
            except Exception as error:
                send_json(self, 500, {"error": f"Could not generate an answer: {error}"})
                return
            send_json(self, 200, {"answer": answer, "sources": sources})
            return

        send_json(self, 404, {"error": "Unknown API endpoint"})

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    os.makedirs(PAPERS_DIR, exist_ok=True)
    host = "127.0.0.1"
    port = 8000
    server = ThreadingHTTPServer((host, port), PersonalBrainHandler)
    print(f"Personal Brain is running at http://{host}:{port}")
    print("Press Ctrl+C to stop the server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Personal Brain...")
    finally:
        server.server_close()