// Top-bar actions: Merge, Split, Extract — each opens a small modal that
// builds the job payload from current state.

import { api } from "../api.js";
import { buildPageOps, isUntouched, pageState } from "../state.js";
import { toastError } from "../toast.js";
import { escapeHtml, parseRanges } from "../util.js";
import { startJob } from "./jobs.js";

function openModal(title, bodyHtml) {
  const root = document.getElementById("modal-root");
  root.innerHTML = `
    <div class="modal-overlay">
      <div class="modal" role="dialog" aria-label="${escapeHtml(title)}">
        <h3>${escapeHtml(title)}</h3>
        ${bodyHtml}
        <div class="modal-actions">
          <button class="btn" data-modal-cancel>Cancel</button>
          <button class="btn btn-primary" data-modal-ok>Start</button>
        </div>
      </div>
    </div>`;
  const overlay = root.firstElementChild;
  const close = () => (root.innerHTML = "");
  overlay.addEventListener("click", (e) => { if (e.target === overlay) close(); });
  overlay.querySelector("[data-modal-cancel]").addEventListener("click", close);
  const onEsc = (e) => { if (e.key === "Escape") { close(); document.removeEventListener("keydown", onEsc); } };
  document.addEventListener("keydown", onEsc);
  overlay.querySelector("input")?.focus();
  return { overlay, close };
}

export function initToolbar(store) {
  const btnMerge = document.getElementById("btn-merge");
  const btnSplit = document.getElementById("btn-split");
  const btnExtract = document.getElementById("btn-extract");

  function activeFile(state) {
    return state.files.find((f) => f.file_id === state.activeFileId) || null;
  }

  function refreshButtons(state) {
    const file = activeFile(state);
    const ps = file && state.pageState[file.file_id];
    btnMerge.disabled = state.files.length === 0;
    btnSplit.disabled = !file;
    btnExtract.disabled = !file || !ps || ps.selected.size === 0;
    btnExtract.title = btnExtract.disabled
      ? "Select pages in the grid to enable extraction"
      : `Extract ${ps.selected.size} selected page(s) from ${file.name}`;
  }

  // ---- merge -----------------------------------------------------------

  btnMerge.addEventListener("click", () => {
    const state = store.state;
    const anySelected = state.files.some((f) => state.pageState[f.file_id]?.selected.size);
    const totalPages = state.files.reduce((n, f) => n + f.page_count, 0);
    const { overlay, close } = openModal("Merge PDFs", `
      <div class="field">
        <label for="merge-name">Output file name</label>
        <input type="text" id="merge-name" value="merged.pdf">
      </div>
      ${anySelected ? `
      <div class="field">
        <label class="check-row">
          <input type="checkbox" id="merge-selected-only">
          Merge only the selected pages
        </label>
      </div>` : ""}
      <p class="hint">${state.files.length} file(s), ${totalPages} pages in the sidebar order.
      Deleted pages are skipped and rotations are applied.</p>`);

    overlay.querySelector("[data-modal-ok]").addEventListener("click", () => {
      const name = overlay.querySelector("#merge-name").value.trim() || "merged.pdf";
      const onlySelected = overlay.querySelector("#merge-selected-only")?.checked || false;
      const items = [];
      for (const file of store.state.files) {
        const ps = store.state.pageState[file.file_id];
        if (onlySelected) {
          if (!ps || ps.selected.size === 0) continue;
          items.push({ file_id: file.file_id, pages: buildPageOps(file, ps, true) });
        } else if (isUntouched(ps)) {
          items.push({ file_id: file.file_id, pages: null });
        } else {
          const ops = buildPageOps(file, ps, false);
          if (ops.length) items.push({ file_id: file.file_id, pages: ops });
        }
      }
      if (!items.length) { toastError("Nothing to merge — every page is deselected or deleted."); return; }
      close();
      startJob(store.state.sessionId, api.merge(store.state.sessionId, { output_name: name, items }),
        `Merging into ${name}`);
    });
  });

  // ---- split --------------------------------------------------------------

  btnSplit.addEventListener("click", () => {
    const file = activeFile(store.state);
    if (!file) return;
    const { overlay, close } = openModal(`Split ${file.name}`, `
      <div class="field radio-row">
        <label><input type="radio" name="split-mode" value="ranges" checked> Page ranges</label>
        <label><input type="radio" name="split-mode" value="chunks"> Every N pages</label>
        <label><input type="radio" name="split-mode" value="every_page"> One file per page</label>
      </div>
      <div class="field" id="split-ranges-field">
        <label for="split-ranges">Ranges (1&ndash;${file.page_count})</label>
        <input type="text" id="split-ranges" placeholder="e.g. 1-3, 7, 9-12">
      </div>
      <div class="field" id="split-chunk-field" style="display:none">
        <label for="split-chunk">Pages per file</label>
        <input type="number" id="split-chunk" value="10" min="1" max="${file.page_count}">
      </div>
      <div class="field">
        <label for="split-base">Output name prefix</label>
        <input type="text" id="split-base" value="${escapeHtml(file.name.replace(/\.pdf$/i, ""))}">
      </div>`);

    overlay.querySelectorAll('input[name="split-mode"]').forEach((radio) =>
      radio.addEventListener("change", () => {
        overlay.querySelector("#split-ranges-field").style.display = radio.value === "ranges" && radio.checked ? "" : "none";
        overlay.querySelector("#split-chunk-field").style.display = radio.value === "chunks" && radio.checked ? "" : "none";
      })
    );

    overlay.querySelector("[data-modal-ok]").addEventListener("click", () => {
      const mode = overlay.querySelector('input[name="split-mode"]:checked').value;
      const payload = {
        file_id: file.file_id,
        mode,
        output_basename: overlay.querySelector("#split-base").value.trim() || "part",
      };
      try {
        if (mode === "ranges") payload.ranges = parseRanges(overlay.querySelector("#split-ranges").value);
        if (mode === "chunks") {
          payload.chunk_size = parseInt(overlay.querySelector("#split-chunk").value, 10);
          if (!payload.chunk_size || payload.chunk_size < 1) throw new Error("Enter a valid chunk size.");
        }
      } catch (err) {
        toastError(err.message);
        return;
      }
      close();
      startJob(store.state.sessionId, api.split(store.state.sessionId, payload), `Splitting ${file.name}`);
    });
  });

  // ---- extract ------------------------------------------------------------

  btnExtract.addEventListener("click", () => {
    const file = activeFile(store.state);
    const ps = file && store.state.pageState[file.file_id];
    if (!file || !ps || ps.selected.size === 0) return;
    const { overlay, close } = openModal(`Extract ${ps.selected.size} page(s)`, `
      <div class="field">
        <label for="extract-name">Output file name</label>
        <input type="text" id="extract-name" value="${escapeHtml(file.name.replace(/\.pdf$/i, ""))}_pages.pdf">
      </div>
      <p class="hint">Selected pages are extracted in document order with their rotations applied.</p>`);

    overlay.querySelector("[data-modal-ok]").addEventListener("click", () => {
      const name = overlay.querySelector("#extract-name").value.trim() || "extracted.pdf";
      const pages = buildPageOps(file, pageState(store.state, file.file_id), true);
      if (!pages.length) { toastError("The selected pages were all deleted."); return; }
      close();
      startJob(store.state.sessionId,
        api.extract(store.state.sessionId, { file_id: file.file_id, output_name: name, pages }),
        `Extracting into ${name}`);
    });
  });

  store.on(["files", "activeFileId", "pageState"], refreshButtons);
  refreshButtons(store.state);
}
