const state = {
  chats: [],
  activeChatId: null,
  files: [],
  busy: false,
  statusTimer: null,
  editingIndex: null,
};

const elements = {
  chatList: document.querySelector("#chat-list"),
  historyCount: document.querySelector("#history-count"),
  search: document.querySelector("#search-chats"),
  newChat: document.querySelector("#new-chat"),
  themeToggle: document.querySelector("#theme-toggle"),
  conversation: document.querySelector("#conversation"),
  welcome: document.querySelector("#welcome"),
  messageList: document.querySelector("#message-list"),
  composer: document.querySelector("#composer"),
  input: document.querySelector("#message-input"),
  sendButton: document.querySelector("#send-button"),
  attachButton: document.querySelector("#attach-button"),
  fileInput: document.querySelector("#file-input"),
  attachmentList: document.querySelector("#attachment-list"),
  uploadStatus: document.querySelector("#upload-status"),
  suggestionGrid: document.querySelector("#suggestion-grid"),
  editDialog: document.querySelector("#edit-dialog"),
  editForm: document.querySelector("#edit-form"),
  editInput: document.querySelector("#edit-input"),
};

const icon = {
  assistant: '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 3.2 20.8 8v8L12 20.8 3.2 16V8L12 3.2Z" stroke="currentColor" stroke-width="1.5"/><path d="m8 14 2.2-4.5L12.5 17l2.1-4" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.4"/></svg>',
  pin: '<svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="m13.5 3.5 3 3-2.2 1.1-.9 4.3-1.3 1.3-2.2-2.2-4.1 4.1-.9-.9 4.1-4.1-2.2-2.2 1.3-1.3 4.3-.9 1.1-2.2Z" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.2"/></svg>',
  trash: '<svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M4.5 6h11m-9.5 0 .6 10h5.8l.6-10M8 6V4h4v2m-3.5 2v5m3-5v5" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.2"/></svg>',
};

function createId() {
  return crypto.randomUUID();
}

function titleFromQuestion(question) {
  const title = question.trim().replace(/\s+/g, " ");
  return title.length <= 45 ? title : `${title.slice(0, 42).trimEnd()}...`;
}

function activeChat() {
  return state.chats.find((chat) => chat.id === state.activeChatId) ?? null;
}

async function request(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || `Request failed (${response.status}).`);
  return result;
}

async function persistChats() {
  try {
    await request("/api/chats", { chats: state.chats });
  } catch (error) {
    showStatus(`Could not save chat history: ${error.message}`, true);
  }
}

function showStatus(message, isError = false) {
  clearTimeout(state.statusTimer);
  elements.uploadStatus.textContent = message;
  elements.uploadStatus.classList.toggle("error", isError);
  elements.uploadStatus.hidden = false;
  state.statusTimer = setTimeout(() => {
    elements.uploadStatus.hidden = true;
  }, 5500);
}

function setBusy(busy) {
  state.busy = busy;
  elements.input.disabled = busy;
  elements.sendButton.disabled = busy || (!elements.input.value.trim() && state.files.length === 0);
  elements.attachButton.disabled = busy;
}

function resizeInput() {
  elements.input.style.height = "auto";
  elements.input.style.height = `${Math.min(elements.input.scrollHeight, 160)}px`;
  elements.sendButton.disabled = state.busy || (!elements.input.value.trim() && state.files.length === 0);
}

function makeChat() {
  return { id: createId(), title: "New chat", messages: [], pinned: false };
}

function makeButton(className, accessibleName, buttonIcon, onClick) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = className;
  button.setAttribute("aria-label", accessibleName);
  button.title = accessibleName;
  button.innerHTML = buttonIcon;
  button.addEventListener("click", onClick);
  return button;
}

