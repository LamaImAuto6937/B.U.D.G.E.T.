        // Dark Mode beim Laden anwenden
        (function() {
            const isDarkMode = localStorage.getItem('darkMode') === 'true';
            if (isDarkMode) {
                document.body.classList.add('dark-mode');
            }
        })();

        // Global variable to store current detail item
        let currentDetailItem = null;

        // Initialize on page load
        document.addEventListener('DOMContentLoaded', () => {
            loadBudgetData();
            // Set default date to today for date inputs
            setDefaultDate();
        });

        function setDefaultDate() {
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('revenueStartDate').value = today;
            document.getElementById('expenseStartDate').value = today;
        }

        function getDurationText(duration) {
            switch(duration) {
                case 1:
                    return 'Monatlich';
                case 4:
                    return 'Vierteljährlich';
                case 12:
                    return 'Jährlich';
                default:
                    return `Alle ${duration} Monate`;
            }
        }

        function formatDate(dateString) {
            if (!dateString) return '-';
            const date = new Date(dateString);
            return date.toLocaleDateString('de-DE', { year: 'numeric', month: '2-digit', day: '2-digit' });
        }

        function loadBudgetData() {
            Promise.all([
                fetch('/api/budget/monthly-totals').then(r => {
                    if (!r.ok) throw new Error(`HTTP ${r.status}`);
                    return r.json();
                }),
                fetch('/api/budget/items').then(r => {
                    if (!r.ok) throw new Error(`HTTP ${r.status}`);
                    return r.json();
                })
            ])
                .then(([totals, records]) => {
                    // DEIN FORMAT: [amount, description, flag, user_id, id, duration, created_at, start_date, monthly_rate]
                    const processItems = (items) => {
                        if (!Array.isArray(items)) return [];
                        return items.map(item => {
                            let amount = 0;
                            let description = 'Unnamed';
                            let duration = 1;
                            let id = null;
                            let createdAt = null;
                            let startDate = null;
                            let monthlyRate = 0;
                            let yearlyRate = 0;
                            
                            if (Array.isArray(item)) {
                                amount = parseFloat(item[0]) || 0;
                                description = item[1] || 'Unnamed';
                                id = item[4] || null;
                                duration = parseInt(item[5]) || 1;
                                createdAt = item[6] || null;
                                startDate = item[7] || null;
                                monthlyRate = parseFloat(item[8]) || 0;
                                yearlyRate = parseFloat(item[9]) || 0;
                            } else if (typeof item === 'object') {
                                amount = parseFloat(item.amount) || 0;
                                description = item.description || 'Unnamed';
                                duration = parseInt(item.duration) || 1;
                                id = item.id || null;
                                createdAt = item.created_at || null;
                                startDate = item.start_date || null;
                                monthlyRate = parseFloat(item.monthly_rate) || 0;
                                yearlyRate = parseFloat(item.yearlyRate) || 0;
                            }
                            
                            return {
                                description: description,
                                amount: amount,
                                monthlyRate: monthlyRate,
                                yearlyRate: yearlyRate,
                                duration: duration,
                                id: id,
                                createdAt: createdAt,
                                startDate: startDate
                            };
                        });
                    };
                    
                    console.log('DEBUG - Received records:', records);
                    
                    updateBudgetData({
                        revenue: totals.monthlyRevenue || 0,
                        expense: totals.monthlyExpense || 0,
                        revenueItems: processItems(records.revenue),
                        expenseItems: processItems(records.expense)
                    });
                })
                .catch(error => {
                    console.error('Fehler:', error);
                    showError('Fehler beim Laden der Budget-Daten. Bitte versuchen Sie es später erneut.');
                });
        }

        function showError(message) {
            const container = document.getElementById('errorContainer');
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.textContent = message;
            container.innerHTML = '';
            container.appendChild(errorDiv);
        }

        function updateBudgetData(data) {
            const revenue = data.revenue || 0;
            const expense = data.expense || 0;
            const budget = revenue - expense;

            updateBudgetAmount(budget);
            updateProgressBar(expense, revenue);
            updateBudgetChart(revenue, expense);
            updateRevenueCards(data.revenueItems || []);
            updateExpenseCards(data.expenseItems || []);
        }

        function updateBudgetAmount(budget) {
            const element = document.getElementById('budgetAmount');
            const isNegative = budget < 0;
            const color = isNegative ? '#e74c3c' : '#27ae60';
            element.textContent = `€ ${Math.abs(budget).toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            element.style.color = color;
        }

        function updateProgressBar(expense, revenue) {
            const percentage = revenue > 0 ? (expense / revenue * 100) : 0;
            const percentage_rounded = Math.min(percentage, 100);

            const progressFill = document.getElementById('progressFill');
            const percentageLabel = document.getElementById('percentageLabel');

            progressFill.style.width = percentage_rounded + '%';
            percentageLabel.textContent = percentage_rounded.toFixed(1) + '%';
        }

        function updateBudgetChart(revenue, expense) {
            const ctx = document.getElementById('budgetChart').getContext('2d');

            if (window.budgetChartInstance) {
                window.budgetChartInstance.destroy();
            }

            window.budgetChartInstance = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Einnahmen', 'Ausgaben'],
                    datasets: [{
                        data: [revenue, expense],
                        backgroundColor: ['#36a2eb', '#ff6384'],
                        borderColor: ['#2980b9', '#e74c3c'],
                        borderWidth: 2,
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return '€ ' + context.parsed.toLocaleString('de-DE', { 
                                        minimumFractionDigits: 2, 
                                        maximumFractionDigits: 2 
                                    });
                                }
                            }
                        }
                    }
                }
            });
        }

        function updateRevenueCards(items) {
            const container = document.getElementById('revenueCardsContainer');
            container.innerHTML = '';

            if (items.length === 0) {
                container.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #999;">Keine Einnahmen vorhanden</p>';
                return;
            }

            items.forEach(item => {
                item.flag = 1; // Mark as revenue
                const card = createItemCard(item, '#36a2eb');
                container.appendChild(card);
            });
        }

        function updateExpenseCards(items) {
            const container = document.getElementById('expenseCardsContainer');
            container.innerHTML = '';

            if (items.length === 0) {
                container.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #999;">Keine Ausgaben vorhanden</p>';
                return;
            }

            items.forEach(item => {
                item.flag = 0; // Mark as expense
                const card = createItemCard(item, '#ff6384');
                container.appendChild(card);
            });
        }

        function createItemCard(item, accentColor) {
            const card = document.createElement('div');
            card.className = 'item-card';
            card.style.borderLeftColor = accentColor;
            card.style.borderLeftWidth = '3px';
            
            // Click to open detail dialog
            card.onclick = () => openDetailDialog(item);

            card.innerHTML = `
                <button class="delete-item-btn" onclick="handleDeleteEntry(event, ${item.id})" title="Löschen">−</button>
                <div class="item-description" title="${item.description}">${item.description}</div>
                <div class="item-monthly-rate">€ ${item.monthlyRate.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
            `;

            return card;
        }

        // Dialog Functions - Revenue
        function openAddRevenueDialog() {
            setDefaultDate();
            document.getElementById('addRevenueBackdrop').classList.add('open');
            document.getElementById('revenueAmount').focus();
        }

        function closeAddRevenueDialog(event) {
            if (event && event.target !== event.currentTarget) return;
            document.getElementById('addRevenueBackdrop').classList.remove('open');
        }

        // Dialog Functions - Expense
        function openAddExpenseDialog() {
            setDefaultDate();
            document.getElementById('addExpenseBackdrop').classList.add('open');
            document.getElementById('expenseAmount').focus();
        }

        function closeAddExpenseDialog(event) {
            if (event && event.target !== event.currentTarget) return;
            document.getElementById('addExpenseBackdrop').classList.remove('open');
        }

        // Detail Dialog Functions
        function openDetailDialog(item) {
            currentDetailItem = item;
            document.getElementById('detailTitle').textContent = `📋 ${item.description}`;
            document.getElementById('detailName').textContent = item.description;
            document.getElementById('detailAmount').textContent = `€ ${item.amount.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            document.getElementById('detailMonthlyRate').textContent = `€ ${item.monthlyRate.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            document.getElementById('detailYearlyRate').textContent = `€ ${item.yearlyRate.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            document.getElementById('detailDuration').textContent = getDurationText(item.duration);
            document.getElementById('detailCreatedAt').textContent = formatDate(item.createdAt);
            document.getElementById('detailStartDate').textContent = formatDate(item.startDate);
            
            document.getElementById('detailBackdrop').classList.add('open');
        }

        function closeDetailDialog(event) {
            if (event && event.target !== event.currentTarget) return;
            document.getElementById('detailBackdrop').classList.remove('open');
            currentDetailItem = null;
        }

        function deleteFromDetail() {
            if (currentDetailItem) {
                handleDeleteEntry(null, currentDetailItem.id, true);
            }
        }

        // Handle Add Entry
        async function handleAddEntry(event, flag) {
            event.preventDefault();

            const isRevenue = flag === 1;
            const amountId = isRevenue ? 'revenueAmount' : 'expenseAmount';
            const descriptionId = isRevenue ? 'revenueDescription' : 'expenseDescription';
            const durationId = isRevenue ? 'revenueDuration' : 'expenseDuration';
            const startDateId = isRevenue ? 'revenueStartDate' : 'expenseStartDate';

            const betrag = document.getElementById(amountId).value;
            const description = document.getElementById(descriptionId).value;
            const duration = document.getElementById(durationId).value;
            const startDate = document.getElementById(startDateId).value;

            const formData = new FormData();
            formData.append('betrag', betrag);
            formData.append('description', description);
            formData.append('flag', flag);
            formData.append('duration', duration);
            formData.append('start_date', startDate);

            try {
                const response = await fetch('/add_entry', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    if (isRevenue) {
                        closeAddRevenueDialog();
                        document.getElementById('revenueAmount').value = '';
                        document.getElementById('revenueDescription').value = '';
                        document.getElementById('revenueDuration').value = '1';
                        document.getElementById('revenueStartDate').value = new Date().toISOString().split('T')[0];
                    } else {
                        closeAddExpenseDialog();
                        document.getElementById('expenseAmount').value = '';
                        document.getElementById('expenseDescription').value = '';
                        document.getElementById('expenseDuration').value = '1';
                        document.getElementById('expenseStartDate').value = new Date().toISOString().split('T')[0];
                    }

                    setTimeout(() => loadBudgetData(), 500);
                    showSuccess(`${isRevenue ? 'Einnahme' : 'Ausgabe'} erfolgreich hinzugefügt!`);
                } else {
                    const error = await response.text();
                    showError(error);
                }
            } catch (error) {
                console.error('Error:', error);
                showError('Fehler beim Hinzufügen. Bitte versuchen Sie es später erneut.');
            }
        }

        // Handle Delete Entry
        async function handleDeleteEntry(event, monthlyBudgetID, fromDetail = false) {
            if (event) {
                event.stopPropagation();
            }

            if (!confirm('Möchten Sie diesen Eintrag wirklich löschen?')) {
                return;
            }

            const formData = new FormData();
            formData.append('monthlyBudgetID', monthlyBudgetID);

            try {
                const response = await fetch('/remove_entry', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    if (fromDetail) {
                        closeDetailDialog();
                    }
                    setTimeout(() => loadBudgetData(), 500);
                    showSuccess('Eintrag erfolgreich gelöscht!');
                } else {
                    const error = await response.text();
                    showError(error);
                }
            } catch (error) {
                console.error('Error:', error);
                showError('Fehler beim Löschen. Bitte versuchen Sie es später erneut.');
            }
        }

        function showSuccess(message) {
            const container = document.getElementById('errorContainer');
            const successDiv = document.createElement('div');
            successDiv.className = 'error-message';
            successDiv.style.backgroundColor = '#d4edda';
            successDiv.style.color = '#155724';
            successDiv.style.borderColor = '#c3e6cb';
            successDiv.textContent = '✅ ' + message;
            container.innerHTML = '';
            container.appendChild(successDiv);

            setTimeout(() => {
                successDiv.remove();
            }, 3000);
        }

        // Close dialogs with ESC key
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                closeAddRevenueDialog();
                closeAddExpenseDialog();
                closeDetailDialog();
                closeEditDialog();
            }
        });

        // Edit Dialog Functions
        function openEditDialog() {
            if (!currentDetailItem) return;
            
            document.getElementById('editAmount').value = currentDetailItem.amount;
            document.getElementById('editDescription').value = currentDetailItem.description;
            document.getElementById('editFlag').value = currentDetailItem.flag;
            document.getElementById('editDuration').value = currentDetailItem.duration;
            document.getElementById('editStartDate').value = currentDetailItem.startDate;
            
            document.getElementById('detailBackdrop').classList.remove('open');
            document.getElementById('editBackdrop').classList.add('open');
        }

        function closeEditDialog(event) {
            if (event && event.target !== event.currentTarget) return;
            document.getElementById('editBackdrop').classList.remove('open');
        }

        async function handleUpdateEntry(event) {
            event.preventDefault();

            const betrag = document.getElementById('editAmount').value;
            const description = document.getElementById('editDescription').value;
            const flag = document.getElementById('editFlag').value;
            const duration = document.getElementById('editDuration').value;
            const start_date = document.getElementById('editStartDate').value;

            const formData = new FormData();
            formData.append('betrag', betrag);
            formData.append('description', description);
            formData.append('flag', flag);
            formData.append('duration', duration);
            formData.append('start_date', start_date);
            formData.append('monthlyBudgetID', currentDetailItem.id);

            try {
                const response = await fetch('/monthlyBudget/update_entry', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    closeEditDialog();
                    showSuccess('Eintrag erfolgreich aktualisiert!');
                    loadBudgetData();
                } else {
                    const text = await response.text();
                    showError(text || 'Fehler beim Aktualisieren.');
                }
            } catch (error) {
                console.error('Error:', error);
                showError('Fehler beim Aktualisieren. Bitte versuchen Sie es später erneut.');
            }
        }