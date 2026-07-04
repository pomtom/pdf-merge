// REST client. All errors become ApiError with the server's envelope message.

export class ApiError extends Error {
  constructor(code, message, detail) {
    super(message);
    this.code = code;
    this.detail = detail;
  }
}

async function request(path, opts = {}) {
  const init = { method: opts.method || "GET" };
  if (opts.body !== undefined) {
    init.headers = { "Content-Type": "application/json" };
    init.body = JSON.stringify(opts.body);
  }
  let res;
  try {
    res = await fetch("/api" + path, init);
  } catch {
    throw new ApiError("network", "Cannot reach the server. Is it still running?");
  }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const err = (data && data.error) || {};
    throw new ApiError(err.code || "internal", err.message || `Request failed (${res.status})`, err.detail);
  }
  return data;
}

export const api = {
  createSession: () => request("/sessions", { method: "POST" }),
  listFiles: (sid) => request(`/sessions/${sid}/files`),
  reorder: (sid, order) => request(`/sessions/${sid}/files/order`, { method: "PATCH", body: { order } }),
  removeFile: (sid, fid) => request(`/sessions/${sid}/files/${fid}`, { method: "DELETE" }),
  merge: (sid, payload) => request(`/sessions/${sid}/jobs/merge`, { method: "POST", body: payload }),
  split: (sid, payload) => request(`/sessions/${sid}/jobs/split`, { method: "POST", body: payload }),
  extract: (sid, payload) => request(`/sessions/${sid}/jobs/extract`, { method: "POST", body: payload }),
  jobStatus: (sid, jid) => request(`/sessions/${sid}/jobs/${jid}`),

  thumbUrl: (sid, fid, page, w) =>
    `/api/sessions/${sid}/files/${fid}/pages/${page}/thumbnail?w=${w}`,
  downloadUrl: (sid, oid) => `/api/sessions/${sid}/outputs/${oid}/download`,

  // XHR instead of fetch: fetch has no upload progress events.
  uploadFiles(sid, files, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const form = new FormData();
      for (const f of files) form.append("files", f);
      xhr.open("POST", `/api/sessions/${sid}/files`);
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable && onProgress) onProgress(e.loaded, e.total);
      };
      xhr.onload = () => {
        let data = null;
        try { data = JSON.parse(xhr.responseText); } catch { /* non-JSON error page */ }
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(data);
        } else {
          const err = (data && data.error) || {};
          reject(new ApiError(err.code || "upload_failed", err.message || `Upload failed (${xhr.status})`));
        }
      };
      xhr.onerror = () => reject(new ApiError("network", "Network error during upload."));
      xhr.send(form);
    });
  },
};
