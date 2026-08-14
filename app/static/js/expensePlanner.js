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

async function loadEntries() {
  const data = await fetchJSON(
    `/expensePlanner/get?month=${currentMonth + 1}&year=${currentYear}`
  );
  if (data.error) {
    console.error("Einträge Fehler:", data.error);
    entries = [];
  } else {
    entries = data.map((r) => ({
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
      tags: r.tags || [],
    }));
  }
  renderEntriesOnly();
}

async function refreshAllData() {
  await Promise.all([loadCategories(), loadSummary(), loadEntries()]);
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
    alert("Fehler beim Speichern des Budgets: " + err.message);
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
  document.getElementById("entriesLabel").textContent = `${MONTHS_DE[currentMonth]} ${currentYear}`;
  const list = document.getElementById("entriesList");
  list.innerHTML = "";

  if (!entries || entries.length === 0) {
    list.innerHTML = `<div class="empty-state"><div class="icon"></div><p>Keine Einträge für diesen Monat.</p></div>`;
    return;
  }

  [...entries].sort((a, b) => b.date - a.date).forEach((entry) => {
    const tile = document.createElement("div");
    tile.className = "entry-tile";
    tile.style.borderLeftColor = entry.mainCat && entry.mainCatColor ? entry.mainCatColor : "var(--border-strong)";

    const info = document.createElement("div");
    info.className = "entry-info";

    const topRow = document.createElement("div");
    topRow.className = "entry-top-row";
    const descSpan = document.createElement("span");
    descSpan.className = "entry-description";
    descSpan.textContent = entry.desc;
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
    await loadSummary();
  } catch (err) {
    console.error(err);
    alert("Fehler beim Entfernen: " + err.message);
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
  tagInput.disabled = limitReached;
  tagInput.placeholder = limitReached ? "Maximal 2 Tags erreicht" : "Tag eingeben und Enter drücken...";
  document.getElementById("tagLimitMsg").textContent = limitReached ? "Maximal 2 zusätzliche Tags erreicht." : "";
  if (limitReached) hideSuggestions();
}

function hideSuggestions() {
  tagSuggestionsEl.classList.remove("open");
  tagSuggestionsEl.innerHTML = "";
  highlightedSuggestIndex = -1;
}

function addTag(rawTag) {
  const tag = rawTag.trim();
  if (!tag || selectedSubTags.length >= 2) return;
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
  if (!q || selectedSubTags.length >= 2) { hideSuggestions(); return; }

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
  selectedSubTags = (editingEntry.tags || []).slice();
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
    alert("Bitte Beschreibung und gültigen Betrag eingeben.");
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
    alert("Fehler: " + err.message);
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

// ── INIT ────────────────────────────────────────────────────────────────
updatePickerLabel();
refreshAllData().catch((e) => console.error(e));
