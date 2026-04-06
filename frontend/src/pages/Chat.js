import {
  getDialogue,
  getSession,
  sendMessage,
} from "../services_api/chat_api_client.js";

const params = new URLSearchParams(window.location.search);
let sessionId = params.get("session_id") || localStorage.getItem("session_id");
let userId = localStorage.getItem("user_id");

const messagesNode = document.getElementById("messages");
const historyNode = document.getElementById("offer-history-list");
const turnCounter = document.getElementById("turn-counter");
const messageForm = document.getElementById("message-form");
const messageInput = document.getElementById("message-input");
const offerInput = document.getElementById("offer-input");
const errorNode = document.getElementById("chat-error");
const typingNode = document.getElementById("typing-indicator");
const sendButton = document.getElementById("send-button");

if (!sessionId) {
  window.location.href = "Onboarding.html";
} else {
}

function currency(value) {
  if (value === null || value === undefined) {
    return "-";
  }
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}

function addBubble(text, who) {
  const bubble = document.createElement("div");
  bubble.className = `bubble ${who}`;
  bubble.textContent = text;
  messagesNode.appendChild(bubble);
  messagesNode.scrollTop = messagesNode.scrollHeight;
}

function renderOfferHistory(offers) {
  historyNode.innerHTML = "";
  offers.forEach((offer) => {
    const item = document.createElement("li");
    item.className = "offer-history-item";
    const change = offer.concession_amount === null || offer.concession_amount === undefined
      ? "-"
      : `${offer.concession_amount.toFixed(0)} (${(offer.concession_percentage || 0).toFixed(2)}%)`;

    item.innerHTML = `<span>T${offer.turn_number} ${offer.speaker}</span><span>${currency(offer.offer_amount)} | ${change}</span>`;
    historyNode.appendChild(item);
  });
}

async function refreshSession() {
  try {
    const session = await getSession(sessionId, userId);
    turnCounter.textContent = `${session.turn_count}/5`;

    if (session.turn_count >= 5 || session.outcome) {
      messageInput.disabled = true;
      offerInput.disabled = true;
      sendButton.disabled = true;
    }

    messagesNode.innerHTML = "";
    session.dialogue_turns.forEach((turn) => addBubble(turn.message, turn.speaker === "Human" ? "human" : "ai"));
    renderOfferHistory(session.offer_progression);
  } catch (error) {
    errorNode.textContent = error.message;
    errorNode.classList.remove("hidden");
  }
}

messageForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorNode.classList.add("hidden");

  const message = messageInput.value.trim();
  const offer = Number(offerInput.value);

  if (!message) {
    errorNode.textContent = "Message cannot be empty.";
    errorNode.classList.remove("hidden");
    return;
  }

  if (!offer || offer <= 0) {
    errorNode.textContent = "Offer must be a positive number.";
    errorNode.classList.remove("hidden");
    return;
  }

  sendButton.disabled = true;
  typingNode.classList.remove("hidden");

  try {
    addBubble(message, "human");
    const turnResult = await sendMessage(sessionId, { user_id: userId, message, offer });

    if (turnResult?.outcome) {
      localStorage.setItem("final_result", JSON.stringify(turnResult));
      window.location.href = `Results.html?session_id=${encodeURIComponent(sessionId)}`;
      return;
    }

    messageInput.value = "";
    offerInput.value = "";
    await refreshSession();
  } catch (error) {
    errorNode.textContent = error.message;
    errorNode.classList.remove("hidden");
  } finally {
    sendButton.disabled = false;
    typingNode.classList.add("hidden");
  }
});

if (sessionId) {
  refreshSession();
  getDialogue(sessionId, userId).catch(() => {});
}