function renderChats() {
  const query = elements.search.value.trim().toLocaleLowerCase();
  const sortedChats = [...state.chats].sort((a, b) => Number(b.pinned) - Number(a.pinned));
  const filtered = sortedChats.filter((chat) => (chat.title || "New chat").toLocaleLowerCase().includes(query));
  elements.historyCount.textContent = String(state.chats.length);
  elements.chatList.replaceChildren();

  if (filtered.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-history";
    empty.textContent = query ? "No chats match your search." : "Your conversations will appear here.";
    elements.chatList.append(empty);
    return;
  }

  for (const chat of filtered) {
    const row = document.createElement("div");
    row.className = `chat-row${chat.id === state.activeChatId ? " active" : ""}${chat.pinned ? " pinned" : ""}`;
    const select = document.createElement("button");
    select.type = "button";
    select.className = "chat-select";
    select.textContent = chat.title || "New chat";
    select.title = chat.title || "New chat";
    select.addEventListener("click", () => {
      state.activeChatId = chat.id;
      renderConversation();
    });
    const actions = document.createElement("span");
    actions.className = "chat-actions";
    actions.append(
      makeButton("chat-action pin-action", chat.pinned ? "Unpin chat" : "Pin chat", icon.pin, async (event) => {
        event.stopPropagation();
        chat.pinned = !chat.pinned;
        renderChats();
        await persistChats();
      }),
      makeButton("chat-action", "Delete chat", icon.trash, async (event) => {
        event.stopPropagation();
        state.chats = state.chats.filter((item) => item.id !== chat.id);
        if (state.activeChatId === chat.id) state.activeChatId = null;
        render();
        await persistChats();
      }),
    );
    row.append(select, actions);
    elements.chatList.append(row);
  }
}

