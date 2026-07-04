// Minimal observable store. Components subscribe to named keys and rebuild
// only their own subtree when one of those keys is reported as changed.

export function createStore(initial) {
  const subs = new Set();
  const state = initial;
  return {
    state,
    // update(fn, keys): mutate state inside fn, then notify subscribers of keys.
    update(fn, keys = []) {
      fn(state);
      for (const sub of subs) sub(state, keys);
    },
    on(keys, fn) {
      const watched = new Set(keys);
      const sub = (st, changed) => {
        if (changed.some((k) => watched.has(k))) fn(st);
      };
      subs.add(sub);
      return () => subs.delete(sub);
    },
  };
}

// Per-file page-level edits (selection / deletion / rotation) live only in
// the client; the server receives them as explicit merge/extract payloads.
export function pageState(state, fileId) {
  if (!state.pageState[fileId]) {
    state.pageState[fileId] = {
      selected: new Set(),
      deleted: new Set(),
      rotations: new Map(), // page index -> 0|90|180|270
      lastClicked: null,    // anchor for shift-range selection
    };
  }
  return state.pageState[fileId];
}

// Ordered page ops for a file honoring deletions and rotations.
// onlySelected=true limits to the current selection.
export function buildPageOps(file, ps, onlySelected) {
  const ops = [];
  for (const page of file.pages) {
    const i = page.index;
    if (ps.deleted.has(i)) continue;
    if (onlySelected && !ps.selected.has(i)) continue;
    ops.push({ index: i, rotate: ps.rotations.get(i) || 0 });
  }
  return ops;
}

// True when the user has made no page-level edits to a file (merge can send
// pages:null and the server takes every page as-is).
export function isUntouched(ps) {
  return !ps || (ps.deleted.size === 0 && ps.rotations.size === 0);
}
