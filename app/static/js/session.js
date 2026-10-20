(() => {
  const nav = document.querySelector(".top-nav");
  const LIFETIME_MS = Number(nav.dataset.sessionLifetime) * 1000;
  const STORAGE_KEY = "budget.lastServerContact";

  function markServerContact() {
    localStorage.setItem(STORAGE_KEY, String(Date.now()));
  }

  function remainingMs() {
    const last = Number(localStorage.getItem(STORAGE_KEY));
    return ( last + LIFETIME_MS ) - Date.now();
  }

  const originalFetch = window.fetch;

  window.fetch = async (...args) => {
    const response = await originalFetch(...args);
    if (response.redirected) {
        window.location.href = "/logout";
    } 
    else {
        markServerContact();
    }
    return response;
  };

  // Die Seite kam gerade vom Server, also wurde die Session soeben verlängert
  markServerContact();

  let toast = null;

  function showWarning(seconds) {
    if (!toast) {
      toast = document.createElement("div");
      toast.className = "budget-toast budget-toast--warning";
      toast.setAttribute("role", "alert");

      const text = document.createElement("span");
      text.className = "budget-toast__text";

      const button = document.createElement("button");
      button.type = "button";
      button.className = "budget-toast__action";
      button.textContent = "Verlängern";
      button.addEventListener("click", extendSession);

      toast.append(text, button);
      window.getToastStack().prepend(toast);
    }
    toast.querySelector(".budget-toast__text").textContent =
      `Deine Sitzung läuft in ${seconds} s ab.`;
  }

  function hideWarning() {
    if (toast) {
      toast.remove();
      toast = null;
    }
  }

  async function extendSession() {
    await fetch("/session/refresh", { method: "POST" });
  }

  setInterval(() => {
    const seconds = Math.round(remainingMs() / 1000);
    if ( seconds <= 0 ) {
        window.location.href = "/logout";
    }
    else if ( seconds <= 60 ) {
        showWarning(seconds);
    }
    else {
        hideWarning();
    }
  }, 1000);

})();