function addAssistantContent(container, content) {
  const text = document.createElement("div");
  text.className = "message-content";
  const lines = content.split(/\r?\n/);
  let list = null;
  let paragraph = null;
  const closeBlocks = () => {
    list = null;
    paragraph = null;
  };
  const appendInline = (parent, value) => {
    const tokens = value.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g);
    for (const token of tokens) {
      if (!token) continue;
      const match = token.match(/^(\*\*|\*|`)([\s\S]+)\1$/);
      if (!match) {
        parent.append(document.createTextNode(token));
        continue;
      }
      const node = document.createElement(match[1] === "**" ? "strong" : match[1] === "*" ? "em" : "code");
      node.textContent = match[2];
      parent.append(node);
    }
  };

  for (const line of lines) {
    const heading = line.match(/^#{1,3}\s+(.+)$/);
    const listItem = line.match(/^\s*([-*+]|\d+\.)\s+(.+)$/);
    if (!line.trim()) {
      closeBlocks();
      continue;
    }
    if (heading) {
      closeBlocks();
      const element = document.createElement("h3");
      appendInline(element, heading[1]);
      text.append(element);
    } else if (listItem) {
      paragraph = null;
      const isOrdered = /^\d/.test(listItem[1]);
      if (!list || list.tagName !== (isOrdered ? "OL" : "UL")) {
        list = document.createElement(isOrdered ? "ol" : "ul");
        text.append(list);
      }
      const item = document.createElement("li");
      appendInline(item, listItem[2]);
      list.append(item);
    } else {
      list = null;
      if (!paragraph) {
        paragraph = document.createElement("p");
        text.append(paragraph);
      } else {
        paragraph.append(document.createTextNode(" "));
      }
      appendInline(paragraph, line.trim());
    }
  }
  container.append(text);
}

function renderConversation() {
  const chat = activeChat();
  const hasMessages = Boolean(chat?.messages?.length);
  elements.welcome.hidden = hasMessages;
  elements.messageList.replaceChildren();

  if (!hasMessages) {
    return;
  }

  chat.messages.forEach((message, index) => {
    const article = document.createElement("article");
    article.className = `message ${message.role === "user" ? "user" : "assistant"}`;
    const heading = document.createElement("div");
    heading.className = "message-heading";
    if (message.role === "user") {
      heading.textContent = "You";
    } else {
      const avatar = document.createElement("span");
      avatar.className = "message-avatar";
      avatar.innerHTML = icon.assistant;
      const name = document.createElement("span");
      name.textContent = "Personal Brain";
      heading.append(avatar, name);
    }
    article.append(heading);
    addAssistantContent(article, message.content || "");

    if (message.role === "user") {
      const tools = document.createElement("div");
      tools.className = "message-tools";
      const edit = document.createElement("button");
      edit.type = "button";
      edit.className = "message-action";
      edit.textContent = "Edit question";
      edit.addEventListener("click", () => openEdit(index));
      tools.append(edit);
      article.append(tools);
    } else if (Array.isArray(message.sources) && message.sources.length) {
      const sources = document.createElement("div");
      sources.className = "sources";
      for (const source of message.sources) {
        const chip = document.createElement("span");
        chip.className = "source-chip";
        const paper = document.createElement("strong");
        paper.textContent = source.paper || "Source";
        const page = document.createElement("span");
        page.textContent = `p. ${source.page}`;
        chip.append(paper, page);
        sources.append(chip);
      }
      article.append(sources);
    }
    elements.messageList.append(article);
  });
  elements.conversation.scrollTop = elements.conversation.scrollHeight;
}

function render() {
  renderChats();
  renderConversation();
}

function openEdit(index) {
  const message = activeChat()?.messages[index];
  if (!message || state.busy) return;
  state.editingIndex = index;
  elements.editInput.value = message.content;
  elements.editDialog.showModal();
  elements.editInput.focus();
}

function appendThinking() {
  const article = document.createElement("article");
  article.className = "message assistant";
  article.id = "thinking-message";
  const heading = document.createElement("div");
  heading.className = "message-heading";
  const avatar = document.createElement("span");
  avatar.className = "message-avatar";
  avatar.innerHTML = icon.assistant;
  const name = document.createElement("span");
  name.textContent = "Personal Brain";
  const dots = document.createElement("div");
  dots.className = "thinking-dots";
  dots.setAttribute("aria-label", "Thinking");
  dots.innerHTML = "<span></span><span></span><span></span>";
  heading.append(avatar, name);
  article.append(heading, dots);
  elements.messageList.append(article);
  elements.conversation.scrollTop = elements.conversation.scrollHeight;
}

async function uploadFiles(files) {
  if (!files.length) return;
  const encodedFiles = await Promise.all(files.map(async (file) => ({
    name: file.name,
    data: await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result).split(",", 2)[1]);
      reader.onerror = () => reject(new Error(`Could not read ${file.name}.`));
      reader.readAsDataURL(file);
    }),
  })));
  const result = await request("/api/upload", { files: encodedFiles });
  showStatus(result.message);
}

async function sendQuestion(question, editIndex = null) {
  const trimmed = question.trim();
  if ((!trimmed && state.files.length === 0) || state.busy) return;
  const files = state.files;
  state.files = [];
  renderAttachments();

  let uploadFailed = false;
  if (files.length) {
    showStatus("Adding your papers to the library...");
    setBusy(true);
    try {
      await uploadFiles(files);
    } catch (error) {
      showStatus(`PDF indexing failed: ${error.message}`, true);
      uploadFailed = true;
    }
    setBusy(false);
  }

  if (!trimmed) {
    if (!uploadFailed) showStatus(`Your papers are ready. Ask a question whenever you like.`);
    resizeInput();
    return;
  }

  let chat = activeChat();
  if (!chat) {
    chat = makeChat();
    state.chats.unshift(chat);
    state.activeChatId = chat.id;
  }
  if (editIndex !== null) {
    chat.messages = chat.messages.slice(0, editIndex);
  }
  if (!chat.messages.length) chat.title = titleFromQuestion(trimmed);
  chat.messages.push({ role: "user", content: trimmed });
  render();
  elements.input.value = "";
  resizeInput();
  await persistChats();

  setBusy(true);
  appendThinking();
  try {
    const result = await request("/api/ask", { question: trimmed });
    chat.messages.push({ role: "assistant", content: result.answer, sources: result.sources || [] });
  } catch (error) {
    chat.messages.push({ role: "assistant", content: `I could not generate an answer: ${error.message}`, sources: [] });
  } finally {
    document.querySelector("#thinking-message")?.remove();
    setBusy(false);
    await persistChats();
    render();
    elements.input.focus();
  }
}

function renderAttachments() {
  elements.attachmentList.replaceChildren();
  state.files.forEach((file, index) => {
    const chip = document.createElement("span");
    chip.className = "attachment-chip";
    const label = document.createElement("span");
    label.textContent = file.name;
    const remove = document.createElement("button");
    remove.type = "button";
    remove.setAttribute("aria-label", `Remove ${file.name}`);
    remove.textContent = "×";
    remove.addEventListener("click", () => {
      state.files.splice(index, 1);
      renderAttachments();
      resizeInput();
    });
    chip.append(label, remove);
    elements.attachmentList.append(chip);
  });
  resizeInput();
}

function setTheme(dark) {
  document.body.classList.toggle("light-theme", !dark);
  localStorage.setItem("personal-brain-theme", dark ? "dark" : "light");
}

async function initialize() {
  setTheme(localStorage.getItem("personal-brain-theme") !== "light");
  try {
    const response = await fetch("/api/chats");
    if (!response.ok) throw new Error(`Could not load chat history (${response.status}).`);
    const payload = await response.json();
    state.chats = Array.isArray(payload.chats) ? payload.chats : [];
    state.activeChatId = state.chats[0]?.id ?? null;
  } catch (error) {
    showStatus(error.message, true);
  }
  resizeInput();
  render();
}

elements.newChat.addEventListener("click", () => {
  state.activeChatId = null;
  elements.input.value = "";
  state.files = [];
  renderAttachments();
  render();
  elements.input.focus();
});
elements.search.addEventListener("input", renderChats);
elements.themeToggle.addEventListener("click", () => setTheme(document.body.classList.contains("light-theme")));
elements.attachButton.addEventListener("click", () => elements.fileInput.click());
elements.fileInput.addEventListener("change", () => {
  const selected = [...elements.fileInput.files];
  const invalid = selected.filter((file) => !file.name.toLowerCase().endsWith(".pdf"));
  if (invalid.length) showStatus("Only PDF files can be attached.", true);
  state.files.push(...selected.filter((file) => file.name.toLowerCase().endsWith(".pdf")));
  elements.fileInput.value = "";
  renderAttachments();
});
elements.input.addEventListener("input", resizeInput);
elements.input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    elements.composer.requestSubmit();
  }
});
elements.composer.addEventListener("submit", (event) => {
  event.preventDefault();
  sendQuestion(elements.input.value);
});
elements.suggestionGrid.addEventListener("click", (event) => {
  const button = event.target.closest("button");
  if (!button) return;
  if (button.dataset.action === "upload") {
    elements.fileInput.click();
    return;
  }
  elements.input.value = button.dataset.prompt || "";
  resizeInput();
  elements.input.focus();
});
elements.editDialog.querySelector(".close-edit").addEventListener("click", () => elements.editDialog.close());
elements.editDialog.querySelector(".cancel-edit").addEventListener("click", () => elements.editDialog.close());
elements.editForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const question = elements.editInput.value.trim();
  const index = state.editingIndex;
  if (!question || index === null) return;
  const chat = activeChat();
  chat.title = titleFromQuestion(question);
  elements.editDialog.close();
  state.editingIndex = null;
  sendQuestion(question, index);
});
elements.editDialog.addEventListener("click", (event) => {
  if (event.target === elements.editDialog) elements.editDialog.close();
});
document.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    state.activeChatId = null;
    render();
    elements.input.focus();
  } else if (event.key === "/" && document.activeElement !== elements.search && !elements.editDialog.open) {
    event.preventDefault();
    elements.search.focus();
  }
});

initialize();
