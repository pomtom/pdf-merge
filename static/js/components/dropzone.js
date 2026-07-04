// File intake: browse button, empty-state dropzone, and full-window drag-drop.

import { api } from "../api.js";
import { progressToast, toast, toastError } from "../toast.js";
import { humanSize } from "../util.js";

export function initDropzone(store) {
  const input = document.getElementById("file-input");
  const overlay = document.getElementById("drop-overlay");
  const emptyZone = document.getElementById("dropzone-empty");

  document.getElementById("btn-add").addEventListener("click", () => input.click());
  emptyZone.addEventListener("click", () => input.click());

  input.addEventListener("change", () => {
    if (input.files.length) upload([...input.files]);
    input.value = ""; // allow re-selecting the same files
  });

  // dragenter/dragleave fire for every child node; a counter tells us when
  // the pointer actually left the window.
  let depth = 0;
  window.addEventListener("dragenter", (e) => {
    if (![...e.dataTransfer.types].includes("Files")) return;
    depth += 1;
    overlay.hidden = false;
  });
  window.addEventListener("dragleave", () => {
    depth = Math.max(0, depth - 1);
    if (depth === 0) overlay.hidden = true;
  });
  window.addEventListener("dragover", (e) => e.preventDefault());
  window.addEventListener("drop", (e) => {
    e.preventDefault();
    depth = 0;
    overlay.hidden = true;
    const files = [...e.dataTransfer.files];
    if (files.length) upload(files);
  });

  async function upload(files) {
    const sid = store.state.sessionId;
    const totalBytes = files.reduce((n, f) => n + f.size, 0);
    const pt = progressToast(
      `Uploading ${files.length} file${files.length > 1 ? "s" : ""} (${humanSize(totalBytes)})`
    );
    try {
      const res = await api.uploadFiles(sid, files, (loaded, total) =>
        pt.setProgress(loaded, total, "Uploading")
      );
      pt.remove();
      for (const r of res.rejected) toastError(`${r.name}: ${r.message}`);
      if (res.files.length) {
        store.update((s) => {
          s.files.push(...res.files);
          if (!s.activeFileId) s.activeFileId = res.files[0].file_id;
        }, ["files", "activeFileId"]);
        toast(`Added ${res.files.length} file${res.files.length > 1 ? "s" : ""}`, "success");
      }
    } catch (err) {
      pt.remove();
      toastError(err.message);
    }
  }
}
