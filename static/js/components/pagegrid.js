// Page thumbnail grid for the active file: lazy-loaded thumbnails,
// select (with shift-range), rotate, delete/restore per page.

import { api } from "../api.js";
import { pageState } from "../state.js";

export function initPagegrid(store) {
  const grid = document.getElementById("pagegrid");
  const bar = document.getElementById("pagegrid-toolbar");
  const empty = document.getElementById("content-empty");

  // Load a thumbnail only when its tile scrolls into view — a 500-page file
  // must not fire 500 requests up front.
  const io = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        const img = entry.target;
        img.src = img.dataset.src;
        io.unobserve(img);
      }
    },
    { root: grid, rootMargin: "300px" }
  );

  function activeFile(state) {
    return state.files.find((f) => f.file_id === state.activeFileId) || null;
  }

  // ---- interactions --------------------------------------------------------

  grid.addEventListener("click", (e) => {
    const tile = e.target.closest(".tile");
    if (!tile) return;
    const index = Number(tile.dataset.page);
    const fileId = store.state.activeFileId;

    if (e.target.closest("button.rot")) {
      store.update((s) => {
        const ps = pageState(s, fileId);
        const next = ((ps.rotations.get(index) || 0) + 90) % 360;
        if (next === 0) ps.rotations.delete(index);
        else ps.rotations.set(index, next);
      }, ["pageState"]);
      return;
    }
    if (e.target.closest("button.del")) {
      store.update((s) => {
        const ps = pageState(s, fileId);
        if (ps.deleted.has(index)) ps.deleted.delete(index);
        else { ps.deleted.add(index); ps.selected.delete(index); }
      }, ["pageState"]);
      return;
    }
    if (e.target.closest(".tile-frame")) {
      store.update((s) => {
        const ps = pageState(s, fileId);
        if (e.shiftKey && ps.lastClicked !== null) {
          const [a, b] = [Math.min(ps.lastClicked, index), Math.max(ps.lastClicked, index)];
          for (let i = a; i <= b; i++) if (!ps.deleted.has(i)) ps.selected.add(i);
        } else if (ps.selected.has(index)) {
          ps.selected.delete(index);
        } else if (!ps.deleted.has(index)) {
          ps.selected.add(index);
        }
        ps.lastClicked = index;
      }, ["pageState"]);
    }
  });

  bar.addEventListener("click", (e) => {
    const btn = e.target.closest("button[data-act]");
    if (!btn) return;
    const fileId = store.state.activeFileId;
    const file = activeFile(store.state);
    store.update((s) => {
      const ps = pageState(s, fileId);
      const all = file.pages.map((p) => p.index).filter((i) => !ps.deleted.has(i));
      switch (btn.dataset.act) {
        case "all": ps.selected = new Set(all); break;
        case "none": ps.selected.clear(); break;
        case "invert": ps.selected = new Set(all.filter((i) => !ps.selected.has(i))); break;
        case "rotate-sel":
          for (const i of ps.selected) {
            const next = ((ps.rotations.get(i) || 0) + 90) % 360;
            if (next === 0) ps.rotations.delete(i); else ps.rotations.set(i, next);
          }
          break;
        case "delete-sel":
          for (const i of ps.selected) ps.deleted.add(i);
          ps.selected.clear();
          break;
        case "restore":
          ps.deleted.clear();
          ps.rotations.clear();
          break;
      }
    }, ["pageState"]);
  });

  // ---- rendering ---------------------------------------------------------

  function rebuild(state) {
    const file = activeFile(state);
    empty.style.display = file ? "none" : "";
    bar.hidden = !file;
    if (!file) { grid.innerHTML = ""; return; }

    grid.innerHTML = file.pages
      .map(
        (p) => `
      <div class="tile" data-page="${p.index}">
        <div class="tile-frame skeleton">
          <img data-src="${api.thumbUrl(state.sessionId, file.file_id, p.index, 320)}" alt="Page ${p.index + 1}">
          <div class="tile-check"></div>
          <div class="tile-del-badge">Deleted</div>
        </div>
        <div class="tile-foot">
          <span class="tile-num">${p.index + 1}</span>
          <div class="tile-actions">
            <button class="rot" title="Rotate 90°">⟳</button>
            <button class="del" title="Delete / restore page">🗑</button>
          </div>
        </div>
      </div>`
      )
      .join("");

    for (const img of grid.querySelectorAll("img[data-src]")) {
      img.addEventListener("load", () => {
        img.classList.add("loaded");
        img.closest(".tile-frame").classList.remove("skeleton");
      });
      io.observe(img);
    }
    refresh(state);
  }

  // Cheap in-place class/transform updates so toggling selection or rotation
  // never reloads thumbnails.
  function refresh(state) {
    const file = activeFile(state);
    if (!file) return;
    const ps = state.pageState[file.file_id];
    for (const tile of grid.children) {
      const i = Number(tile.dataset.page);
      tile.classList.toggle("selected", !!ps && ps.selected.has(i));
      tile.classList.toggle("deleted", !!ps && ps.deleted.has(i));
      const rot = (ps && ps.rotations.get(i)) || 0;
      tile.querySelector("img").style.transform = rot ? `rotate(${rot}deg)` : "";
    }
    const selected = ps ? ps.selected.size : 0;
    const deleted = ps ? ps.deleted.size : 0;
    bar.querySelector(".selcount").textContent =
      `${selected} of ${file.page_count} selected` + (deleted ? ` · ${deleted} deleted` : "");
  }

  function renderBar(state) {
    const file = activeFile(state);
    if (!file) return;
    bar.innerHTML = `
      <span class="file-title">${file.name.replace(/</g, "&lt;")}</span>
      <span class="selcount"></span>
      <span class="spacer"></span>
      <button class="btn btn-small btn-ghost" data-act="all">Select all</button>
      <button class="btn btn-small btn-ghost" data-act="none">None</button>
      <button class="btn btn-small btn-ghost" data-act="invert">Invert</button>
      <button class="btn btn-small btn-ghost" data-act="rotate-sel" title="Rotate selected pages 90°">⟳ Rotate</button>
      <button class="btn btn-small btn-ghost btn-danger" data-act="delete-sel">Delete</button>
      <button class="btn btn-small btn-ghost" data-act="restore" title="Undo all deletions and rotations">Restore</button>`;
  }

  store.on(["activeFileId", "files"], (state) => { renderBar(state); rebuild(state); });
  store.on(["pageState"], refresh);
  renderBar(store.state);
  rebuild(store.state);
}
