// Dark Mode beim Laden anwenden
(function () {
  const isDarkMode = localStorage.getItem("darkMode") === "true";
  if (isDarkMode) {
    document.body.classList.add("dark-mode");
  }
})();

const MONTHS_DE = [
  "Januar",
  "Februar",
  "März",
  "April",
  "Mai",
  "Juni",
  "Juli",
  "August",
  "September",
  "Oktober",
  "November",
  "Dezember",
];
const MONTHS_SHORT = [
  "Jan",
  "Feb",
  "Mär",
  "Apr",
  "Mai",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Okt",
  "Nov",
  "Dez",
];

const today = new Date();
let currentYear = today.getFullYear();
let currentMonth = today.getMonth(); // 0-basiert

// Globale Datenstruktur für die aktuell geladenen Einträge
let entries = [];
let ctxTargetId = null;
let editingEntryKey = null; // description|day|month|year (für Update/Delete, falls du später Update-Route baust)

const fmtNum = (v) =>
  Math.abs(v).toLocaleString("de-DE", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }) + " €";
const fmtSigned = (v) => (v < 0 ? "–" : "+") + fmtNum(v);
const fmtDate = (d) =>
  d.toLocaleDateString("de-DE", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });

// ---------------------------------------------------------------------
// API-Helper
// ---------------------------------------------------------------------

