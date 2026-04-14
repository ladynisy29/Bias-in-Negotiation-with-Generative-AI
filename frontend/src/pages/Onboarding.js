import { registerUser, startSession } from "../services_api/chat_api_client.js";

const form = document.getElementById("onboarding-form");
const nextButton = document.getElementById("next-button");
const statusNode = document.getElementById("onboarding-status");
const errorNode = document.getElementById("onboarding-error");

function setStatus(text) {
  if (statusNode) {
    statusNode.textContent = text;
  }
}

function showError(text) {
  if (!errorNode) {
    return;
  }
  errorNode.textContent = text;
  errorNode.classList.remove("hidden");
}

function clearError() {
  if (!errorNode) {
    return;
  }
  errorNode.textContent = "";
  errorNode.classList.add("hidden");
}

function randomString(length = 10) {
  const alphabet = "abcdefghijklmnopqrstuvwxyz0123456789";
  let out = "";
  for (let index = 0; index < length; index += 1) {
    out += alphabet[Math.floor(Math.random() * alphabet.length)];
  }
  return out;
}

function buildParticipantCredentials() {
  const suffix = `${Date.now().toString(36)}${randomString(4)}`;
  return {
    username: `participant_${suffix}`,
    password: `P!${randomString(14)}Aa9`,
  };
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();

  const gender = document.getElementById("gender").value.trim();
  const ageValue = document.getElementById("age").value.trim();
  const location = document.getElementById("location").value.trim();
  const nationality = document.getElementById("nationality").value.trim();

  nextButton.disabled = true;

  try {
    setStatus("Creating participant account...");
    const credentials = buildParticipantCredentials();
    const participant = await registerUser({
      username: credentials.username,
      password: credentials.password,
      gender,
      age: ageValue || null,
      location,
      nationality,
    });

    setStatus("Starting negotiation session...");
    localStorage.setItem("access_token", participant.access_token || "");
    const session = await startSession();

    localStorage.setItem("user_id", participant.user_id);
    localStorage.setItem("session_id", session.session_id);
    localStorage.setItem(
      "participant_profile",
      JSON.stringify({
        gender,
        age: ageValue || "",
        location,
        nationality,
      })
    );

    setStatus("Redirecting to negotiation...");
    window.location.href = `Chat.html?session_id=${encodeURIComponent(session.session_id)}`;
  } catch (error) {
    showError(error.message || "Unable to start negotiation.");
  } finally {
    nextButton.disabled = false;
  }
});
