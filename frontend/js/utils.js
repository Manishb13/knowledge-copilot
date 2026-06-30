/**
 * Shared UI utility functions.
 */

/**
 * Redirect to login page if not authenticated.
 */
function requireAuth() {
  if (!window.KC || !KC.isLoggedIn()) {
    window.location.href = "login.html";
  }
}

/**
 * Redirect to corpus selection page if authenticated.
 */
function redirectIfLoggedIn() {
  if (window.KC && KC.isLoggedIn()) {
    window.location.href = "corpus.html";
  }
}

/**
 * Show an alert element with a message.
 * @param {HTMLElement} el - The alert element
 * @param {string} message
 * @param {'error'|'success'|'info'} [type='error']
 */
function showAlert(el, message, type = "error") {
  el.textContent = message;
  el.className = `alert alert-${type} visible`;
}

/**
 * Hide an alert element.
 * @param {HTMLElement} el
 */
function hideAlert(el) {
  el.className = "alert";
  el.textContent = "";
}

/**
 * Get the active corpus ID from sessionStorage.
 * @returns {number|null}
 */
function getActiveCorpusId() {
  const id = sessionStorage.getItem("kc_active_corpus_id");
  return id ? parseInt(id, 10) : null;
}

/**
 * Get the active corpus name from sessionStorage.
 * @returns {string}
 */
function getActiveCorpusName() {
  return sessionStorage.getItem("kc_active_corpus_name") || "Corpus";
}

/**
 * Set the active corpus in sessionStorage.
 * @param {number} id
 * @param {string} name
 */
function setActiveCorpus(id, name) {
  sessionStorage.setItem("kc_active_corpus_id", String(id));
  sessionStorage.setItem("kc_active_corpus_name", name);
}

/**
 * Format an ISO date string into a human-readable time.
 * @param {string} isoString
 * @returns {string}
 */
function formatTime(isoString) {
  if (!isoString) return "";
  const date = new Date(isoString);
  if (isNaN(date.getTime())) return "";
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

/**
 * Format an ISO date string into a readable date.
 * @param {string} isoString
 * @returns {string}
 */
function formatDate(isoString) {
  if (!isoString) return "";
  const date = new Date(isoString);
  if (isNaN(date.getTime())) return "";
  return date.toLocaleDateString([], {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/**
 * Escape HTML special characters to prevent XSS.
 * @param {string} text
 * @returns {string}
 */
function escapeHtml(text) {
  const div = document.createElement("div");
  div.appendChild(document.createTextNode(text));
  return div.innerHTML;
}

/**
 * Get the emoji icon for a file type.
 * @param {string} fileType
 * @returns {string}
 */
function getFileIcon(fileType) {
  const icons = {
    pdf: "📄",
    docx: "📝",
    txt: "📋",
    md: "📓",
  };
  return icons[fileType] || "📄";
}

/**
 * Get initial letters for avatar display.
 * @param {string} email
 * @returns {string}
 */
function getInitials(email) {
  if (!email) return "?";
  const parts = email.split("@")[0].split(/[._-]/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return email.substring(0, 2).toUpperCase();
}

/**
 * Debounce a function.
 * @param {Function} fn
 * @param {number} delay
 * @returns {Function}
 */
function debounce(fn, delay) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

/**
 * Auto-resize a textarea to fit its content.
 * @param {HTMLTextAreaElement} textarea
 */
function autoResizeTextarea(textarea) {
  textarea.style.height = "auto";
  textarea.style.height = Math.min(textarea.scrollHeight, 160) + "px";
}

// Expose utilities globally
window.UI = {
  requireAuth,
  redirectIfLoggedIn,
  showAlert,
  hideAlert,
  getActiveCorpusId,
  getActiveCorpusName,
  setActiveCorpus,
  formatTime,
  formatDate,
  escapeHtml,
  getFileIcon,
  getInitials,
  debounce,
  autoResizeTextarea,
};