async function fetchJSON(url) {
  const res = await fetch(url, {
    credentials: "same-origin",
    headers: { "X-Requested-With": "XMLHttpRequest" },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res.json();
}

async function postForm(url, data) {
  const formData = new FormData();
  Object.entries(data).forEach(([k, v]) => formData.append(k, v));
  const res = await fetch(url, {
    method: "POST",
    credentials: "same-origin",
    headers: { "X-Requested-With": "XMLHttpRequest" },
    body: formData,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res.text();
}

// ---------------------------------------------------------------------
// Daten laden
// ---------------------------------------------------------------------

async function loadSummary() {
  const monthParam = currentMonth + 1; // Flask erwartet 1-12
  const yearParam = currentYear;

  const data = await fetchJSON(
    `/expensePlanner/summary?month=${monthParam}&year=${yearParam}`
  );

  if (data.error) {
    console.error("Fehler Summary:", data.error);
    return;
  }

  const budget = data.budget || 0;
  const expenseSum = data.expenseSum || 0;
  const saved = data.saved || 0;
  const expensePercentage = data.expensePercentage || 0;

  const budgetAmountEl = document.getElementById("budgetAmount");
  const statExpensesEl = document.getElementById("statExpenses");
  const statBalanceEl = document.getElementById("statBalance");
  const statAvailableEl = document.getElementById("statAvailable");
  const progressLabelEl = document.getElementById("progressLabel");
  const progressRemainingEl = document.getElementById("progressRemaining");
  const progressFillEl = document.getElementById("progressFill");

  const spent = expenseSum < 0 ? Math.abs(expenseSum) : expenseSum;
  const available = budget - spent;
  const pct = budget > 0 ? Math.min(expensePercentage, 100) : 0;

  // Budget (globalBudget identisch zu budget bei dir)
  budgetAmountEl.textContent = fmtNum(budget);

  // Ausgaben
  statExpensesEl.textContent = "–" + fmtNum(spent);

  // Bilanz (saved)
  statBalanceEl.textContent =
    (saved >= 0 ? "+" : "–") + fmtNum(saved);
  statBalanceEl.className =
    "stat-value " + (saved >= 0 ? "positive" : "negative");

  // Verfügbar (Budget - Ausgaben)
  statAvailableEl.textContent = fmtNum(available);
  statAvailableEl.className =
    "stat-value " + (available < 0 ? "negative" : "positive");

  // Fortschrittsbalken
  progressLabelEl.textContent = `${pct.toFixed(0)} % ausgegeben`;
  progressRemainingEl.textContent =
    available >= 0
      ? `${fmtNum(available)} verfügbar`
      : `${fmtNum(Math.abs(available))} überzogen`;

  progressFillEl.style.width = `${pct}%`;
  if (pct >= 100) {
    progressFillEl.className = "progress-fill over";
  } else if (pct >= 75) {
    progressFillEl.className = "progress-fill warn";
  } else {
    progressFillEl.className = "progress-fill";
  }
}

async function loadEntries() {
  const monthParam = currentMonth + 1;
  const yearParam = currentYear;

  const data = await fetchJSON(
    `/expensePlanner/get?month=${monthParam}&year=${yearParam}`
  );

  if (data.error) {
    console.error("Fehler Einträge:", data.error);
    entries = [];
  } else {
    // data = [{ day, month, year, amount, description }]
  // Ausgabe = positiv im Backend -> negativ für Anzeige umrechnen
  entries = data.map((r, index) => ({
  id: index + 1,
  desc: r.description,
  amount: r.amount > 0 ? -r.amount : r.amount, // Ausgaben positiv -> für Anzeige negativ
  date: new Date(r.year, r.month - 1, r.day),
  key: `${r.description}|${r.day}|${r.month}|${r.year}`,
  }));

  renderEntriesOnly();
}}

// ---------------------------------------------------------------------
// Monatspicker
// ---------------------------------------------------------------------

const monthPickerBtn = document.getElementById("monthPickerBtn");
const monthPickerLabel = document.getElementById("monthPickerLabel");
const monthPopover = document.getElementById("monthPopover");
const popoverYear = document.getElementById("popoverYear");
const monthsGrid = document.getElementById("monthsGrid");

function updatePickerLabel() {
  monthPickerLabel.textContent = `${MONTHS_DE[currentMonth]} ${currentYear}`;
}

function renderMonthsGrid() {
  popoverYear.textContent = currentYear;
  monthsGrid.innerHTML = "";
  MONTHS_SHORT.forEach((m, i) => {
    const cell = document.createElement("div");
    cell.className = "month-cell";
    if (i === currentMonth) cell.classList.add("active");
    if (i === today.getMonth() && currentYear === today.getFullYear())
      cell.classList.add("today-month");
    cell.textContent = m;
    cell.addEventListener("click", async () => {
      currentMonth = i;
      updatePickerLabel();
      renderMonthsGrid();
      monthPopover.classList.remove("open");
      await refreshAllData();
    });
    monthsGrid.appendChild(cell);
  });
}

monthPickerBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  const rect = monthPickerBtn.getBoundingClientRect();
  monthPopover.style.top = rect.bottom + 8 + "px";
  monthPopover.style.right = window.innerWidth - rect.right + "px";
  renderMonthsGrid();
  monthPopover.classList.toggle("open");
});

document.getElementById("prevYear").addEventListener("click", (e) => {
  e.stopPropagation();
  currentYear--;
  renderMonthsGrid();
});

document.getElementById("nextYear").addEventListener("click", (e) => {
  e.stopPropagation();
  currentYear++;
  renderMonthsGrid();
});

// ---------------------------------------------------------------------
// Render-Einträge (nur Kacheln, Summary kommt aus loadSummary)
// ---------------------------------------------------------------------

function renderEntriesOnly() {
  const entriesLabel = document.getElementById("entriesLabel");
  const list = document.getElementById("entriesList");

  entriesLabel.textContent = `${MONTHS_DE[currentMonth]} ${currentYear}`;
  list.innerHTML = "";

  if (!entries || entries.length === 0) {
    list.innerHTML = `
      <div class="empty-state">
        <div class="icon">📭</div>
        <p>Keine Einträge für diesen Monat.</p>
      </div>`;
    return;
  }

  [...entries]
    .sort((a, b) => b.date - a.date)
    .forEach((entry) => {
      const tile = document.createElement("div");
      tile.className = "entry-tile";
      tile.innerHTML = `
        <div class="entry-info">
          <div class="entry-description">${entry.desc}</div>
          <div class="entry-date">${fmtDate(entry.date)}</div>
        </div>
        <div class="entry-amount ${
          entry.amount < 0 ? "negative" : "positive"
        }">${fmtSigned(entry.amount)}</div>
        <button class="tile-menu-btn" data-key="${
          entry.key
        }" title="Optionen">⋯</button>`;

      tile
        .querySelector(".tile-menu-btn")
        .addEventListener("click", (e) => openContextMenu(e, entry.key));

      list.appendChild(tile);
    });
}

// ---------------------------------------------------------------------
// Kontextmenü (Bearbeiten/Löschen – aktuell nur Löschen aktiv mit Route)
// ---------------------------------------------------------------------

const contextMenu = document.getElementById("contextMenu");

function openContextMenu(e, key) {
  e.stopPropagation();
  ctxTargetId = key;
  const rect = e.currentTarget.getBoundingClientRect();
  let top = rect.bottom + 4;
  let left = rect.right - 160;
  if (left < 8) left = 8;
  if (top + 100 > window.innerHeight) top = rect.top - 100;
  contextMenu.style.top = top + "px";
  contextMenu.style.left = left + "px";
  contextMenu.classList.add("open");
}

document.getElementById("ctxEdit").addEventListener("click", () => {
  // Platzhalter – du hast aktuell keine Update-Route.
  // Wenn du später eine Update-Route hast, kannst du hier ein Dialog öffnen
  // und mit editingEntryKey arbeiten.
  contextMenu.classList.remove("open");
  alert("Bearbeiten ist noch nicht an die Backend-Route angebunden.");
});

document.getElementById("ctxDelete").addEventListener("click", async () => {
  if (!ctxTargetId) return;
  contextMenu.classList.remove("open");

  try {
    await postForm("/expensePlanner/remove", { entry: ctxTargetId });
    // Lokales Array aktualisieren
    entries = entries.filter((e) => e.key !== ctxTargetId);
    renderEntriesOnly();
    // Summary neu laden, weil sich Ausgaben/Budget geändert haben
    await loadSummary();
  } catch (err) {
    console.error(err);
    alert("Fehler beim Entfernen: " + err.message);
  }
});

// ---------------------------------------------------------------------
// Dialog Neu-Eintrag -> POST /expensePlanner/add
// ---------------------------------------------------------------------

const dialogOverlay = document.getElementById("dialogOverlay");
const fabBtn = document.getElementById("fabBtn");

function openDialogForNew() {
  editingEntryKey = null;
  document.getElementById("dialogTitle").textContent = "Neuer Eintrag";
  document.getElementById("inputDesc").value = "";
  document.getElementById("inputAmount").value = "";
  document.getElementById("inputType").value = "expense";
  dialogOverlay.classList.add("open");
}

fabBtn.addEventListener("click", () => openDialogForNew());

document
  .getElementById("dialogCancel")
  .addEventListener("click", () =>
    dialogOverlay.classList.remove("open")
  );

dialogOverlay.addEventListener("click", (e) => {
  if (e.target === dialogOverlay) dialogOverlay.classList.remove("open");
});

document
  .getElementById("dialogSave")
  .addEventListener("click", async () => {
    const desc = document.getElementById("inputDesc").value.trim();
    const amountRaw = parseFloat(
      document.getElementById("inputAmount").value
    );
    const type = document.getElementById("inputType").value;

    if (!desc || isNaN(amountRaw) || amountRaw <= 0) {
      alert("Bitte Beschreibung und gültigen Betrag eingeben.");
      return;
    }

    // Backend erwartet immer positive amount und entscheidet intern,
    // ob es Ausgabe oder Einnahme ist? -> Du kannst hier ggf. Vorzeichen setzen.
    const finalAmount = type === "expense" ? Math.abs(amountRaw) : -Math.abs(amountRaw);

    const day = today.getDate();
    const month = currentMonth + 1;
    const year = currentYear;

    try {
      await postForm("/expensePlanner/add", {
        amount: finalAmount,
        description: desc,
        day,
        month,
        year,
      });

      dialogOverlay.classList.remove("open");

      // Nach Speichern Backend erneut abfragen
      await refreshAllData();
    } catch (err) {
      console.error(err);
      alert("Fehler beim Speichern: " + err.message);
    }
  });

// ---------------------------------------------------------------------
// Globales Schließen von Popover / Kontextmenü
// ---------------------------------------------------------------------

document.addEventListener("click", () => {
  contextMenu.classList.remove("open");
  monthPopover.classList.remove("open");
});

// ---------------------------------------------------------------------
// Initial
// ---------------------------------------------------------------------

async function refreshAllData() {
  await Promise.all([loadSummary(), loadEntries()]);
}

updatePickerLabel();
refreshAllData().catch((e) => console.error(e));
