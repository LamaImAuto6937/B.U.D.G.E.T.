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
const today = new Date();
let currentYear = today.getFullYear();
let currentMonth = today.getMonth(); // 0-basiert
let entries = [];
let ctxTargetId = null;
let editingEntry = null;
let budgetIsSet = false;
let suggestedBudget = 0;
let deleteTargetId = null;
let focusedTileElement = null;
let recentlyUpdatedEntryId = null;

// Kalender-State
let calYear = today.getFullYear();
let calMonth = today.getMonth();
let selectedDay = today.getDate();
let selectedMonth = today.getMonth() + 1;
let selectedYear = today.getFullYear();

// NEU: Kategorien & Tags
let categories = [];          // zentral verwaltete Hauptkategorien { id, name, color }
let selectedMainCat = null;   // aktuell gewählte Kategorie-ID im Dialog
let selectedSubTags = [];     // aktuell gewählte Freitext-Tags im Dialog (max 2)
let tagSuggestTimer = null;   // Debounce-Handle für Tag-Vorschläge
let highlightedSuggestIndex = -1;
let tagLimitWarningTimer = null;
function normalizeTag(tag) {
  return Array.isArray(tag) ? tag[0] : tag;
}

// ── FORMAT-HELPER ──────────────────────────────────────────────────────
const pad = (n) => String(n).padStart(2, "0");
const fmtNum = (v) => Math.abs(v).toLocaleString("de-DE", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " €";
const fmtSigned = (v) => (v < 0 ? "–" : "+") + fmtNum(v);
const fmtDate = (d) => d.toLocaleDateString("de-DE", { day: "2-digit", month: "short", year: "numeric" });

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
  Object.entries(data).forEach(([k, v]) => {
    if (Array.isArray(v)) {
      v.forEach((item) => fd.append(k + "[]", item));
    } else if (v !== null && v !== undefined) {
      fd.append(k, v);
    }
  });
  const res = await fetch(url, {
    method: "POST",
    credentials: "same-origin",
    headers: { "X-Requested-With": "XMLHttpRequest" },
    body: fd,
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.text();
}

// ── KATEGORIEN LADEN ───────────────────────────────────────────────────
async function loadCategories() {
  try {
    const data = await fetchJSON("/settings/categories");
    categories = (data.categories || []).map((c) => ({ id: c.id, name: c.name, color: c.color }));
  } catch (err) {
    console.error("Kategorien Fehler:", err);
    categories = [];
  }
}

function catById(id) {
  return categories.find((c) => String(c.id) === String(id)) || null;
}

// ── TAG-AUTOVERVOLLSTÄNDIGUNG (Backend-Anbindung) ─────────────────────
async function fetchTagSuggestions(query) {
  if (!query.trim()) return [];
  try {
    const data = await fetchJSON(`/expensePlanner/tags/suggest?q=${encodeURIComponent(query.trim())}`);
    return data.suggestions || [];
  } catch (err) {
    console.error("Tag-Vorschläge Fehler:", err);
    return [];
  }
}

// ── DATEN LADEN ────────────────────────────────────────────────────────
async function loadSummary() {
  const data = await fetchJSON(
    `/expensePlanner/summary?month=${currentMonth + 1}&year=${currentYear}`
  );
  if (data.error) {
    console.error("Summary Fehler:", data.error);
    return;
  }
  budgetIsSet = !data.needsBudget;
  suggestedBudget = data.globalBudget || data.budget || 0;
  const budget = data.budget || 0;
  const expenseSum = data.expenseSum || 0;
  const saved = data.saved || 0;
  const pct = data.expensePercentage || 0;
  const spent = Math.abs(expenseSum);
  const available = budget - spent;
  const pctCapped = budget > 0 ? Math.min(pct, 100) : 0;

  document.getElementById("budgetAmount").textContent = fmtNum(budget);
  document.getElementById("statExpenses").textContent = "–" + fmtNum(spent);
  const balEl = document.getElementById("statBalance");
  balEl.textContent = (saved >= 0 ? "+" : "–") + fmtNum(saved);
  balEl.className = "stat-value " + (saved >= 0 ? "positive" : "negative");
  const avEl = document.getElementById("statAvailable");
  avEl.textContent = fmtNum(available);
  avEl.className = "stat-value " + (available < 0 ? "negative" : "positive");
  document.getElementById("progressLabel").textContent = `${pctCapped.toFixed(0)} % ausgegeben`;
  document.getElementById("progressRemaining").textContent = available >= 0
    ? `${fmtNum(available)} verfügbar`
    : `${fmtNum(Math.abs(available))} überzogen`;
  const fill = document.getElementById("progressFill");
  fill.style.width = `${pctCapped}%`;
  fill.className = "progress-fill" + (pctCapped >= 100 ? " over" : pctCapped >= 75 ? " warn" : "");
  updateFabState();
  if (data.needsBudget) showBudgetPopup();
}

function mapEntry(r) {
  return {
    id: r.id,
    desc: r.description,
    amount: -r.amount,
    date: new Date(r.year, r.month - 1, r.day),
    day: r.day,
    month: r.month,
    year: r.year,
    mainCat: r.category ? r.category.id : null,
    mainCatColor: r.category ? r.category.color : null,
    mainCatName: r.category ? r.category.name : null,
    tags: (r.tags || []).map(normalizeTag),
  };
}

// FILTER: Gefiltert wird im Backend; jede neue Anfrage verwirft ältere, noch laufende Antworten.
let entriesRequestSeq = 0;
async function loadEntries() {
  const seq = ++entriesRequestSeq;

  const data = await fetchJSON(`/expensePlanner/entries/search?${ExpenseFilter.toQueryString()}`);

  if (seq !== entriesRequestSeq) return;
  if (data.error) {
    console.error("Einträge Fehler:", data.error);
    entries = [];
  } else {
    entries = (data.entries || []).map(mapEntry);
    ExpenseFilter.applyFacets(data.facets || {});
  }
  renderEntriesOnly();
}

async function refreshAllData() {
  // FILTER: Jahresübersicht mitladen und Sidebar nach dem Laden der Kategorien neu zeichnen
  await Promise.all([loadCategories(), loadSummary(), loadEntries(), ExpenseFilter.loadOverview()]);
  ExpenseFilter.render();
}

// ── FAB ZUSTAND ─────────────────────────────────────────────────────────
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

// ── BUDGET POPUP ──────────────────────────────────────────────────────
const budgetOverlay = document.getElementById("budgetOverlay");
function showBudgetPopup() {
  document.getElementById("budgetSuggestionAmount").textContent = fmtNum(suggestedBudget);
  budgetOverlay.classList.add("open");
}
document.getElementById("budgetConfirm").addEventListener("click", async () => {
  budgetOverlay.classList.remove("open");
  try {
    await postForm("/expensePlanner/setBudget", {
      amount: suggestedBudget,
      month: currentMonth + 1,
      year: currentYear,
    });
    budgetIsSet = true;
    updateFabState();
    await refreshAllData();
  } catch (err) {
    console.error(err);
    showToast("Fehler beim Speichern des Budgets: " + err.message, "error");
  }
});
document.getElementById("budgetDeny").addEventListener("click", () => {
  budgetOverlay.classList.remove("open");
});

// ── MONATSPICKER ──────────────────────────────────────────────────────
const monthPickerBtn = document.getElementById("monthPickerBtn");
const monthPickerLabel = document.getElementById("monthPickerLabel");
const monthPopover = document.getElementById("monthPopover");

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
    if (i === today.getMonth() && currentYear === today.getFullYear()) cell.classList.add("today-month");
    cell.textContent = m;
    cell.addEventListener("click", async () => {
      currentMonth = i;
      updatePickerLabel();
      renderMonthsGrid();
      monthPopover.classList.remove("open");
      // FILTER: Monatspicker setzt den Zeitraum-Filter auf diesen Monat
      ExpenseFilter.setPeriodToMonth(currentYear, currentMonth + 1);
      await refreshAllData();
    });
    grid.appendChild(cell);
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

// ── TAG-DARSTELLUNG AUF DER KACHEL ───────────────────────────────────
function buildTagElements(entry) {
  const frag = document.createDocumentFragment();

  if (entry.mainCat) {
    const mainTag = document.createElement("span");
    mainTag.className = "cat-tag";
    mainTag.style.background = entry.mainCatColor || "#7f8c8d";
    mainTag.textContent = entry.mainCatName || "Kategorie";
    frag.appendChild(mainTag);
  } else {
    const noneTag = document.createElement("span");
    noneTag.className = "cat-tag none";
    noneTag.textContent = "Keine Kategorie";
    frag.appendChild(noneTag);
  }

  if (entry.tags && entry.tags.length > 0) {
    const badge = document.createElement("span");
    badge.className = "extra-tags-badge";
    badge.textContent = "+" + entry.tags.length;

    const popover = document.createElement("div");
    popover.className = "extra-tags-popover";
    entry.tags.forEach((t) => {
      const mini = document.createElement("div");
      mini.className = "mini-tag";
      const dot = document.createElement("span");
      dot.className = "mini-dot";
      mini.appendChild(dot);
      mini.appendChild(document.createTextNode(t));
      popover.appendChild(mini);
    });
    badge.appendChild(popover);

    badge.addEventListener("click", (e) => {
      e.stopPropagation();
      const isOpen = popover.classList.contains("open");
      document.querySelectorAll(".extra-tags-popover.open").forEach((p) => p.classList.remove("open"));
      if (!isOpen) popover.classList.add("open");
    });

    frag.appendChild(badge);
  }
  return frag;
}

// ── EINTRÄGE RENDERN ─────────────────────────────────────────────────
function renderEntriesOnly() {
  // FILTER: Überschrift = gewählter Zeitraum
  document.getElementById("entriesLabel").textContent = ExpenseFilter.periodLabel();
  const list = document.getElementById("entriesList");
  list.innerHTML = "";

  if (!entries || entries.length === 0) {
    // FILTER: eigener Leer-Hinweis, wenn Filter aktiv sind
    if (ExpenseFilter.hasActiveFilters()) {
      list.innerHTML = `<div class="empty-state"><div class="icon"></div><p>Keine Einträge passen zu deinen Filtern.</p>` +
        `<button type="button" class="ef-link ef-empty-reset">Filter zurücksetzen</button></div>`;
      list.querySelector(".ef-empty-reset").addEventListener("click", () => ExpenseFilter.reset());
    } else {
      list.innerHTML = `<div class="empty-state"><div class="icon"></div><p>Keine Einträge für diesen Monat.</p></div>`;
    }
    return;
  }

  // FILTER: Reihenfolge kommt sortiert vom Backend; Monatstrenner bei mehreren Monaten
  const groupByMonth = ExpenseFilter.shouldGroupByMonth(entries);
  const monthCounts = new Map();
  entries.forEach((e) => monthCounts.set(`${e.year}-${e.month}`, (monthCounts.get(`${e.year}-${e.month}`) || 0) + 1));
  let lastMonthKey = null;

  entries.forEach((entry) => {
    const monthKey = `${entry.year}-${entry.month}`;
    if (groupByMonth && monthKey !== lastMonthKey) {
      list.appendChild(ExpenseFilter.buildMonthSeparator(entry.year, entry.month, monthCounts.get(monthKey)));
      lastMonthKey = monthKey;
    }

    const tile = document.createElement("div");
    tile.className = "entry-tile";
    tile.style.borderLeftColor = entry.mainCat && entry.mainCatColor ? entry.mainCatColor : "var(--border-strong)";

    const info = document.createElement("div");
    info.className = "entry-info";

    const topRow = document.createElement("div");
    topRow.className = "entry-top-row";
    const descSpan = document.createElement("span");
    descSpan.className = "entry-description";
    ExpenseFilter.highlightInto(descSpan, entry.desc); // FILTER: Suchtreffer markieren
    topRow.appendChild(descSpan);
    topRow.appendChild(buildTagElements(entry));

    const dateDiv = document.createElement("div");
    dateDiv.className = "entry-date";
    dateDiv.textContent = fmtDate(entry.date);

    info.appendChild(topRow);
    info.appendChild(dateDiv);

    const amountDiv = document.createElement("div");
    amountDiv.className = "entry-amount " + (entry.amount < 0 ? "negative" : "positive");
    amountDiv.textContent = fmtSigned(entry.amount);

    const menuBtn = document.createElement("button");
    menuBtn.className = "tile-menu-btn";
    menuBtn.dataset.id = entry.id;
    menuBtn.title = "Optionen";
    menuBtn.textContent = "⋮";
    menuBtn.addEventListener("click", (e) => openContextMenu(e, entry.id));

    tile.appendChild(info);
    tile.appendChild(amountDiv);
    tile.appendChild(menuBtn);
    list.appendChild(tile);
  });

  updateFabState();
}

// ── KONTEXTMENÜ ───────────────────────────────────────────────────────
const contextMenu = document.getElementById("contextMenu");
function openContextMenu(e, entryId) {
  if (!budgetIsSet) return;
  e.stopPropagation();
  ctxTargetId = entryId;
  const rect = e.currentTarget.getBoundingClientRect();
  let top = rect.bottom + 4;
  let left = rect.right - 160;
  if (left < 8) left = 8;
  if (top + 110 > window.innerHeight) top = rect.top - 110;
  contextMenu.style.top = top + "px";
  contextMenu.style.left = left + "px";
  contextMenu.classList.add("open");

  document.getElementById("focusOverlay").classList.add("active");
  focusedTileElement = e.currentTarget.closest(".entry-tile");
  if (focusedTileElement) focusedTileElement.classList.add("focused");
}

document.getElementById("ctxEdit").addEventListener("click", () => {
  contextMenu.classList.remove("open");
  document.getElementById("focusOverlay").classList.remove("active");
  if (focusedTileElement) focusedTileElement.classList.remove("focused");
  openDialogForEdit(ctxTargetId);
});

document.getElementById("ctxDelete").addEventListener("click", async () => {
  if (ctxTargetId == null) return;
  contextMenu.classList.remove("open");
  document.getElementById("focusOverlay").classList.remove("active");
  if (focusedTileElement) focusedTileElement.classList.remove("focused");
  const entryToDelete = entries.find((e) => e.id === ctxTargetId);
  if (!entryToDelete) return;
  deleteTargetId = ctxTargetId;
  document.getElementById("deleteConfirmText").textContent =
    `Möchtest du wirklich diesen Eintrag "${entryToDelete.desc}" löschen?`;
  document.getElementById("deleteConfirmOverlay").classList.add("open");
});

// ── DELETE CONFIRMATION ───────────────────────────────────────────────
document.getElementById("deleteConfirmCancel").addEventListener("click", () => {
  document.getElementById("deleteConfirmOverlay").classList.remove("open");
  deleteTargetId = null;
});
document.getElementById("deleteConfirmOk").addEventListener("click", async () => {
  if (deleteTargetId == null) return;
  document.getElementById("deleteConfirmOverlay").classList.remove("open");
  try {
    const tileElement = document.querySelector(`[data-id="${deleteTargetId}"]`)?.closest(".entry-tile");
    if (tileElement) {
      tileElement.classList.add("deleting");
      await new Promise((resolve) => tileElement.addEventListener("animationend", resolve, { once: true }));
    }
    await postForm("/expensePlanner/remove", { entryid: deleteTargetId });
    entries = entries.filter((e) => e.id !== deleteTargetId);
    renderEntriesOnly();
    await refreshAllData(); // FILTER: auch Jahresübersicht und Sidebar-Summen aktualisieren
  } catch (err) {
    console.error(err);
    showToast("Fehler beim Entfernen: " + err.message, "error");
  }
  deleteTargetId = null;
});

// ── KALENDER / DATEPICKER (unverändert) ──────────────────────────────
const calPopup = document.getElementById("calPopup");
const calDays = document.getElementById("calDays");
const calMonthLabel = document.getElementById("calMonthLabel");

function updateDateDisplay() {
  document.getElementById("dateDisplay").textContent = `${pad(selectedDay)}.${pad(selectedMonth)}.${selectedYear}`;
}
function renderCalendar() {
  calMonthLabel.textContent = `${MONTHS_DE[calMonth]} ${calYear}`;
  calDays.innerHTML = "";
  const firstDay = new Date(calYear, calMonth, 1).getDay();
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
    if (d === selectedDay && calMonth + 1 === selectedMonth && calYear === selectedYear) cell.classList.add("selected");
    if (d === today.getDate() && calMonth === today.getMonth() && calYear === today.getFullYear()) cell.classList.add("today");
    cell.addEventListener("click", (e) => {
      e.stopPropagation();
      selectedDay = d;
      selectedMonth = calMonth + 1;
      selectedYear = calYear;
      updateDateDisplay();
      calPopup.style.display = "none";
      renderCalendar();
    });
    calDays.appendChild(cell);
  }
}
document.getElementById("dateCalBtn").addEventListener("click", (e) => {
  e.stopPropagation();
  const rect = document.getElementById("dateCalBtn").getBoundingClientRect();
  calPopup.style.top = rect.bottom + 6 + "px";
  calPopup.style.left = rect.left + "px";
  calPopup.style.display = calPopup.style.display === "none" ? "block" : "none";
  calMonth = selectedMonth - 1;
  calYear = selectedYear;
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

// ── DIALOG: HAUPTKATEGORIE-AUSWAHL ───────────────────────────────────
function renderMainCatPicker() {
  const wrap = document.getElementById("mainCatPicker");
  wrap.innerHTML = "";

  const noneChip = document.createElement("div");
  noneChip.className = "pick-chip none-chip" + (selectedMainCat === null ? " selected" : "");
  noneChip.textContent = "Keine Kategorie";
  noneChip.addEventListener("click", () => { selectedMainCat = null; renderMainCatPicker(); });
  wrap.appendChild(noneChip);

  categories.forEach((cat) => {
    const chip = document.createElement("div");
    chip.className = "pick-chip" + (String(selectedMainCat) === String(cat.id) ? " selected" : "");
    chip.style.background = cat.color;
    chip.textContent = cat.name;
    chip.addEventListener("click", () => { selectedMainCat = cat.id; renderMainCatPicker(); });
    wrap.appendChild(chip);
  });
}

// ── DIALOG: FREITEXT TAGS mit AUTOVERVOLLSTÄNDIGUNG ──────────────────
const tagInput = document.getElementById("tagInput");
const tagSuggestionsEl = document.getElementById("tagSuggestions");

function renderSelectedTags() {
  const row = document.getElementById("selectedTagsRow");
  row.innerHTML = "";
  selectedSubTags.forEach((tag, idx) => {
    const chip = document.createElement("span");
    chip.className = "selected-tag-chip";
    const textNode = document.createElement("span");
    textNode.textContent = tag;
    chip.appendChild(textNode);

    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "remove-tag-btn";
    removeBtn.textContent = "✕";
    removeBtn.addEventListener("click", () => {
      selectedSubTags.splice(idx, 1);
      renderSelectedTags();
      updateTagInputState();
    });
    chip.appendChild(removeBtn);
    row.appendChild(chip);
  });
}

function updateTagInputState() {
  const limitReached = selectedSubTags.length >= 2;
  tagInput.disabled = false;
  tagInput.placeholder = limitReached ? "Tag suchen..." : "Tag eingeben und Enter drücken...";
  const limitMsg = document.getElementById("tagLimitMsg");
  if (!limitMsg.classList.contains("visible")) {
    limitMsg.textContent = limitReached ? "Maximal 2 zusätzliche Tags erreicht." : "";
  }
}

function showTagLimitWarning() {
  const limitMsg = document.getElementById("tagLimitMsg");
  clearTimeout(tagLimitWarningTimer);
  limitMsg.textContent = "Bitte zuerst einen vorhandenen Tag entfernen.";
  limitMsg.classList.remove("visible");
  tagInput.classList.remove("limit-warning");
  void tagInput.offsetWidth;
  limitMsg.classList.add("visible");
  tagInput.classList.add("limit-warning");
  tagLimitWarningTimer = setTimeout(() => {
    limitMsg.classList.remove("visible");
    tagInput.classList.remove("limit-warning");
    updateTagInputState();
  }, 4000);
}

function hideSuggestions() {
  tagSuggestionsEl.classList.remove("open");
  tagSuggestionsEl.innerHTML = "";
  highlightedSuggestIndex = -1;
}

function addTag(rawTag) {
  const tag = rawTag.trim();
  if (!tag) return;
  if (selectedSubTags.length >= 2) {
    showTagLimitWarning();
    return;
  }
  const alreadySelected = selectedSubTags.some((t) => t.toLowerCase() === tag.toLowerCase());
  if (alreadySelected) { tagInput.value = ""; hideSuggestions(); return; }

  selectedSubTags.push(tag);
  tagInput.value = "";
  renderSelectedTags();
  updateTagInputState();
  hideSuggestions();
  tagInput.focus();
}

async function renderSuggestions(query) {
  const q = query.trim();
  if (!q) { hideSuggestions(); return; }

  const rawMatches = await fetchTagSuggestions(q);
  const matches = rawMatches.filter(
    (t) => !selectedSubTags.some((sel) => sel.toLowerCase() === t.toLowerCase())
  );

  // Race-Condition-Schutz: nur rendern, wenn Eingabefeld noch denselben Wert hat
  if (tagInput.value.trim() !== q) return;

  tagSuggestionsEl.innerHTML = "";
  highlightedSuggestIndex = -1;

  matches.forEach((match) => {
    const item = document.createElement("div");
    item.className = "tag-suggestion-item";
    const icon = document.createElement("span");
    icon.className = "tag-suggest-icon";
    icon.textContent = "#";
    item.appendChild(icon);
    item.appendChild(document.createTextNode(match));
    item.addEventListener("click", () => addTag(match));
    tagSuggestionsEl.appendChild(item);
  });

  const exactMatch = matches.some((m) => m.toLowerCase() === q.toLowerCase());
  if (!exactMatch) {
    const createHint = document.createElement("div");
    createHint.className = "tag-create-hint";
    createHint.textContent = `Enter drücken, um "${q}" als neuen Tag zu erstellen`;
    tagSuggestionsEl.appendChild(createHint);
  }

  tagSuggestionsEl.classList.add("open");
}

tagInput.addEventListener("input", () => {
  clearTimeout(tagSuggestTimer);
  const value = tagInput.value;
  tagSuggestTimer = setTimeout(() => renderSuggestions(value), 200); // Debounce
});

tagInput.addEventListener("keydown", (e) => {
  const items = tagSuggestionsEl.querySelectorAll(".tag-suggestion-item");
  if (e.key === "ArrowDown") {
    e.preventDefault();
    if (items.length === 0) return;
    highlightedSuggestIndex = (highlightedSuggestIndex + 1) % items.length;
    items.forEach((it, i) => it.classList.toggle("highlighted", i === highlightedSuggestIndex));
  } else if (e.key === "ArrowUp") {
    e.preventDefault();
    if (items.length === 0) return;
    highlightedSuggestIndex = (highlightedSuggestIndex - 1 + items.length) % items.length;
    items.forEach((it, i) => it.classList.toggle("highlighted", i === highlightedSuggestIndex));
  } else if (e.key === "Enter") {
    e.preventDefault();
    if (highlightedSuggestIndex >= 0 && items[highlightedSuggestIndex]) {
      addTag(items[highlightedSuggestIndex].textContent.replace(/^#/, ""));
    } else if (tagInput.value.trim()) {
      addTag(tagInput.value);
    }
  } else if (e.key === "Escape") {
    hideSuggestions();
  }
});
tagInput.addEventListener("click", (e) => e.stopPropagation());
tagSuggestionsEl.addEventListener("click", (e) => e.stopPropagation());

// ── DIALOG: NEU / BEARBEITEN ──────────────────────────────────────────
const dialogOverlay = document.getElementById("dialogOverlay");
const dateField = document.getElementById("dateField");

function openDialogForNew() {
  if (!budgetIsSet) return;
  editingEntry = null;
  selectedMainCat = null;
  selectedSubTags = [];
  document.getElementById("dialogTitle").textContent = "Neuer Eintrag";
  document.getElementById("inputDesc").value = "";
  document.getElementById("inputAmount").value = "";
  document.getElementById("inputType").value = "expense";
  dateField.style.display = "none";
  renderMainCatPicker();
  renderSelectedTags();
  updateTagInputState();
  hideSuggestions();
  dialogOverlay.classList.add("open");
}

function openDialogForEdit(entryId) {
  editingEntry = entries.find((e) => e.id === entryId);
  if (!editingEntry) return;
  selectedMainCat = editingEntry.mainCat;
  selectedSubTags = (editingEntry.tags || []).map(normalizeTag);
  document.getElementById("dialogTitle").textContent = "Eintrag bearbeiten";
  document.getElementById("inputDesc").value = editingEntry.desc;
  document.getElementById("inputAmount").value = Math.abs(editingEntry.amount);
  document.getElementById("inputType").value = editingEntry.amount < 0 ? "expense" : "income";
  selectedDay = editingEntry.day;
  selectedMonth = editingEntry.month;
  selectedYear = editingEntry.year;
  updateDateDisplay();
  dateField.style.display = "block";
  renderMainCatPicker();
  renderSelectedTags();
  updateTagInputState();
  hideSuggestions();
  dialogOverlay.classList.add("open");
}

document.getElementById("fabBtn").addEventListener("click", openDialogForNew);
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
  const desc = document.getElementById("inputDesc").value.trim();
  const amountRaw = parseFloat(document.getElementById("inputAmount").value);
  const type = document.getElementById("inputType").value;

  if (!desc || isNaN(amountRaw) || amountRaw <= 0) {
    showToast("Bitte Beschreibung und gültigen Betrag eingeben.", "error");
    return;
  }
  const finalAmount = type === "expense" ? Math.abs(amountRaw) : -Math.abs(amountRaw);

  const payload = {
    amount: finalAmount,
    description: desc,
    category_id: selectedMainCat || "",
    tags: selectedSubTags,
  };

  try {
    if (editingEntry) {
      recentlyUpdatedEntryId = editingEntry.id;
      await postForm("/expensePlanner/update", {
        entryid: editingEntry.id,
        ...payload,
        day: selectedDay,
        month: selectedMonth,
        year: selectedYear,
      });
    } else {
      await postForm("/expensePlanner/add", {
        ...payload,
        day: today.getDate(),
        month: currentMonth + 1,
        year: currentYear,
      });
    }
    dialogOverlay.classList.remove("open");
    calPopup.style.display = "none";
    editingEntry = null;
    await refreshAllData();

    if (recentlyUpdatedEntryId) {
      const tileElement = document.querySelector(`[data-id="${recentlyUpdatedEntryId}"]`)?.closest(".entry-tile");
      if (tileElement) tileElement.classList.add("updating");
      recentlyUpdatedEntryId = null;
    }
  } catch (err) {
    console.error(err);
    showToast("Fehler: " + err.message, "error");
  }
});

// ── GLOBALES SCHLIESSEN ────────────────────────────────────────────────
document.addEventListener("click", () => {
  contextMenu.classList.remove("open");
  document.getElementById("focusOverlay").classList.remove("active");
  if (focusedTileElement) focusedTileElement.classList.remove("focused");
  monthPopover.classList.remove("open");
  calPopup.style.display = "none";
  document.querySelectorAll(".extra-tags-popover.open").forEach((p) => p.classList.remove("open"));
  hideSuggestions();
});

// ════════════════════════════════════════════════════════════════════
// ── FILTER-SIDEBAR (Anfang) ──────────────────────────────────────────
// Suche, Typ, Kategorien, Tags, Betrag, Zeitraum (Jahresübersicht) und
// Sortierung. Verwaltet den Filterzustand, baut die Query für
// /expensePlanner/entries/search und rendert die Sidebar.
// Gefiltert wird im Backend (siehe anforderungen.md).
// Nutzt MONTHS_DE, MONTHS_SHORT, pad, fmtNum und fetchJSON von oben.
// ════════════════════════════════════════════════════════════════════
const ExpenseFilter = (function () {
  const WEEKDAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"];
  const AMOUNT_MAX = 200;
  const BUCKETS = 20;
  const DEBOUNCE_MS = 300;
  const NO_CAT = { id: "none", name: "Ohne Kategorie", color: "#95a5a6" };

  const $ = (id) => document.getElementById(id);
  const mkey = (y, m) => y * 12 + (m - 1);
  const keyY = (k) => Math.floor(k / 12);
  const keyM = (k) => (k % 12) + 1;
  const daysIn = (y, m) => new Date(y, m, 0).getDate();
  const esc = (v) => String(v).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const safeColor = (c) => (/^#[0-9a-f]{3,8}$/i.test(c || "") ? c : NO_CAT.color);
  const blankDays = () => ({ from: 1, to: 31, pick: null });

  let opts = { getCategories: () => [], onChange: () => {}, onSingleMonth: () => {} };
  let defaultKey = null;        // Monat der Budget-Karte (= Standard-Zeitraum)
  let overview = new Map();     // key -> { expenseSum, entryCount, days:Set }
  let years = [];
  let facets = { categories: new Map(), tags: [], histogram: new Array(BUCKETS).fill(0) };
  let s = null;
  let strictTagOptions = new Set();
  let searchTimer = null;
  let drag = null;

  const blankState = () => ({
    q: "", type: "all", cats: new Set(), tags: new Set(), tagMode: "any", noTags: false,
    appliedTags: new Set(), appliedTagMode: "any",
    amin: 0, amax: AMOUNT_MAX, period: new Set(defaultKey === null ? [] : [defaultKey]), days: blankDays(), sort: "date-desc",
  });

  // ── ZEITRAUM-HELFER ────────────────────────────────────────────────
  const singleKey = () => (s.period.size === 1 ? [...s.period][0] : null);
  function daysActive() {
    const k = singleKey();
    return k !== null && !(s.days.from === 1 && s.days.to >= daysIn(keyY(k), keyM(k)));
  }
  const periodIsDefault = () => singleKey() === defaultKey && !daysActive();

  function compressKeys(keys) {
    const runs = [];
    [...keys].sort((a, b) => a - b).forEach((k) => {
      const r = runs[runs.length - 1];
      if (r && r[1] === k - 1) r[1] = k; else runs.push([k, k]);
    });
    const lbl = (k) => `${MONTHS_SHORT[keyM(k) - 1]} ${keyY(k)}`;
    return runs.map(([a, b]) => {
      if (a === b) return lbl(a);
      if (keyY(a) === keyY(b) && keyM(a) === 1 && keyM(b) === 12) return `${keyY(a)} (ganzes Jahr)`;
      if (keyY(a) === keyY(b)) return `${MONTHS_SHORT[keyM(a) - 1]}–${MONTHS_SHORT[keyM(b) - 1]} ${keyY(a)}`;
      return `${lbl(a)} – ${lbl(b)}`;
    }).join(", ");
  }

  function periodLabel() {
    if (!s.period.size) return "Gesamte Historie";
    const k = singleKey();
    if (k === null) return compressKeys(s.period);
    let label = `${MONTHS_DE[keyM(k) - 1]} ${keyY(k)}`;
    if (daysActive()) {
      const to = Math.min(s.days.to, daysIn(keyY(k), keyM(k)));
      label += s.days.from === to ? `, ${to}.` : `, ${s.days.from}.–${to}.`;
    }
    return label;
  }

  function activeSections() {
    return {
      search: !!s.q, type: s.type !== "all", cats: s.cats.size > 0, tags: s.appliedTags.size > 0 || s.noTags,
      amount: s.amin > 0 || s.amax < AMOUNT_MAX, period: !periodIsDefault(),
    };
  }
  const hasActiveFilters = () => Object.values(activeSections()).some(Boolean);

  // ── QUERY FÜR DAS BACKEND ──────────────────────────────────────────
  function toQueryString() {
    const p = new URLSearchParams();
    if (s.q) p.set("q", s.q);
    if (s.type !== "all") p.set("type", s.type);
    s.cats.forEach((c) => p.append("category", c));
    if (s.noTags) p.set("noTags", "1");
    else if (s.appliedTags.size) { s.appliedTags.forEach((t) => p.append("tag", t)); p.set("tagMode", s.appliedTagMode); }
    if (s.amin > 0) p.set("amountMin", s.amin);
    if (s.amax < AMOUNT_MAX) p.set("amountMax", s.amax);
    [...s.period].sort((a, b) => a - b).forEach((k) => p.append("period", `${keyY(k)}-${pad(keyM(k))}`));
    if (daysActive()) {
      const k = singleKey();
      p.set("dayFrom", s.days.from);
      p.set("dayTo", Math.min(s.days.to, daysIn(keyY(k), keyM(k))));
    }
    p.set("sort", s.sort);
    return p.toString();
  }

  // ── ÄNDERUNGEN ─────────────────────────────────────────────────────
  function changed(delay = 0) {
    renderPanel();
    clearTimeout(searchTimer);
    if (delay) searchTimer = setTimeout(() => opts.onChange(), delay);
    else opts.onChange();
  }

  function hasPendingTags() {
    return s.tags.size !== s.appliedTags.size ||
      [...s.tags].some((t) => !s.appliedTags.has(t)) ||
      (s.tags.size > 0 && s.tagMode !== s.appliedTagMode);
  }

  function applyTags() {
    s.appliedTags = new Set(s.tags);
    s.appliedTagMode = s.tagMode;
    changed();
  }

  function commitPeriod() {
    s.days = blankDays();
    const k = singleKey();
    if (k !== null) {
      defaultKey = k;
      opts.onSingleMonth(keyY(k), keyM(k));
    }
    changed();
  }

  function reset() {
    s = blankState();
    strictTagOptions.clear();
    $("efSearch").value = "";
    $("efSort").value = s.sort;
    changed();
  }

  // ── RENDERING: SIDEBAR ─────────────────────────────────────────────
  function setSeg(id, value) {
    $(id).querySelectorAll("button").forEach((b) => b.classList.toggle("ef-on", b.dataset.v === value));
  }

  function renderCategories() {
    const list = [...opts.getCategories(), NO_CAT];
    const sumOf = (c) => facets.categories.get(String(c.id)) || 0;
    const max = Math.max(1, ...list.map(sumOf));
    $("efCats").innerHTML = list.sort((a, b) => sumOf(b) - sumOf(a)).map((c) => {
      const id = String(c.id);
      const cls = s.cats.has(id) ? "ef-on" : s.cats.size ? "ef-dim" : "";
      return `<div class="ef-cat ${cls}" data-cat="${esc(id)}" style="--c:${safeColor(c.color)}">
        <span class="ef-cat-name">${esc(c.name)}</span><span class="ef-cat-sum">${fmtNum(sumOf(c))}</span>
        <div class="ef-cat-bar"><span style="width:${(sumOf(c) / max) * 100}%"></span></div></div>`;
    }).join("");
  }

  function renderTags() {
    const tags = [...facets.tags];
    // Strikte Treffer dürfen bereits angebotene Tags nicht aus der Auswahl entfernen.
    if (s.tagMode === "strict") {
      facets.tags.forEach((t) => strictTagOptions.add(t.name));
      strictTagOptions.forEach((t) => { if (!tags.some((x) => x.name === t)) tags.push({ name: t, count: 0 }); });
    }
    s.tags.forEach((t) => { if (!tags.some((x) => x.name === t)) tags.push({ name: t, count: 0 }); });
    $("efTags").innerHTML = tags.length
      ? tags.map((t) => `<button type="button" class="${s.tags.has(t.name) ? "ef-on" : ""}" data-tag="${esc(t.name)}"${s.noTags ? " disabled" : ""}>#${esc(t.name)}<small> ${t.count}</small></button>`).join("")
      : `<span class="ef-hint" style="margin:0">Keine Tags im gewählten Zeitraum.</span>`;
    $("efTags").classList.toggle("ef-disabled", s.noTags);
    $("efTagMode").classList.toggle("ef-disabled", s.noTags);
    $("efNoTags").checked = s.noTags;
    setSeg("efTagMode", s.tagMode);
    $("efTagMode").querySelectorAll("button").forEach((b) => { b.disabled = s.noTags; });
    const pending = hasPendingTags();
    $("efApplyTags").hidden = s.tagMode !== "strict";
    $("efApplyTags").disabled = s.noTags || !pending;
    $("efTagPending").hidden = s.tagMode !== "strict" || s.noTags || !pending;
    const sel = esc([...s.tags].map((t) => "#" + t).join(" + ") || "#a + #b");
    $("efModeExplain").innerHTML = s.tagMode === "strict"
      ? `<b>Strikt:</b> nur Einträge, deren Tags <i>genau</i> ${sel} sind – nicht mehr, nicht weniger.`
      : `<b>Beliebig:</b> Einträge, deren Tags eine Teilmenge von ${sel} sind (nur ausgewählte Tags, aber nicht unbedingt alle).`;
  }

  function renderAmount() {
    const max = Math.max(1, ...facets.histogram);
    const upper = s.amax >= AMOUNT_MAX ? Infinity : s.amax;
    $("efHisto").innerHTML = facets.histogram.map((n, i) => {
      const lo = i * (AMOUNT_MAX / BUCKETS);
      return `<div class="${lo >= s.amin && lo < upper ? "ef-in" : ""}" style="height:${(n / max) * 100}%"></div>`;
    }).join("");
    $("efAmin").value = s.amin;
    $("efAmax").value = s.amax;
    $("efFill").style.left = (s.amin / AMOUNT_MAX) * 100 + "%";
    $("efFill").style.right = 100 - (s.amax / AMOUNT_MAX) * 100 + "%";
    $("efAminLbl").textContent = fmtNum(s.amin);
    $("efAmaxLbl").textContent = s.amax >= AMOUNT_MAX ? `${AMOUNT_MAX} € +` : fmtNum(s.amax);
  }

  function buildHeat() {
    const heat = $("efHeat");
    if (!years.length) {
      heat.style.display = "none";
      $("efHeatEmpty").style.display = "block";
      return;
    }
    heat.style.display = "";
    $("efHeatEmpty").style.display = "none";
    const sums = [...overview.values()].map((o) => o.expenseSum);
    const vmin = Math.min(...sums), vmax = Math.max(...sums);
    const now = new Date();
    const todayKey = mkey(now.getFullYear(), now.getMonth() + 1);
    let h = "<div></div>" + MONTHS_SHORT.map((n, i) => `<div class="ef-mh" data-m="${i + 1}" title="${MONTHS_DE[i]} in allen Jahren">${n}</div>`).join("");
    years.forEach((y) => {
      h += `<div class="ef-yh" data-y="${y}" title="Ganzes Jahr ${y}">${y}</div>`;
      for (let m = 1; m <= 12; m++) {
        const k = mkey(y, m), o = overview.get(k);
        const a = o ? 0.22 + 0.78 * ((o.expenseSum - vmin) / (vmax - vmin || 1)) : 0;
        h += `<div class="ef-hc${o ? "" : " ef-nodata"}${k === todayKey ? " ef-today" : ""}" data-k="${k}" style="--a:${a.toFixed(2)}"></div>`;
      }
    });
    heat.innerHTML = h;
  }

  function renderHeatSelection() {
    $("efHeat").classList.toggle("ef-has-sel", s.period.size > 0);
    $("efHeat").querySelectorAll(".ef-hc").forEach((c) => c.classList.toggle("ef-on", s.period.has(+c.dataset.k)));
    $("efSelInfo").textContent = s.period.size ? `${s.period.size} Monat${s.period.size > 1 ? "e" : ""} gewählt` : "Gesamte Historie";
  }

  function renderDays() {
    const wrap = $("efDays");
    const k = singleKey();
    if (k === null) { wrap.innerHTML = ""; return; }
    const y = keyY(k), m = keyM(k), n = daysIn(y, m);
    const offset = (new Date(y, m - 1, 1).getDay() + 6) % 7;
    const has = overview.get(k)?.days || new Set();
    const now = new Date();
    const isCurrent = y === now.getFullYear() && m === now.getMonth() + 1;
    const active = daysActive();
    const to = Math.min(s.days.to, n);
    let h = `<div class="ef-cal-title">${MONTHS_DE[m - 1]} ${y}</div><div class="ef-cal">` +
      WEEKDAYS.map((d) => `<div class="ef-wd">${d}</div>`).join("") + "<div></div>".repeat(offset);
    for (let d = 1; d <= n; d++) {
      const cls = active && (d === s.days.from || d === to) ? " ef-edge" : active && d > s.days.from && d < to ? " ef-inr" : "";
      h += `<button type="button" class="ef-day${has.has(d) ? " ef-has" : ""}${cls}" data-d="${d}"${isCurrent && d > now.getDate() ? " disabled" : ""}>${d}</button>`;
    }
    wrap.innerHTML = h + "</div>";
  }

  function renderChips(act) {
    const chips = [];
    if (s.q) chips.push([`„${s.q}“`, () => { s.q = ""; $("efSearch").value = ""; }]);
    if (s.type !== "all") chips.push([s.type === "expense" ? "Ausgaben" : "Einnahmen", () => (s.type = "all")]);
    s.cats.forEach((id) => {
      const c = id === "none" ? NO_CAT : opts.getCategories().find((x) => String(x.id) === id);
      chips.push([c ? c.name : "Kategorie", () => s.cats.delete(id)]);
    });
    if (s.noTags) chips.push(["ohne Tags", () => (s.noTags = false)]);
    else s.appliedTags.forEach((t) => chips.push([`#${t}${s.appliedTagMode === "strict" ? " (strikt)" : ""}`, () => {
      s.appliedTags.delete(t);
      s.tags.delete(t);
    }]));
    if (act.amount) chips.push([`${s.amin} – ${s.amax >= AMOUNT_MAX ? "∞" : s.amax} €`, () => { s.amin = 0; s.amax = AMOUNT_MAX; }]);
    if (act.period) chips.push([periodLabel(), () => { s.period = new Set(defaultKey === null ? [] : [defaultKey]); s.days = blankDays(); }]);

    const box = $("efChips");
    box.innerHTML = "";
    chips.forEach(([label, remove]) => {
      const chip = document.createElement("span");
      chip.className = "ef-chip";
      chip.append(label + " ");
      const btn = document.createElement("button");
      btn.type = "button";
      btn.title = "Filter entfernen";
      btn.textContent = "✕";
      btn.addEventListener("click", (e) => { e.stopPropagation(); remove(); changed(); });
      chip.appendChild(btn);
      box.appendChild(chip);
    });
    if (chips.length > 1) {
      const all = document.createElement("button");
      all.type = "button";
      all.className = "ef-link";
      all.textContent = "Alle entfernen";
      all.addEventListener("click", (e) => { e.stopPropagation(); reset(); });
      box.appendChild(all);
    }
  }

  function renderPanel() {
    setSeg("efType", s.type);
    renderCategories();
    renderTags();
    renderAmount();
    renderHeatSelection();
    renderDays();
    const act = activeSections();
    Object.entries(act).forEach(([key, on]) => $("efSec-" + key).classList.toggle("ef-active", on));
    const n = Object.values(act).filter(Boolean).length;
    $("efHandleCount").hidden = !n;
    $("efHandleCount").textContent = n;
    renderChips(act);
  }

  // ── EVENTS ─────────────────────────────────────────────────────────
  function bindEvents() {
    $("efHandle").addEventListener("click", (e) => {
      e.stopPropagation();
      const open = document.body.classList.toggle("ef-open");
      $("efHandle").setAttribute("aria-expanded", open);
    });
    document.querySelectorAll(".ef-section-head").forEach((head) => head.addEventListener("click", (e) => {
      if (!e.target.closest(".ef-link")) head.parentElement.classList.toggle("ef-closed");
    }));

    $("efSearch").addEventListener("input", (e) => { s.q = e.target.value.trim(); changed(DEBOUNCE_MS); });
    $("efType").addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) { s.type = b.dataset.v; changed(); } });

    $("efCats").addEventListener("click", (e) => {
      const row = e.target.closest(".ef-cat");
      if (!row) return;
      const id = row.dataset.cat;
      s.cats.has(id) ? s.cats.delete(id) : s.cats.add(id);
      changed();
    });
    $("efCatsReset").addEventListener("click", () => { s.cats.clear(); changed(); });

    $("efTags").addEventListener("click", (e) => {
      const b = e.target.closest("button");
      if (!b || s.noTags) return;
      const t = b.dataset.tag;
      s.tags.has(t) ? s.tags.delete(t) : s.tags.add(t);
      if (s.tagMode === "strict") renderPanel();
      else applyTags();
    });
    $("efTagMode").addEventListener("click", (e) => {
      const b = e.target.closest("button");
      if (!b || s.noTags || b.dataset.v === s.tagMode) return;
      s.tagMode = b.dataset.v;
      if (s.tagMode === "strict") renderPanel();
      else {
        strictTagOptions.clear();
        applyTags();
      }
    });
    $("efApplyTags").addEventListener("click", () => {
      if (!s.noTags && hasPendingTags()) applyTags();
    });
    $("efNoTags").addEventListener("change", (e) => { s.noTags = e.target.checked; changed(); });

    $("efAmin").addEventListener("input", (e) => { s.amin = Math.min(+e.target.value, s.amax - 5); changed(DEBOUNCE_MS); });
    $("efAmax").addEventListener("input", (e) => { s.amax = Math.max(+e.target.value, s.amin + 5); changed(DEBOUNCE_MS); });

    bindHeatEvents();
    $("efPeriodAll").addEventListener("click", () => { s.period = new Set(); commitPeriod(); });
    $("efDays").addEventListener("click", (e) => {
      const b = e.target.closest(".ef-day");
      if (!b || b.disabled) return;
      const d = +b.dataset.d;
      if (s.days.pick === null) { s.days = { from: d, to: d, pick: d }; }
      else { s.days = { from: Math.min(s.days.pick, d), to: Math.max(s.days.pick, d), pick: null }; }
      changed();
    });

    $("efSort").addEventListener("change", (e) => { s.sort = e.target.value; changed(); });
    $("efResetAll").addEventListener("click", reset);
  }

  function bindHeatEvents() {
    const heat = $("efHeat"), tip = $("efTip");
    const cellAt = (x, y) => {
      const el = document.elementFromPoint(x, y);
      const c = el && el.closest ? el.closest(".ef-hc") : null;
      return c && !c.classList.contains("ef-nodata") ? c : null;
    };
    const preview = (k) => {
      const next = new Set(drag.snap);
      for (let i = Math.min(drag.anchor, k); i <= Math.max(drag.anchor, k); i++) {
        if (overview.has(i)) drag.add ? next.add(i) : next.delete(i);
      }
      s.period = next;
      renderHeatSelection();
    };
    const toggleGroup = (keys) => {
      keys = keys.filter((k) => overview.has(k));
      if (!keys.length) return;
      const all = keys.every((k) => s.period.has(k));
      keys.forEach((k) => (all ? s.period.delete(k) : s.period.add(k)));
      commitPeriod();
    };

    heat.addEventListener("pointerdown", (e) => {
      const c = e.target.closest(".ef-hc");
      if (!c || c.classList.contains("ef-nodata")) return;
      e.preventDefault();
      const k = +c.dataset.k;
      drag = { anchor: k, last: k, add: !s.period.has(k), snap: new Set(s.period) };
      preview(k);
    });
    document.addEventListener("pointermove", (e) => {
      if (!drag) return;
      const c = cellAt(e.clientX, e.clientY);
      if (c && +c.dataset.k !== drag.last) { drag.last = +c.dataset.k; preview(drag.last); }
    });
    document.addEventListener("pointerup", () => {
      if (!drag) return;
      drag = null;
      commitPeriod();
    });

    heat.addEventListener("mousemove", (e) => {
      const c = e.target.closest(".ef-hc");
      if (!c || c.classList.contains("ef-nodata")) { tip.style.display = "none"; return; }
      const k = +c.dataset.k;
      tip.textContent = `${MONTHS_DE[keyM(k) - 1]} ${keyY(k)} · ${fmtNum(overview.get(k).expenseSum)}`;
      tip.style.display = "block";
      tip.style.left = e.clientX + 12 + "px";
      tip.style.top = e.clientY - 30 + "px";
    });
    heat.addEventListener("mouseleave", () => (tip.style.display = "none"));

    heat.addEventListener("click", (e) => {
      const mh = e.target.closest(".ef-mh"), yh = e.target.closest(".ef-yh");
      if (mh) toggleGroup(years.map((y) => mkey(y, +mh.dataset.m)));
      if (yh) toggleGroup([...Array(12)].map((_, i) => mkey(+yh.dataset.y, i + 1)));
    });
  }

  // ── ÖFFENTLICHE SCHNITTSTELLE ──────────────────────────────────────
  return {
    init(options) {
      opts = { ...opts, ...options };
      defaultKey = mkey(options.year, options.month);
      s = blankState();
      bindEvents();
      renderPanel();
    },

    // Monatspicker der Budget-Karte → Zeitraum auf genau diesen Monat setzen (lädt nicht selbst nach)
    setPeriodToMonth(year, month) {
      defaultKey = mkey(year, month);
      s.period = new Set([defaultKey]);
      s.days = blankDays();
      renderPanel();
    },

    async loadOverview() {
      try {
        const data = await fetchJSON("/expensePlanner/entries/overview");
        overview = new Map((data.months || []).map((o) => [mkey(o.year, o.month), {
          expenseSum: Math.abs(+o.expenseSum || 0), entryCount: o.entryCount || 0, days: new Set(o.days || []),
        }]));
      } catch (err) {
        console.error("Jahresübersicht Fehler:", err);
        overview = new Map();
      }
      years = [...new Set([...overview.keys()].map(keyY))].sort((a, b) => a - b);
      buildHeat();
      renderPanel();
    },

    applyFacets(f = {}) {
      facets = {
        categories: new Map((f.categories || []).map((c) => [c.id === null || c.id === undefined ? "none" : String(c.id), Math.abs(+c.expenseSum || 0)])),
        tags: (f.tags || []).map((t) => ({ name: String(t.name), count: t.count || 0 })),
        histogram: Array.isArray(f.amountHistogram) && f.amountHistogram.length === BUCKETS ? f.amountHistogram : new Array(BUCKETS).fill(0),
      };
      renderPanel();
    },

    render: () => renderPanel(),
    toQueryString,
    periodLabel,
    hasActiveFilters,
    reset,
    searchTerm: () => s.q,

    // Gruppierung nach Monat nur bei Datumssortierung und Ergebnissen aus mehreren Monaten
    shouldGroupByMonth(list) {
      return s.sort.startsWith("date") && new Set(list.map((e) => mkey(e.year, e.month))).size > 1;
    },

    buildMonthSeparator(year, month, count) {
      const sep = document.createElement("div");
      sep.className = "ef-month-sep";
      sep.textContent = `${MONTHS_DE[month - 1]} ${year} · ${count}`;
      return sep;
    },

    // Schreibt text in el und markiert Vorkommen des Suchbegriffs
    highlightInto(el, text) {
      el.textContent = "";
      const q = s.q.toLowerCase();
      if (!q) { el.textContent = text; return; }
      const lower = text.toLowerCase();
      let i = 0, j;
      while ((j = lower.indexOf(q, i)) !== -1) {
        if (j > i) el.append(text.slice(i, j));
        const mark = document.createElement("mark");
        mark.className = "ef-mark";
        mark.textContent = text.slice(j, j + q.length);
        el.appendChild(mark);
        i = j + q.length;
      }
      el.append(text.slice(i));
    },
  };
})();
// ════════════════════════════════════════════════════════════════════
// ── FILTER-SIDEBAR (Ende) ────────────────────────────────────────────
// ════════════════════════════════════════════════════════════════════

// ── INIT ────────────────────────────────────────────────────────────────
// FILTER: Sidebar initialisieren (Startzeitraum = aktueller Monat)
ExpenseFilter.init({
  year: currentYear,
  month: currentMonth + 1,
  getCategories: () => categories,
  onChange: () => loadEntries().catch((e) => console.error(e)),
  // Genau ein Monat in der Jahresübersicht gewählt → Budget-Karte zieht mit
  onSingleMonth: (year, month) => {
    currentYear = year;
    currentMonth = month - 1;
    updatePickerLabel();
    loadSummary().catch((e) => console.error(e));
  },
});
updatePickerLabel();
refreshAllData().catch((e) => console.error(e));
