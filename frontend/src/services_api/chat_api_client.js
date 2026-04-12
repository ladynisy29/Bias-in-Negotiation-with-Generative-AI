const API_BASE =
  globalThis.__API_BASE__ ||
  localStorage.getItem("api_base") ||
  "http://127.0.0.1:8000/api";

const REQUEST_TIMEOUT_MS = Number(globalThis.__API_TIMEOUT_MS__ || 10000);
const MAX_RETRIES = Number(globalThis.__API_RETRIES__ || 1);

function readAccessToken() {
  return localStorage.getItem("access_token") || "";
}

function extractErrorMessage(payload, status) {
  if (!payload) {
    return `Request failed (${status})`;
  }
  if (typeof payload === "string") {
    return payload;
  }
  if (payload.error && typeof payload.error === "string") {
    return payload.error;
  }
  if (payload.detail && typeof payload.detail === "string") {
    return payload.detail;
  }
  if (typeof payload === "object") {
    const firstValue = Object.values(payload)[0];
    if (typeof firstValue === "string") {
      return firstValue;
    }
    if (Array.isArray(firstValue) && firstValue.length > 0) {
      return String(firstValue[0]);
    }
  }
  return JSON.stringify(payload);
}

async function request(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (!options.skipAuth) {
    const token = readAccessToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
  }

  let lastError = null;
  for (let attempt = 0; attempt <= MAX_RETRIES; attempt += 1) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
      const response = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers,
        signal: controller.signal,
      });

      clearTimeout(timeout);

      if (!response.ok) {
        let message = `Request failed (${response.status})`;
        let payload = null;
        try {
          const errorJson = await response.json();
          payload = errorJson;
          message = extractErrorMessage(errorJson, response.status);
        } catch {
          // Keep default message when response is not JSON.
        }
        const error = new Error(message);
        error.status = response.status;
        error.payload = payload;
        throw error;
      }

      const type = response.headers.get("content-type") || "";
      if (type.includes("application/json")) {
        return response.json();
      }
      return response.text();
    } catch (error) {
      clearTimeout(timeout);
      lastError = error;
      const isLast = attempt === MAX_RETRIES;
      if (isLast) {
        break;
      }
    }
  }

  if (lastError?.name === "AbortError") {
    throw new Error(`Request timed out after ${REQUEST_TIMEOUT_MS}ms`);
  }
  throw lastError || new Error("Request failed.");
}

export function registerUser(payload) {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
    skipAuth: true,
  });
}

export function loginUser(username, password) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
    skipAuth: true,
  });
}

export function logoutUser() {
  return request("/auth/logout", {
    method: "POST",
  });
}

export function startSession() {
  return request("/start-session", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function getSession(sessionId) {
  return request(`/session/${sessionId}`);
}

export function sendMessage(sessionId, payload) {
  return request(`/session/${sessionId}/send-message`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getDialogue(sessionId) {
  return request(`/session/${sessionId}/dialogue`);
}

export function submitFinalOffer(sessionId, payload) {
  return request(`/session/${sessionId}/submit-final-offer`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function exportTranscript(sessionId) {
  return request(`/export/session/${sessionId}/transcript`);
}

export function createTestUser(username = "chatuser", profile = {}) {
  return request("/auth/dev-create-user", {
    method: "POST",
    body: JSON.stringify({ username, ...profile }),
    skipAuth: true,
  });
}
