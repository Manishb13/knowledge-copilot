/**
 * API Client for Domain Knowledge Co-Pilot
 * All HTTP requests to the FastAPI backend go through this module.
 */

const API_BASE = window.API_BASE || "http://localhost:8000/api";

/**
 * Read the JWT token from localStorage.
 * @returns {string|null}
 */
function getToken() {
  return localStorage.getItem("kc_token");
}

/**
 * Store authentication data in localStorage.
 * @param {string} token
 * @param {number} userId
 * @param {string} email
 */
function saveAuth(token, userId, email) {
  localStorage.setItem("kc_token", token);
  localStorage.setItem("kc_user_id", String(userId));
  localStorage.setItem("kc_email", email);
}

/**
 * Clear authentication data from localStorage.
 */
function clearAuth() {
  localStorage.removeItem("kc_token");
  localStorage.removeItem("kc_user_id");
  localStorage.removeItem("kc_email");
}

/**
 * Check if the user is logged in.
 * @returns {boolean}
 */
function isLoggedIn() {
  return !!getToken();
}

/**
 * Get the stored user email.
 * @returns {string}
 */
function getUserEmail() {
  return localStorage.getItem("kc_email") || "";
}

/**
 * Core fetch wrapper that attaches the Bearer token and handles errors.
 * @param {string} endpoint - API path (e.g. '/corpora')
 * @param {RequestInit} options - fetch options
 * @returns {Promise<any>}
 */
async function apiFetch(endpoint, options = {}) {
  const token = getToken();
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Don't set Content-Type for FormData — browser sets it with boundary
  if (options.body instanceof FormData) {
    delete headers["Content-Type"];
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 204) {
    return null;
  }

  const data = await response.json().catch(() => ({ detail: "Unknown error" }));

  if (!response.ok) {
    const message =
      typeof data.detail === "string"
        ? data.detail
        : Array.isArray(data.detail)
        ? data.detail.map((e) => e.msg).join("; ")
        : "An unexpected error occurred";
    throw new Error(message);
  }

  return data;
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

/**
 * Register a new user.
 * @param {string} email
 * @param {string} password
 * @returns {Promise<{access_token: string, user_id: number, email: string}>}
 */
async function signup(email, password) {
  return apiFetch("/signup", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

/**
 * Authenticate an existing user.
 * @param {string} email
 * @param {string} password
 * @returns {Promise<{access_token: string, user_id: number, email: string}>}
 */
async function login(email, password) {
  return apiFetch("/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

// ─── Corpora ──────────────────────────────────────────────────────────────────

/**
 * Create a new corpus.
 * @param {string} name
 * @param {string} [description]
 * @returns {Promise<object>}
 */
async function createCorpus(name, description = "") {
  return apiFetch("/corpora", {
    method: "POST",
    body: JSON.stringify({ name, description: description || null }),
  });
}

/**
 * List all corpora for the current user.
 * @returns {Promise<{corpora: object[]}>}
 */
async function listCorpora() {
  return apiFetch("/corpora");
}

/**
 * Delete a corpus.
 * @param {number} corpusId
 * @returns {Promise<null>}
 */
async function deleteCorpus(corpusId) {
  return apiFetch(`/corpora/${corpusId}`, { method: "DELETE" });
}

// ─── Upload ───────────────────────────────────────────────────────────────────

/**
 * Upload a document to a corpus.
 * @param {number} corpusId
 * @param {File} file
 * @param {function(number): void} [onProgress] - called with 0-100 progress
 * @returns {Promise<object>}
 */
async function uploadDocument(corpusId, file, onProgress) {
  const token = getToken();
  const formData = new FormData();
  formData.append("file", file);

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE}/corpora/${corpusId}/upload`);

    if (token) {
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    }

    if (onProgress) {
      xhr.upload.addEventListener("progress", (e) => {
        if (e.lengthComputable) {
          onProgress(Math.round((e.loaded / e.total) * 80));
        }
      });
    }

    xhr.onload = () => {
      if (onProgress) onProgress(100);
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText));
        } catch {
          reject(new Error("Invalid response from server"));
        }
      } else {
        try {
          const err = JSON.parse(xhr.responseText);
          reject(new Error(err.detail || `Upload failed (${xhr.status})`));
        } catch {
          reject(new Error(`Upload failed (${xhr.status})`));
        }
      }
    };

    xhr.onerror = () => reject(new Error("Network error during upload"));
    xhr.ontimeout = () => reject(new Error("Upload timed out"));
    xhr.timeout = 120000;

    xhr.send(formData);
  });
}

// ─── Query ────────────────────────────────────────────────────────────────────

/**
 * Submit a question to a corpus.
 * @param {number} corpusId
 * @param {string} question
 * @returns {Promise<{answer: string, citations: object[], corpus_id: number}>}
 */
async function queryCorpus(corpusId, question) {
  return apiFetch(`/corpora/${corpusId}/query`, {
    method: "POST",
    body: JSON.stringify({ question }),
  });
}

/**
 * Get the conversation history for a corpus.
 * @param {number} corpusId
 * @returns {Promise<object[]>}
 */
async function getChatHistory(corpusId) {
  return apiFetch(`/corpora/${corpusId}/history`);
}

/**
 * Clear the conversation history for a corpus.
 * @param {number} corpusId
 * @returns {Promise<null>}
 */
async function clearChatHistory(corpusId) {
  return apiFetch(`/corpora/${corpusId}/history`, { method: "DELETE" });
}

// ─── Exports ──────────────────────────────────────────────────────────────────

window.KC = {
  getToken,
  saveAuth,
  clearAuth,
  isLoggedIn,
  getUserEmail,
  signup,
  login,
  createCorpus,
  listCorpora,
  deleteCorpus,
  uploadDocument,
  queryCorpus,
  getChatHistory,
  clearChatHistory,
};
