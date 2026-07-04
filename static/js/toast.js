// Toast notifications and progress toasts (bottom-right stack).

import { escapeHtml } from "./util.js";

const root = () => document.getElementById("toasts");

function make(type, titleHtml) {
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.innerHTML = `<div class="toast-title"><span>${titleHtml}</span>
    <button class="toast-close" aria-label="Dismiss">✕</button></div>`;
  el.querySelector(".toast-close").addEventListener("click", () => el.remove());
  root().appendChild(el);
  return el;
}

export function toast(message, type = "info", timeout = 4000) {
  const el = make(type, escapeHtml(message));
  if (timeout) setTimeout(() => el.remove(), timeout);
  return el;
}

export function toastError(message) {
  return toast(message, "error", 8000);
}

// A persistent toast with a progress bar and lifecycle methods; used for
// uploads and background jobs.
export function progressToast(label) {
  const el = make("info", escapeHtml(label));
  const msg = document.createElement("div");
  msg.className = "toast-msg";
  const bar = document.createElement("div");
  bar.className = "toast-bar indeterminate";
  bar.innerHTML = "<div></div>";
  el.append(msg, bar);

  return {
    el,
    setProgress(current, total, message) {
      if (total > 0) {
        bar.classList.remove("indeterminate");
        bar.firstElementChild.style.width = `${Math.round((current / total) * 100)}%`;
        msg.textContent = message ? `${message} (${current}/${total})` : `${current}/${total}`;
      } else if (message) {
        msg.textContent = message;
      }
    },
    done(message, downloads = []) {
      el.className = "toast success";
      bar.remove();
      msg.textContent = message;
      if (downloads.length) {
        const list = document.createElement("div");
        list.className = "toast-downloads";
        list.innerHTML = downloads
          .map((d) => `<a href="${d.url}" download>⬇ ${escapeHtml(d.name)}</a>`)
          .join("");
        el.appendChild(list);
      }
    },
    error(message) {
      el.className = "toast error";
      bar.remove();
      msg.textContent = message;
    },
    remove() { el.remove(); },
  };
}
