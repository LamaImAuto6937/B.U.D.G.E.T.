// Dark Mode beim Laden anwenden
(function () {
  const isDarkMode = localStorage.getItem("darkMode") === "true";
  if (isDarkMode) document.body.classList.add("dark-mode");
})();

// ── KONSTANTEN & GLOBALS ─────────────────────────────────────────────
const MONTHS_DE = [
  "Januar","Februar","März","April","Mai","Juni",
  "Juli","August","September","Oktober","November","Dezember",
];
const MONTHS_SHORT = [
  "Jan","Feb","Mär","Apr","Mai","Jun",
  "Jul","Aug","Sep","Okt","Nov","Dez",
];

const today       = new Date();
let currentYear   = today.getFullYear();
let currentMonth  = today.getMonth(); // 0-basiert
let entries       = [];
let ctxTargetId   = null;
let editingEntry  = null;
let budgetIsSet   = false;
let suggestedBudget = 0;

// Kalender-State
let calYear       = today.getFullYear();
let calMonth      = today.getMonth();
let selectedDay   = today.getDate();
let selectedMonth = today.getMonth() + 1;
let selectedYear  = today.getFullYear();

// ── FORMAT-HELPER ────────────────────────────────────────────────────
const pad       = (n) => String(n).padStart(2, "0");
const fmtNum    = (v) =>
  Math.abs(v).toLocaleString("de-DE", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " €";
const fmtSigned = (v) => (v < 0 ? "–" : "+") + fmtNum(v);
const fmtDate   = (d) =>
  d.toLocaleDateString("de-DE", { day: "2-digit", month: "short", year: "numeric" });

// ── API-HELPER ───────────────────────────────────────────────────────
async function fetchJSON(url) {
  const res = await fetch(url, {
    credentials: "same-origin",
    headers: { "X-Requested-With": "XMLHttpRequest" },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json();
}

async function postForm(url, data) {
  const fd = new FormData();
  Object.entries(data).forEach(([k, v]) => fd.append(k, v));
  const res = await fetch(url, {
    method: "POST",
    credentials: "same-origin",
    headers: { "X-Requested-With": "XMLHttpRequest" },
    body: fd,
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.text();
}

// ── DATEN LADEN ──────────────────────────────────────────────────────
async function loadSummary() {
  const data = await fetchJSON(
    `/expensePlanner/summary?month=${currentMonth + 1}&year=${currentYear}`
  );
  if (data.error) { console.error("Summary Fehler:", data.error); return; }

  // needsBudget = true  → kein Budget gesetzt → Popup zeigen
  // needsBudget = false → Budget vorhanden    → alles normal
  budgetIsSet     = !data.needsBudget;
  suggestedBudget = data.globalBudget || data.budget || 0;

  const budget     = data.budget           || 0;
  const expenseSum = data.expenseSum        || 0;
  const saved      = data.saved             || 0;
  const pct        = data.expensePercentage || 0;
  const spent      = Math.abs(expenseSum);
  const available  = budget - spent;
  const pctCapped  = budget > 0 ? Math.min(pct, 100) : 0;

  document.getElementById("budgetAmount").textContent = fmtNum(budget);
  document.getElementById("statExpenses").textContent = "–" + fmtNum(spent);

  const balEl = document.getElementById("statBalance");
  balEl.textContent = (saved >= 0 ? "+" : "–") + fmtNum(saved);
  balEl.className   = "stat-value " + (saved >= 0 ? "positive" : "negative");

  const avEl = document.getElementById("statAvailable");
  avEl.textContent = fmtNum(available);
  avEl.className   = "stat-value " + (available < 0 ? "negative" : "positive");

  document.getElementById("progressLabel").textContent =
    `${pctCapped.toFixed(0)} % ausgegeben`;
  document.getElementById("progressRemaining").textContent =
    available >= 0 ? `${fmtNum(available)} verfügbar` : `${fmtNum(Math.abs(available))} überzogen`;

  const fill = document.getElementById("progressFill");
  fill.style.width = `${pctCapped}%`;
  fill.className   = "progress-fill" + (pctCapped >= 100 ? " over" : pctCapped >= 75 ? " warn" : "");

  updateFabState();

  if (data.needsBudget) {
    showBudgetPopup();
  }
}

async function loadEntries() {
  const data = await fetchJSON(
    `/expensePlanner/get?month=${currentMonth + 1}&year=${currentYear}`
  );
  if (data.error) { console.error("Einträge Fehler:", data.error); entries = []; }
  else {
    entries = data.map((r) => ({
      id:     r.id,
      desc:   r.description,
      amount: -r.amount,
      date:   new Date(r.year, r.month - 1, r.day),
      day:    r.day,
      month:  r.month,
      year:   r.year,
    }));
  }
  renderEntriesOnly();
}

async function refreshAllData() {
  await Promise.all([loadSummary(), loadEntries()]);
}

// ── FAB ZUSTAND ──────────────────────────────────────────────────────
function updateFabState() {
  const fab = document.getElementById("fabBtn");
  if (budgetIsSet) {
    fab.disabled = false;
    fab.classList.remove("fab-disabled");
    fab.title = "";
  } else {
    fab.disabled = true;
    fab.classList.add("fab-disabled");
    fab.title = "Bitte zuerst ein Budget festlegen";
  }

  document.querySelectorAll(".tile-menu-btn").forEach((btn) => {
    btn.disabled = !budgetIsSet;
    btn.classList.toggle("fab-disabled", !budgetIsSet);
  });
}

// ── BUDGET POPUP ─────────────────────────────────────────────────────
const budgetOverlay = document.getElementById("budgetOverlay");

function showBudgetPopup() {
  document.getElementById("budgetSuggestionAmount").textContent =
    fmtNum(suggestedBudget);
  budgetOverlay.classList.add("open");
}

document.getElementById("budgetConfirm").addEventListener("click", async () => {
  budgetOverlay.classList.remove("open");
  try {
    await postForm("/expensePlanner/setBudget", {
      amount: suggestedBudget,
      month:  currentMonth + 1,
      year:   currentYear,
    });
    budgetIsSet = true;
    updateFabState();
    await refreshAllData();
  } catch (err) {
    console.error(err);
    alert("Fehler beim Speichern des Budgets: " + err.message);
  }
});

document.getElementById("budgetDeny").addEventListener("click", () => {
  budgetOverlay.classList.remove("open");
});

// ── MONATSPICKER ─────────────────────────────────────────────────────
const monthPickerBtn   = document.getElementById("monthPickerBtn");
const monthPickerLabel = document.getElementById("monthPickerLabel");
const monthPopover     = document.getElementById("monthPopover");

function updatePickerLabel() {
  monthPickerLabel.textContent = `${MONTHS_DE[currentMonth]} ${currentYear}`;
}

function renderMonthsGrid() {
  document.getElementById("popoverYear").textContent = currentYear;
  const grid = document.getElementById("monthsGrid");
  grid.innerHTML = "";
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
    grid.appendChild(cell);
  });
}

monthPickerBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  const rect = monthPickerBtn.getBoundingClientRect();
  monthPopover.style.top   = rect.bottom + 8 + "px";
  monthPopover.style.right = window.innerWidth - rect.right + "px";
  renderMonthsGrid();
  monthPopover.classList.toggle("open");
});

document.getElementById("prevYear").addEventListener("click", (e) => {
  e.stopPropagation(); currentYear--; renderMonthsGrid();
});
document.getElementById("nextYear").addEventListener("click", (e) => {
  e.stopPropagation(); currentYear++; renderMonthsGrid();
});

// ── EINTRÄGE RENDERN ─────────────────────────────────────────────────
function renderEntriesOnly() {
  document.getElementById("entriesLabel").textContent =
    `${MONTHS_DE[currentMonth]} ${currentYear}`;
  const list = document.getElementById("entriesList");
  list.innerHTML = "";

  if (!entries || entries.length === 0) {
    list.innerHTML = `
      <div class="empty-state">
        <div class="icon">📭</div>
        <p>Keine Einträge für diesen Monat.</p>
      </div>`;
    return;
  }

  [...entries].sort((a, b) => b.date - a.date).forEach((entry) => {
    const tile = document.createElement("div");
    tile.className = "entry-tile";
    tile.innerHTML = `
      <div class="entry-info">
        <div class="entry-description">${entry.desc}</div>
        <div class="entry-date">${fmtDate(entry.date)}</div>
      </div>
      <div class="entry-amount ${entry.amount < 0 ? "negative" : "positive"}">
        ${fmtSigned(entry.amount)}
      </div>
      <button class="tile-menu-btn" data-id="${entry.id}" title="Optionen">⋯</button>`;
    tile.querySelector(".tile-menu-btn")
        .addEventListener("click", (e) => openContextMenu(e, entry.id));
    list.appendChild(tile);
  });
}

// ── KONTEXTMENÜ ──────────────────────────────────────────────────────
const contextMenu = document.getElementById("contextMenu");

function openContextMenu(e, entryId) {
  if (!budgetIsSet) return;
  e.stopPropagation();
  ctxTargetId = entryId;
  const rect = e.currentTarget.getBoundingClientRect();
  let top  = rect.bottom + 4;
  let left = rect.right - 160;
  if (left < 8) left = 8;
  if (top + 110 > window.innerHeight) top = rect.top - 110;
  contextMenu.style.top  = top + "px";
  contextMenu.style.left = left + "px";
  contextMenu.classList.add("open");
}

document.getElementById("ctxEdit").addEventListener("click", () => {
  contextMenu.classList.remove("open");
  openDialogForEdit(ctxTargetId);
});

document.getElementById("ctxDelete").addEventListener("click", async () => {
  if (ctxTargetId === null) return;
  contextMenu.classList.remove("open");
  try {
    await postForm("/expensePlanner/remove", { entry_id: ctxTargetId });
    entries = entries.filter((e) => e.id !== ctxTargetId);
    renderEntriesOnly();
    await loadSummary();
  } catch (err) {
    console.error(err);
    alert("Fehler beim Entfernen: " + err.message);
  }
});

// ── KALENDER DATEPICKER ──────────────────────────────────────────────
const calPopup      = document.getElementById("calPopup");
const calDays       = document.getElementById("calDays");
const calMonthLabel = document.getElementById("calMonthLabel");

function updateDateDisplay() {
  document.getElementById("dateDisplay").textContent =
    `${pad(selectedDay)}.${pad(selectedMonth)}.${selectedYear}`;
}

function renderCalendar() {
  calMonthLabel.textContent = `${MONTHS_DE[calMonth]} ${calYear}`;
  calDays.innerHTML = "";

  const firstDay    = new Date(calYear, calMonth, 1).getDay();
  const startOffset = (firstDay + 6) % 7;
  const daysInMonth = new Date(calYear, calMonth + 1, 0).getDate();

  for (let i = 0; i < startOffset; i++) {
    const blank = document.createElement("div");
    blank.className = "cal-day empty";
    calDays.appendChild(blank);
  }

  for (let d = 1; d <= daysInMonth; d++) {
    const cell = document.createElement("div");
    cell.className = "cal-day";
    cell.textContent = d;
    if (d === selectedDay && calMonth + 1 === selectedMonth && calYear === selectedYear)
      cell.classList.add("selected");
    if (d === today.getDate() && calMonth === today.getMonth() && calYear === today.getFullYear())
      cell.classList.add("today");
    cell.addEventListener("click", (e) => {
      e.stopPropagation();
      selectedDay   = d;
      selectedMonth = calMonth + 1;
      selectedYear  = calYear;
      updateDateDisplay();
      calPopup.style.display = "none";
    });
    calDays.appendChild(cell);
  }
}

document.getElementById("dateCalBtn").addEventListener("click", (e) => {
  e.stopPropagation();
  const rect = document.getElementById("dateCalBtn").getBoundingClientRect();
  calPopup.style.top     = rect.bottom + 6 + "px";
  calPopup.style.left    = rect.left + "px";
  calPopup.style.display = calPopup.style.display === "block" ? "none" : "block";
  calMonth = selectedMonth - 1;
  calYear  = selectedYear;
  renderCalendar();
});

document.getElementById("calPrevMonth").addEventListener("click", (e) => {
  e.stopPropagation();
  calMonth--;
  if (calMonth < 0) { calMonth = 11; calYear--; }
  renderCalendar();
});
document.getElementById("calNextMonth").addEventListener("click", (e) => {
  e.stopPropagation();
  calMonth++;
  if (calMonth > 11) { calMonth = 0; calYear++; }
  renderCalendar();
});

// ── DIALOG ───────────────────────────────────────────────────────────
const dialogOverlay = document.getElementById("dialogOverlay");
const dateField     = document.getElementById("dateField");

function openDialogForNew() {
  if (!budgetIsSet) return;
  editingEntry = null;
  document.getElementById("dialogTitle").textContent = "Neuer Eintrag";
  document.getElementById("inputDesc").value          = "";
  document.getElementById("inputAmount").value        = "";
  document.getElementById("inputType").value          = "expense";
  dateField.style.display = "none";
  dialogOverlay.classList.add("open");
}

function openDialogForEdit(entryId) {
  editingEntry = entries.find((e) => e.id == entryId);
  if (!editingEntry) return;

  document.getElementById("dialogTitle").textContent = "Eintrag bearbeiten";
  document.getElementById("inputDesc").value          = editingEntry.desc;
  document.getElementById("inputAmount").value        = Math.abs(editingEntry.amount);
  document.getElementById("inputType").value          = editingEntry.amount < 0 ? "expense" : "income";

  selectedDay   = editingEntry.day;
  selectedMonth = editingEntry.month;
  selectedYear  = editingEntry.year;
  updateDateDisplay();

  dateField.style.display = "block";
  dialogOverlay.classList.add("open");
}

document.getElementById("fabBtn").addEventListener("click", () => openDialogForNew());

document.getElementById("dialogCancel").addEventListener("click", () => {
  dialogOverlay.classList.remove("open");
  calPopup.style.display = "none";
});

dialogOverlay.addEventListener("click", (e) => {
  if (e.target === dialogOverlay) {
    dialogOverlay.classList.remove("open");
    calPopup.style.display = "none";
  }
});

document.getElementById("dialogSave").addEventListener("click", async () => {
  const desc      = document.getElementById("inputDesc").value.trim();
  const amountRaw = parseFloat(document.getElementById("inputAmount").value);
  const type      = document.getElementById("inputType").value;

  if (!desc || isNaN(amountRaw) || amountRaw <= 0) {
    alert("Bitte Beschreibung und gültigen Betrag eingeben.");
    return;
  }

  const finalAmount = type === "expense" ? Math.abs(amountRaw) : -Math.abs(amountRaw);

  try {
    if (editingEntry) {
      await postForm("/expensePlanner/update", {
        entry_id:    editingEntry.id,
        amount:      finalAmount,
        description: desc,
        day:         selectedDay,
        month:       selectedMonth,
        year:        selectedYear,
      });
    } else {
      await postForm("/expensePlanner/add", {
        amount:      finalAmount,
        description: desc,
        day:         today.getDate(),
        month:       currentMonth + 1,
        year:        currentYear,
      });
    }
    dialogOverlay.classList.remove("open");
    calPopup.style.display = "none";
    editingEntry = null;
    await refreshAllData();
  } catch (err) {
    console.error(err);
    alert("Fehler: " + err.message);
  }
});

// ── GLOBALES SCHLIEßEN ───────────────────────────────────────────────
document.addEventListener("click", () => {
  contextMenu.classList.remove("open");
  monthPopover.classList.remove("open");
  calPopup.style.display = "none";
});

// ── INIT ─────────────────────────────────────────────────────────────
updatePickerLabel();
refreshAllData().catch((e) => console.error(e));
