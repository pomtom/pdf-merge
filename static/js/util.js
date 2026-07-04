// Small shared helpers.

export function humanSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`;
}

export function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

// Parse "1-3, 7, 9-12" into [[1,3],[7,7],[9,12]]; throws on bad input.
export function parseRanges(text) {
  const ranges = [];
  for (const token of text.split(",").map((t) => t.trim()).filter(Boolean)) {
    const m = token.match(/^(\d+)\s*-\s*(\d+)$/) || token.match(/^(\d+)$/);
    if (!m) throw new Error(`Invalid range: "${token}"`);
    const start = parseInt(m[1], 10);
    const end = m[2] !== undefined ? parseInt(m[2], 10) : start;
    if (start < 1 || end < start) throw new Error(`Invalid range: "${token}"`);
    ranges.push([start, end]);
  }
  if (!ranges.length) throw new Error("Enter at least one page range.");
  return ranges;
}
