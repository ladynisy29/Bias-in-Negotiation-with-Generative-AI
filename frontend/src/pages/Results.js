import { exportTranscript, getSession } from "../services_api/chat_api_client.js";

const params = new URLSearchParams(window.location.search);
const sessionId = params.get("session_id") || localStorage.getItem("session_id");
const userId = localStorage.getItem("user_id");

const outcomeNode = document.getElementById("outcome-badge");
const finalPriceNode = document.getElementById("final-price");
const reserveNode = document.getElementById("reserve-price");
const profitNode = document.getElementById("profit-value");
const turnsNode = document.getElementById("turns-used");
const sessionIdNode = document.getElementById("session-id");
const durationNode = document.getElementById("session-duration");
const concessionBody = document.getElementById("concession-body");
const exportButton = document.getElementById("export-btn");

function currency(value) {
  if (value === null || value === undefined) {
    return "-";
  }
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}

function renderTable(offers) {
  concessionBody.innerHTML = "";
  offers
    .filter((item) => item.speaker === "Human")
    .forEach((item) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${item.turn_number}</td>
        <td>${currency(item.offer_amount)}</td>
        <td>${item.concession_amount === null || item.concession_amount === undefined ? "-" : item.concession_amount.toFixed(0)}</td>
        <td>${item.concession_percentage === null || item.concession_percentage === undefined ? "-" : item.concession_percentage.toFixed(2) + "%"}</td>
      `;
      concessionBody.appendChild(row);
    });
}

async function load() {
  if (!sessionId) {
    outcomeNode.textContent = "Missing session id";
    outcomeNode.className = "outcome-banner outcome-rejected";
    return;
  }

  const session = await getSession(sessionId, userId);
  const finalResult = localStorage.getItem("final_result");
  const parsed = finalResult ? JSON.parse(finalResult) : null;

  outcomeNode.textContent = session.outcome === "Accepted" ? "Deal Accepted" : "Deal Declined";
  outcomeNode.className = `outcome-banner ${session.outcome === "Accepted" ? "outcome-accepted" : "outcome-rejected"}`;

  finalPriceNode.textContent = currency(session.final_offer);
  reserveNode.textContent = parsed ? currency(parsed.acceptance_threshold) : "-";
  profitNode.textContent = parsed ? currency(parsed.human_profit) : "-";
  turnsNode.textContent = `${session.turn_count} / 5`;
  sessionIdNode.textContent = session.session_id;
  durationNode.textContent = session.outcome ? "Completed" : "In progress";

  renderTable(session.offer_progression || []);
}

exportButton.addEventListener("click", async (event) => {
  event.preventDefault();
  const transcript = await exportTranscript(sessionId);
  const blob = new Blob([JSON.stringify(transcript, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `session-${sessionId}-transcript.json`;
  anchor.click();
  URL.revokeObjectURL(url);
});

load().catch((error) => {
  outcomeNode.textContent = `Error: ${error.message}`;
  outcomeNode.className = "outcome-banner outcome-rejected";
});
