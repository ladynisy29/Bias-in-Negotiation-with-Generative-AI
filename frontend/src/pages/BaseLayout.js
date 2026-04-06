function toggleNavigation() {
  const navList = document.querySelector("nav ul");
  if (navList) {
    navList.classList.toggle("active");
  }
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme");
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("theme", next);
}

function restoreTheme() {
  const saved = localStorage.getItem("theme") || "light";
  document.documentElement.setAttribute("data-theme", saved);
}

function initHomePage() {
  const userNode = document.getElementById("home-user-id");
  const sessionNode = document.getElementById("home-session-id");
  const clearButton = document.getElementById("clear-local-session");

  if (!userNode || !sessionNode || !clearButton) {
    return;
  }

  const userId = localStorage.getItem("user_id");
  const sessionId = localStorage.getItem("session_id");

  userNode.textContent = userId || "Not set";
  sessionNode.textContent = sessionId || "Not set";

  clearButton.addEventListener("click", () => {
    localStorage.removeItem("user_id");
    localStorage.removeItem("session_id");
    localStorage.removeItem("final_result");
    userNode.textContent = "Not set";
    sessionNode.textContent = "Not set";
  });
}

window.appLayout = {
  toggleNavigation,
  toggleTheme,
};

restoreTheme();
initHomePage();
