const API_BASE = "http://127.0.0.1:8000/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    let payload = null;
    try {
      const errorJson = await response.json();
      payload = errorJson;
      message = errorJson.error || errorJson.detail || JSON.stringify(errorJson);
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
}

export function startSession(userId, initialOffer) {
  return request("/start-session", {
    method: "POST",
    body: JSON.stringify({ user_id: userId, initial_offer: initialOffer }),
  });
}

export function getSession(sessionId, userId) {
  const query = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
  return request(`/session/${sessionId}${query}`);
}

export function sendMessage(sessionId, payload) {
  return request(`/session/${sessionId}/send-message`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getDialogue(sessionId, userId) {
  const query = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
  return request(`/session/${sessionId}/dialogue${query}`);
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
  });
}
