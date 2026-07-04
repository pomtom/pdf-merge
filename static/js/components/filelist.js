// Ordered file cards in the sidebar: select, drag-reorder (SortableJS), remove.

import { api } from "../api.js";
import { toastError } from "../toast.js";
import { escapeHtml, humanSize } from "../util.js";

export function initFilelist(store) {
  const list = document.getElementById("filelist");
  const emptyZone = document.getElementById("dropzone-empty");

  Sortable.create(list, {
    handle: ".filecard-handle",
    animation: 150,
    onEnd: async () => {
      const order = [...list.children].map((el) => el.dataset.id);
      const previous = store.state.files.map((f) => f.file_id);
      // Optimistic: reflect the DOM order in state immediately.
      store.update((s) => {
        const byId = Object.fromEntries(s.files.map((f) => [f.file_id, f]));
        s.files = order.map((id) => byId[id]);
      }, ["files"]);
      try {
        await api.reorder(store.state.sessionId, order);
      } catch (err) {
        toastError(`Could not save the new order: ${err.message}`);
        store.update((s) => {
          const byId = Object.fromEntries(s.files.map((f) => [f.file_id, f]));
          s.files = previous.map((id) => byId[id]);
        }, ["files"]);
      }
    },
  });

  list.addEventListener("click", async (e) => {
    const card = e.target.closest(".filecard");
    if (!card) return;
    const fileId = card.dataset.id;
    if (e.target.closest(".filecard-remove")) {
      try {
        await api.removeFile(store.state.sessionId, fileId);
        store.update((s) => {
          s.files = s.files.filter((f) => f.file_id !== fileId);
          delete s.pageState[fileId];
          if (s.activeFileId === fileId) s.activeFileId = s.files[0]?.file_id ?? null;
        }, ["files", "activeFileId"]);
      } catch (err) {
        toastError(err.message);
      }
      return;
    }
    store.update((s) => { s.activeFileId = fileId; }, ["activeFileId"]);
  });

  function badges(state, file) {
    const ps = state.pageState[file.file_id];
    if (!ps) return "";
    const parts = [];
    if (ps.selected.size) parts.push(`<span class="badge">${ps.selected.size} selected</span>`);
    if (ps.rotations.size) parts.push(`<span class="badge">${ps.rotations.size} rotated</span>`);
    if (ps.deleted.size) parts.push(`<span class="badge badge-danger">${ps.deleted.size} deleted</span>`);
    return parts.length ? `<div class="filecard-badges">${parts.join("")}</div>` : "";
  }

  function render(state) {
    emptyZone.hidden = state.files.length > 0;
    list.innerHTML = state.files
      .map(
        (f) => `
      <div class="filecard ${f.file_id === state.activeFileId ? "active" : ""}" data-id="${f.file_id}">
        <span class="filecard-handle" title="Drag to reorder">⠿</span>
        <img class="filecard-thumb" loading="lazy" alt=""
             src="${api.thumbUrl(state.sessionId, f.file_id, 0, 160)}">
        <div class="filecard-body">
          <div class="filecard-name" title="${escapeHtml(f.name)}">${escapeHtml(f.name)}</div>
          <div class="filecard-meta">${f.page_count} page${f.page_count > 1 ? "s" : ""} · ${humanSize(f.size_bytes)}</div>
          ${badges(state, f)}
        </div>
        <button class="filecard-remove" title="Remove from list">✕</button>
      </div>`
      )
      .join("");
  }

  store.on(["files", "activeFileId", "pageState"], render);
  render(store.state);
}
