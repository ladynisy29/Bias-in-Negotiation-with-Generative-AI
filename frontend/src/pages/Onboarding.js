import { createTestUser, startSession } from "../services_api/chat_api_client.js";

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

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();

  const gender = document.getElementById("gender").value.trim();
  const ageValue = document.getElementById("age").value.trim();
  const location = document.getElementById("location").value.trim();
  const nationality = document.getElementById("nationality").value.trim();

  nextButton.disabled = true;

  try {
    setStatus("Creating participant...");
    const participant = await createTestUser("participant", {
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
