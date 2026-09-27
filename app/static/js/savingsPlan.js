        // Dark Mode beim Laden anwenden
        (function() {
            const isDarkMode = localStorage.getItem('darkMode') === 'true';
            if (isDarkMode) {
                document.body.classList.add('dark-mode');
            }
        })();

        let selectedPlanId = null;
        let planToDelete = null;
        let transactionToDelete = null;
        let fabMenuOpen = false;

        // Sparpläne laden
        async function loadPlans() {
            try {
                const response = await fetch('/api/savings/plans');
                const data = await response.json();

                if (data.success) {
                    const plansList = document.getElementById('plansList');
                    plansList.innerHTML = '';

                    data.plans.forEach(plan => {
                        const progressPercentage = (plan.current_amount / plan.target_amount) * 100;

                        const planCard = document.createElement('div');
                        planCard.className = 'plan-card';
                        planCard.id = `plan-card-${plan.id}`;
                        planCard.innerHTML = `
                            <div class="plan-card-header">
                                <div class="plan-name">${plan.plan_name}</div>
                                <button class="delete-plan-btn" onclick="handleDeleteClick(event, ${plan.id})">−</button>
                            </div>
                            <div class="plan-amount">€${parseFloat(plan.current_amount).toFixed(2)}</div>
                            <div class="progress-bar-container">
                                <div class="progress-bar" style="width: ${Math.min(progressPercentage, 100)}%"></div>
                            </div>
                        `;

                        planCard.addEventListener('click', () => {
                            selectPlan(plan.id, planCard);
                        });

                        plansList.appendChild(planCard);
                    });

                    // ADD NEW PLAN CARD hinzufügen
                    const addCard = document.createElement('div');
                    addCard.className = 'add-plan-card';
                    addCard.innerHTML = '<div class="add-plan-icon">+</div>';
                    addCard.addEventListener('click', openPlanDialog);
                    plansList.appendChild(addCard);
                } else {
                    document.getElementById('plansList').innerHTML = '<div class="content-empty">Keine Sparpläne vorhanden</div>';
                }
            } catch (error) {
                console.error('Fehler beim Laden der Sparpläne:', error);
            }
        }

        // Plan auswählen und Details laden
        async function selectPlan(planId, cardElement) {
            selectedPlanId = planId;

            // Aktive Karte aktualisieren
            document.querySelectorAll('.plan-card').forEach(card => {
                card.classList.remove('active');
            });
            cardElement.classList.add('active');

            // Menu schließen
            closeFabMenu();

            // Details laden
            await loadPlanDetails(planId);
        }

        // Plan Details und Transaktionen laden
        async function loadPlanDetails(planId) {
            try {
                const response = await fetch(`/api/savings/plan/${planId}`);
                const data = await response.json();

                if (data.success) {
                    const contentArea = document.getElementById('contentArea');
                    const fabContainer = document.getElementById('fabContainer');
                    const plan = data.plan;
                    const transactions = data.transactions;

                    const progressPercentage = (plan.current_amount / plan.target_amount) * 100;

                    let transactionsHTML = '';
                    if (transactions.length > 0) {
                        transactionsHTML = transactions.map(tx => {
                            const isIncome = tx.expense_flag === 1;
                            const amount = `${isIncome ? '+' : '-'}€${Math.abs(parseFloat(tx.amount)).toFixed(2)}`;
                            const amountClass = isIncome ? 'income' : 'expense';
                            const date = new Date(tx.created_at).toLocaleDateString('de-DE');

                            return `
                                <div class="transaction-card">
                                    <div class="transaction-amount ${amountClass}">${amount}</div>
                                    <div class="transaction-middle">${tx.description}</div>
                                    <div class="transaction-date">${date}</div>
                                    <button class="delete-transaction-btn" onclick="openDeleteTransactionDialog(${tx.id})">−</button>
                                </div>
                            `;
                        }).join('');
                    } else {
                        transactionsHTML = '<div class="no-transactions">Keine Transaktionen vorhanden</div>';
                    }

                    // Entferne zuerst FAB Container temporär
                    fabContainer.remove();

                    // Ersetze komplett den Inhalt
                    contentArea.innerHTML = `
                        <div class="content-header">
                            <div class="plan-title">${plan.plan_name}</div>
                            <div class="plan-description">${plan.description}</div>
                        </div>

                        <div class="progress-section">
                            <div class="progress-info">
                                <span>€0</span>
                                <span>€${parseFloat(plan.target_amount).toFixed(2)}</span>
                            </div>
                            <div class="progress-bar-large">
                                <div class="progress-bar-large-fill" style="width: ${Math.min(progressPercentage, 100)}%"></div>
                            </div>
                            <div style="color: #7f8c8d; font-size: 13px;">
                                €${parseFloat(plan.current_amount).toFixed(2)} / €${parseFloat(plan.target_amount).toFixed(2)} (${Math.round(progressPercentage)}%)
                            </div>
                        </div>

                        <div class="transactions-section">
                            <div class="transactions-title">Verlauf</div>
                            <div class="transactions-container">
                                ${transactionsHTML}
                            </div>
                        </div>
                    `;

                    // Füge FAB Container wieder am Ende hinzu
                    contentArea.appendChild(fabContainer);
                    fabContainer.style.display = 'block';
                }
            } catch (error) {
                console.error('Fehler beim Laden der Plan Details:', error);
            }
        }

        // FAB MENU FUNKTIONEN
        function toggleFabMenu() {
            fabMenuOpen = !fabMenuOpen;
            const menu = document.getElementById('fabMenu');
            if (fabMenuOpen) {
                menu.classList.add('active');
            } else {
                menu.classList.remove('active');
            }
        }

        function closeFabMenu() {
            fabMenuOpen = false;
            const menu = document.getElementById('fabMenu');
            menu.classList.remove('active');
        }

        // DELETE PLAN HANDLER
        function handleDeleteClick(event, planId) {
            event.stopPropagation();
            
            const planCard = document.getElementById(`plan-card-${planId}`);
            if (!planCard.classList.contains('active')) {
                console.warn('Delete-Button ist nicht verfügbar - Plan ist nicht aktiv');
                return;
            }
            
            openDeleteDialog(planId);
        }

        // DELETE TRANSACTION HANDLER
        function openDeleteTransactionDialog(transactionId) {
            transactionToDelete = transactionId;
            document.getElementById('deleteTransactionDialog').classList.add('active');
        }

        function closeDeleteTransactionDialog() {
            document.getElementById('deleteTransactionDialog').classList.remove('active');
            transactionToDelete = null;
        }

        async function confirmDeleteTransaction() {
            if (!transactionToDelete) return;

            try {
                const response = await fetch(`/api/savings/transaction/${transactionToDelete}`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const data = await response.json();

                if (data.success) {
                    closeDeleteTransactionDialog();
                    loadPlans();
                    loadPlanDetails(selectedPlanId);
                    alert('Transaktion erfolgreich gelöscht!');
                } else {
                    alert('Fehler beim Löschen der Transaktion: ' + data.error);
                }
            } catch (error) {
                console.error('Fehler beim Löschen der Transaktion:', error);
                alert('Ein Fehler ist aufgetreten!');
            }
        }

        // MANUAL TRANSACTION DIALOG
        function openManualTransactionDialog() {
            closeFabMenu();
            document.getElementById('manualTransactionDialog').classList.add('active');
        }

        function closeManualTransactionDialog() {
            document.getElementById('manualTransactionDialog').classList.remove('active');
            document.getElementById('transactionAmount').value = '';
            document.getElementById('transactionType').checked = false;
            document.getElementById('transactionDesc').value = '';
            updateToggleValue();
        }

        function updateToggleValue() {
            const toggle = document.getElementById('transactionType');
            const valueSpan = document.getElementById('toggleValue');
            if (toggle.checked) {
                valueSpan.textContent = 'Einzahlung (+)';
            } else {
                valueSpan.textContent = 'Abhebung (−)';
            }
        }

        document.getElementById('transactionType').addEventListener('change', updateToggleValue);

        async function submitManualTransaction() {
            const amount = document.getElementById('transactionAmount').value.trim();
            const expenseFlag = document.getElementById('transactionType').checked ? 1 : 0;
            const description = document.getElementById('transactionDesc').value.trim();

            if (!amount || parseFloat(amount) <= 0) {
                alert('Bitte gib einen gültigen Betrag ein!');
                return;
            }

            if (!description) {
                alert('Bitte gib eine Beschreibung ein!');
                return;
            }

            try {
                const response = await fetch(`/api/savings/transaction`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        plan_id: selectedPlanId,
                        amount: parseFloat(amount),
                        expense_flag: expenseFlag,
                        description: description
                    })
                });

                const data = await response.json();

                if (data.success) {
                    closeManualTransactionDialog();
                    loadPlans();
                    loadPlanDetails(selectedPlanId);
                    alert('Transaktion hinzugefügt!');
                } else {
                    alert('Fehler: ' + data.error);
                }
            } catch (error) {
                console.error('Fehler:', error);
                alert('Ein Fehler ist aufgetreten!');
            }
        }

        // EXPENSE PLANNER TRANSACTION DIALOG
        function openExpenseTransactionDialog() {
            closeFabMenu();
            document.getElementById('expenseTransactionDialog').classList.add('active');
        }

        function closeExpenseTransactionDialog() {
            document.getElementById('expenseTransactionDialog').classList.remove('active');
            document.getElementById('expenseAmount').value = '';
            document.getElementById('expenseDesc').value = '';
        }

        async function submitExpenseTransaction() {
            const amount = document.getElementById('expenseAmount').value.trim();
            const description = document.getElementById('expenseDesc').value.trim();

            if (!amount || parseFloat(amount) <= 0) {
                alert('Bitte gib einen gültigen Betrag ein!');
                return;
            }

            if (!description) {
                alert('Bitte gib eine Beschreibung ein!');
                return;
            }

            try {
                const response = await fetch(`/api/savings/transaction-from-expense`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        plan_id: selectedPlanId,
                        amount: parseFloat(amount),
                        description: description
                    })
                });

                const data = await response.json();

                if (data.success) {
                    closeExpenseTransactionDialog();
                    loadPlans();
                    loadPlanDetails(selectedPlanId);
                    alert('Transaktion hinzugefügt und Ausgabe im Expense Planner registriert!');
                } else {
                    alert('Fehler: ' + data.error);
                }
            } catch (error) {
                console.error('Fehler:', error);
                alert('Ein Fehler ist aufgetreten!');
            }
        }

        // CREATE NEW PLAN DIALOG
        function openPlanDialog() {
            document.getElementById('createPlanDialog').classList.add('active');
        }

        function closePlanDialog() {
            document.getElementById('createPlanDialog').classList.remove('active');
            document.getElementById('planName').value = '';
            document.getElementById('planDescription').value = '';
            document.getElementById('targetAmount').value = '';
        }

        async function createNewPlan() {
            const planName = document.getElementById('planName').value.trim();
            const planDescription = document.getElementById('planDescription').value.trim();
            const targetAmount = document.getElementById('targetAmount').value.trim();

            if (!planName) {
                alert('Bitte gib einen Sparplan Namen ein!');
                return;
            }

            if (!targetAmount || parseFloat(targetAmount) <= 0) {
                alert('Bitte gib einen gültigen Zielbetrag ein!');
                return;
            }

            try {
                const response = await fetch('/api/savings/plan', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        plan_name: planName,
                        description: planDescription,
                        target_amount: parseFloat(targetAmount)
                    })
                });

                const data = await response.json();

                if (data.success) {
                    closePlanDialog();
                    loadPlans();
                    alert('Sparplan erfolgreich erstellt!');
                } else {
                    alert('Fehler beim Erstellen des Sparplans: ' + data.error);
                }
            } catch (error) {
                console.error('Fehler beim Erstellen des Sparplans:', error);
                alert('Ein Fehler ist aufgetreten!');
            }
        }

        // DELETE PLAN DIALOG
        function openDeleteDialog(planId) {
            planToDelete = planId;
            document.getElementById('deletePlanDialog').classList.add('active');
        }

        function closeDeleteDialog() {
            document.getElementById('deletePlanDialog').classList.remove('active');
            planToDelete = null;
        }

        async function confirmDeletePlan() {
            if (!planToDelete) return;

            try {
                const response = await fetch(`/api/savings/plan/${planToDelete}`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const data = await response.json();

                if (data.success) {
                    closeDeleteDialog();
                    selectedPlanId = null;
                    
                    // WICHTIG: Nur den Content leeren, NICHT den FAB-Container entfernen!
                    const contentArea = document.getElementById('contentArea');
                    const fabContainer = document.getElementById('fabContainer');
                    
                    // Alle Kinder außer FAB-Container entfernen
                    while (contentArea.firstChild && contentArea.firstChild !== fabContainer) {
                        contentArea.removeChild(contentArea.firstChild);
                    }
                    
                    // Neuen Empty-Content hinzufügen (VOR dem FAB-Container)
                    const emptyDiv = document.createElement('div');
                    emptyDiv.className = 'content-empty';
                    emptyDiv.textContent = 'Wähle einen Sparplan aus';
                    contentArea.insertBefore(emptyDiv, fabContainer);
                    
                    // FAB-Container verstecken
                    fabContainer.style.display = 'none';
                    
                    // Sparpläne neu laden
                    await loadPlans();
                    
                    alert('Sparplan erfolgreich gelöscht!');
                } else {
                    alert('Fehler beim Löschen des Sparplans: ' + data.error);
                }
            } catch (error) {
                console.error('Fehler beim Löschen des Sparplans:', error);
                alert('Ein Fehler ist aufgetreten!');
            }
        }

        // Dialog schließen wenn auf Overlay geklickt wird
        document.getElementById('createPlanDialog').addEventListener('click', function(event) {
            if (event.target === this) closePlanDialog();
        });

        document.getElementById('deletePlanDialog').addEventListener('click', function(event) {
            if (event.target === this) closeDeleteDialog();
        });

        document.getElementById('deleteTransactionDialog').addEventListener('click', function(event) {
            if (event.target === this) closeDeleteTransactionDialog();
        });

        document.getElementById('manualTransactionDialog').addEventListener('click', function(event) {
            if (event.target === this) closeManualTransactionDialog();
        });

        document.getElementById('expenseTransactionDialog').addEventListener('click', function(event) {
            if (event.target === this) closeExpenseTransactionDialog();
        });

        // Sparpläne beim Laden der Seite initialisieren
        document.addEventListener('DOMContentLoaded', loadPlans);