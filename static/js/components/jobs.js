// Background job lifecycle: start, poll status, show progress and downloads.

import { api } from "../api.js";
import { progressToast } from "../toast.js";

const POLL_MS = 500;

// creationPromise resolves to {job_id}. The toast lives until dismissed so
// download links stay available.
export function startJob(sessionId, creationPromise, label) {
  const pt = progressToast(label);
  creationPromise
    .then(({ job_id }) => poll(sessionId, job_id, pt))
    .catch((err) => pt.error(err.message));
}

function poll(sessionId, jobId, pt) {
  api.jobStatus(sessionId, jobId)
    .then((job) => {
      if (job.status === "done") {
        const downloads = job.outputs.map((o) => ({
          name: o.name,
          url: api.downloadUrl(sessionId, o.output_id),
        }));
        pt.done(
          downloads.length > 1 ? `Created ${downloads.length} files` : "Ready to download",
          downloads
        );
      } else if (job.status === "error") {
        pt.error(job.error?.message || "The operation failed.");
      } else {
        pt.setProgress(job.progress.current, job.progress.total, job.progress.message);
        // setTimeout re-arming (not setInterval): a slow response can never
        // stack multiple in-flight polls.
        setTimeout(() => poll(sessionId, jobId, pt), POLL_MS);
      }
    })
    .catch((err) => pt.error(err.message));
}
