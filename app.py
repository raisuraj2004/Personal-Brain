import json
import os
import uuid

import streamlit as st
from ingest import main as ingest_papers
from rag import ask, DEFAULT_MODEL

CHAT_HISTORY_FILE = "chat_history.json"


def load_chats():
    if not os.path.isfile(CHAT_HISTORY_FILE):
        return []
    try:
        with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as file:
            chats = json.load(file)
        if not isinstance(chats, list):
            return []
        return [
            {
                "id": chat.get("id", str(uuid.uuid4())),
                "title": chat.get("title") or "New chat",
                "messages": chat.get("messages", []),
                "pinned": bool(chat.get("pinned", False)),
            }
            for chat in chats
            if chat.get("messages")
        ]
    except (json.JSONDecodeError, OSError):
        return []


def save_chats(chats):
    with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(chats, file, indent=2)


def new_chat():
    return {
        "id": str(uuid.uuid4()),
        "title": "New chat",
        "messages": [],
        "pinned": False,
    }


def title_from_question(question):
    title = " ".join(question.split())
    return title if len(title) <= 45 else f"{title[:42].rstrip()}..."


st.set_page_config(page_title="Research Agent",)
st.title(" Our Local Research Agent")
st.caption("Runs 100% locally. No data is sent to the cloud. Your data is safe and private.")

if "chats" not in st.session_state:
    st.session_state.chats = load_chats()
    save_chats(st.session_state.chats)
if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = (
        st.session_state.chats[0]["id"] if st.session_state.chats else None
    )

active_chat = next(
    (
        chat for chat in st.session_state.chats
        if chat["id"] == st.session_state.active_chat_id
    ),
    None,
)

with st.sidebar:
    st.header("Settings")
    model = st.text_input("Ollama model name", value=DEFAULT_MODEL)
    st.divider()
    st.subheader("Chat history")
    if st.button(
        "New chat",
        icon=":material/edit_square:",
        type="primary",
        use_container_width=True,
        help="Start a fresh conversation",
    ):
        st.session_state.active_chat_id = None
        st.rerun()

    sorted_chats = sorted(
        st.session_state.chats,
        key=lambda chat: (not chat.get("pinned", False),),
    )
    for chat in sorted_chats:
        label = chat["title"] or "New chat"
        title_column, pin_column, delete_column = st.columns([7, 1, 1])
        with title_column:
            selected = st.button(
                label,
                key=f"chat-{chat['id']}",
                use_container_width=True,
                type=(
                    "primary"
                    if active_chat and chat["id"] == active_chat["id"]
                    else "secondary"
                ),
            )
        with pin_column:
            pinned = st.button(
                "",
                key=f"pin-{chat['id']}",
                icon=":material/push_pin:" if chat.get("pinned") else ":material/keep:",
                help="Unpin chat" if chat.get("pinned") else "Pin chat",
            )
        with delete_column:
            deleted = st.button(
                "",
                key=f"delete-{chat['id']}",
                icon=":material/delete:",
                help="Delete chat",
            )

        if selected:
            st.session_state.active_chat_id = chat["id"]
            st.rerun()
        if pinned:
            chat["pinned"] = not chat.get("pinned", False)
            save_chats(st.session_state.chats)
            st.rerun()
        if deleted:
            st.session_state.chats = [
                item for item in st.session_state.chats
                if item["id"] != chat["id"]
            ]
            if st.session_state.active_chat_id == chat["id"]:
                st.session_state.active_chat_id = None
            save_chats(st.session_state.chats)
            st.rerun()

for message_index, msg in enumerate(active_chat["messages"] if active_chat else []):
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            message_column, edit_column = st.columns([12, 1])
            with message_column:
                st.markdown(msg["content"])
            with edit_column:
                if st.button(
                    "",
                    key=f"edit-{active_chat['id']}-{message_index}",
                    icon=":material/edit:",
                    help="Edit and rerun this question",
                ):
                    st.session_state.editing_message_index = message_index
                    st.rerun()
        else:
            st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("Sources"):
                for s in msg["sources"]:
                    st.markdown(f"- **{s['paper']}**, page {s['page']}")

if "editing_message_index" not in st.session_state:
    st.session_state.editing_message_index = None

if active_chat and st.session_state.editing_message_index is not None:
    edit_index = st.session_state.editing_message_index
    if edit_index >= len(active_chat["messages"]):
        st.session_state.editing_message_index = None
        st.rerun()
    original_question = active_chat["messages"][edit_index]["content"]
    with st.form("edit-question-form"):
        edited_question = st.text_area(
            "Edit question",
            value=original_question,
            height=100,
        )
        save_edit, cancel_edit = st.columns(2)
        with save_edit:
            rerun_edit = st.form_submit_button("Save and rerun", type="primary", use_container_width=True)
        with cancel_edit:
            cancel_edit = st.form_submit_button("Cancel", use_container_width=True)

    if cancel_edit:
        st.session_state.editing_message_index = None
        st.rerun()
    if rerun_edit and edited_question.strip():
        question = edited_question.strip()
        active_chat["messages"] = active_chat["messages"][:edit_index]
        active_chat["title"] = title_from_question(question)
        active_chat["messages"].append({"role": "user", "content": question})
        with st.spinner("Thinking..."):
            try:
                answer, chunks = ask(question, model=model)
            except Exception as error:
                answer = f"I could not generate an answer: {error}"
                chunks = []
        active_chat["messages"].append({"role": "assistant", "content": answer, "sources": chunks})
        st.session_state.editing_message_index = None
        save_chats(st.session_state.chats)
        st.rerun()

submission = st.chat_input(
    "Ask a question about your papers",
    accept_file="multiple",
    file_type=["pdf"],
    disabled=st.session_state.editing_message_index is not None,
)
if submission:
    if isinstance(submission, str):
        question = submission
        uploaded_files = []
    else:
        question = submission.text
        uploaded_files = submission.files

    if uploaded_files:
        os.makedirs("papers", exist_ok=True)
        for uploaded_file in uploaded_files:
            filename = os.path.basename(uploaded_file.name)
            with open(os.path.join("papers", filename), "wb") as file:
                file.write(uploaded_file.getbuffer())

        try:
            with st.spinner("Indexing uploaded papers..."):
                ingest_papers()
            st.success(f"Indexed {len(uploaded_files)} paper(s).")
        except Exception as error:
            st.error(f"Indexing failed: {error}")

    if question:
        if active_chat is None:
            active_chat = new_chat()
            st.session_state.chats.insert(0, active_chat)
            st.session_state.active_chat_id = active_chat["id"]
        if not active_chat["messages"]:
            active_chat["title"] = title_from_question(question)
        active_chat["messages"].append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    answer, chunks = ask(question, model=model)
                    st.markdown(answer)
                    if chunks:
                        with st.expander("Sources"):
                            for s in chunks:
                                st.markdown(f"- **{s['paper']}**, page {s['page']}")
                except Exception as error:
                    answer = f"I could not generate an answer: {error}"
                    chunks = []
                    st.error(answer)
        active_chat["messages"].append({"role": "assistant", "content": answer, "sources": chunks})
        save_chats(st.session_state.chats)
    elif uploaded_files:
        st.info("Your papers are indexed. Ask a question in the chat box to get an answer.")