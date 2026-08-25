"use strict";

const value = document.querySelector("#noteValue");
const form = document.querySelector("#noteForm");
const save = document.querySelector("#noteSave");
const count = document.querySelector("#noteCount");
const draftState = document.querySelector("#draftState");
const connection = document.querySelector("#connection");
const dragHandle = document.querySelector("#dragHandle");
const DRAFT_KEY = "bok.quick-note-draft.floating.v1";
const DRAFT_TTL = 24 * 60 * 60 * 1000;
let connected = false;
const nativeInvoke = window.__TAURI__?.core?.invoke;

function readDraft() {
  try {
    const draft = JSON.parse(localStorage.getItem(DRAFT_KEY) || "null");
    if (!draft || typeof draft.text !== "string" || Date.now() - Number(draft.updatedAt || 0) > DRAFT_TTL) {
      localStorage.removeItem(DRAFT_KEY);
      return "";
    }
    return draft.text;
  } catch { return ""; }
}

function writeDraft(text) {
  try {
    if (text) localStorage.setItem(DRAFT_KEY, JSON.stringify({ text, updatedAt: Date.now() }));
    else localStorage.removeItem(DRAFT_KEY);
  } catch { /* drafts are best effort */ }
}

function updateMeta() {
  count.textContent = `${value.value.length} / 20000`;
  draftState.textContent = value.value ? "草稿保存在本机" : "还没有内容";
}

async function checkConnection() {
  try {
    if (nativeInvoke) {
      const ready = await nativeInvoke("quick_note_status");
      if (!ready) throw new Error("not_ready");
    } else {
      const response = await fetch("/api/heartbeat", { cache: "no-store", credentials: "same-origin" });
      if (!response.ok) throw new Error(String(response.status));
    }
    connected = true;
    connection.textContent = "本机已连接";
    connection.title = "随手记会直接保存到当前 Bok 知识库";
    connection.classList.remove("is-error");
  } catch {
    connected = false;
    connection.textContent = "连接断开 · 点此重试";
    connection.title = "草稿仍保留在本机；关闭后从知识库重新打开小窗也可恢复";
    connection.classList.add("is-error");
  }
  return connected;
}

async function submitNote() {
  const text = value.value.trim();
  if (!text) {
    value.focus();
    return;
  }
  save.disabled = true;
  save.textContent = "保存中…";
  try {
    if (!connected && !(await checkConnection())) {
      throw new Error("本机服务已断开；草稿已保留，请从知识库重新打开随手记");
    }
    if (nativeInvoke) {
      await nativeInvoke("quick_note_save", { text });
    } else {
      const response = await fetch("/api/bok/v1/quick-notes", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          "Idempotency-Key": `ui-floating-note-${crypto.randomUUID?.() || Date.now()}`,
        },
        body: JSON.stringify({ text, source: "boujoy-ui-floating" }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.error?.message || payload.error || `保存失败（${response.status}）`);
    }
    value.value = "";
    writeDraft("");
    updateMeta();
    draftState.textContent = "已记下来";
    connected = true;
    connection.textContent = "本机已连接";
    connection.classList.remove("is-error");
  } catch (error) {
    draftState.textContent = String(error.message || "保存失败，草稿仍保留在本机");
    connection.textContent = "保存失败 · 点此重试";
    connection.classList.add("is-error");
  } finally {
    save.disabled = false;
    save.innerHTML = "记下来 <kbd>⌘↵</kbd>";
  }
}

let dragOffset = null;
dragHandle.addEventListener("pointerdown", (event) => {
  dragOffset = { x: event.screenX - window.screenX, y: event.screenY - window.screenY };
  dragHandle.setPointerCapture?.(event.pointerId);
});
dragHandle.addEventListener("pointermove", (event) => {
  if (!dragOffset || window.top !== window) return;
  try { window.moveTo(event.screenX - dragOffset.x, event.screenY - dragOffset.y); } catch { /* native titlebar remains draggable */ }
});
dragHandle.addEventListener("pointerup", () => { dragOffset = null; });
value.addEventListener("input", () => { writeDraft(value.value); updateMeta(); });
value.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") { event.preventDefault(); submitNote(); }
});
form.addEventListener("submit", (event) => { event.preventDefault(); submitNote(); });
connection.addEventListener("click", checkConnection);

value.value = readDraft();
updateMeta();
checkConnection();
window.setInterval(checkConnection, 30000);
