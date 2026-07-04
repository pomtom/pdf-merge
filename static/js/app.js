// Entry point: session bootstrap, store creation, component wiring.

import { api } from "./api.js";
import { createStore } from "./state.js";
import { toastError } from "./toast.js";
import { initDropzone } from "./components/dropzone.js";
import { initFilelist } from "./components/filelist.js";
import { initPagegrid } from "./components/pagegrid.js";
import { initTheme } from "./components/theme.js";
import { initToolbar } from "./components/toolbar.js";

// Reuse the session across reloads within a browser tab; fall back to a
// fresh one when the server no longer knows it (restart, TTL cleanup).
async function ensureSession() {
  const existing = sessionStorage.getItem("pdfstudio.sid");
  if (existing) {
    try {
      const { files } = await api.listFiles(existing);
      return { sessionId: existing, files };
    } catch { /* expired or server restarted with a clean data dir */ }
  }
  const { session_id } = await api.createSession();
  sessionStorage.setItem("pdfstudio.sid", session_id);
  return { sessionId: session_id, files: [] };
}

async function main() {
  initTheme();

  let boot;
  try {
    boot = await ensureSession();
  } catch (err) {
    toastError(`Could not start a session: ${err.message}`);
    return;
  }

  const store = createStore({
    sessionId: boot.sessionId,
    files: boot.files,
    pageState: {},
    activeFileId: boot.files[0]?.file_id ?? null,
  });

  initDropzone(store);
  initFilelist(store);
  initPagegrid(store);
  initToolbar(store);

  // Failures must never be silent.
  window.addEventListener("unhandledrejection", (e) => {
    console.error(e.reason);
    toastError(e.reason?.message || "Something went wrong.");
  });
  window.addEventListener("error", (e) => {
    console.error(e.error);
    toastError("Something went wrong.");
  });
}

main();
