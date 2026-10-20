(() => {
  const DURATION_MS = 5000;

  function getToastStack() {
    let stack = document.querySelector(".toast-stack");
    if (!stack) {
      stack = document.createElement("div");
      stack.className = "toast-stack";
      document.body.appendChild(stack);
    }
    return stack;
  }

  // type: "success" | "error" | "info"
  function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `budget-toast budget-toast--${type}`;
    toast.setAttribute("role", type === "error" ? "alert" : "status");

    const text = document.createElement("span");
    text.className = "budget-toast__text";
    text.textContent = message;

    const close = document.createElement("button");
    close.type = "button";
    close.className = "budget-toast__close";
    close.setAttribute("aria-label", "Benachrichtigung schließen");
    close.textContent = "×";

    toast.append(text, close);
    getToastStack().appendChild(toast);

    const timeoutId = setTimeout(() => toast.remove(), DURATION_MS);
    close.addEventListener("click", () => {
      clearTimeout(timeoutId);
      toast.remove();
    });
  }

  window.showToast = showToast;
  window.getToastStack = getToastStack;
})();
