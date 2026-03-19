        // Dark Mode Logic
        const darkModeSlider = document.getElementById('darkModeSlider');
        const darkModeLabel = document.getElementById('darkModeLabel');
        const body = document.body;

        // Load saved dark mode preference
        const savedDarkMode = localStorage.getItem('darkMode') === 'true';
        if (savedDarkMode) {
            body.classList.add('dark-mode');
            darkModeSlider.classList.add('active');
            darkModeLabel.textContent = 'An';
        }

        // Toggle Dark Mode
        darkModeSlider.addEventListener('click', () => {
            body.classList.toggle('dark-mode');
            darkModeSlider.classList.toggle('active');
            const isDarkMode = body.classList.contains('dark-mode');
            darkModeLabel.textContent = isDarkMode ? 'An' : 'Aus';
            localStorage.setItem('darkMode', isDarkMode);
        });

        // Panel Navigation
        const settingsBtns = document.querySelectorAll('.settings-btn');
        const panels = document.querySelectorAll('.settings-panel');

        settingsBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                // Remove active class from all buttons and panels
                settingsBtns.forEach(b => b.classList.remove('active'));
                panels.forEach(p => p.classList.remove('active'));

                // Add active class to clicked button and corresponding panel
                btn.classList.add('active');
                const panelId = btn.getAttribute('data-panel');
                document.getElementById(panelId).classList.add('active');
            });
        });

        // Theme Selection
        const themeSelect = document.getElementById('themeSelect');
        themeSelect.addEventListener('change', (e) => {
            localStorage.setItem('theme', e.target.value);
            // Hier könnten weitere CSS-Variable geändert werden
            console.log('Theme gewechselt zu:', e.target.value);
        });

        // Load saved theme
        const savedTheme = localStorage.getItem('theme') || 'blue';
        themeSelect.value = savedTheme;

        // Reset Budget for Current Month in Expense Planner
        function resetBudget() 
        {
            fetch("/settings/resetBudgetForCurrentMonth")
            .then(r => r.text())
            .then(msg => {
                alert("Budget zurückgesetzt!");
            })
            .catch(err => alert("Fehler: " + err));
        } 

        // DIALOG
        function openDeleteDialog() {
            document.getElementById("deleteDialogBackdrop").classList.add("open");
        }

        function cancelDelete() {
            document.getElementById("deleteDialogBackdrop").classList.remove("open");
        }

        function confirmDelete() 
        {
            fetch("/settings/deleteAccount")
                .then(r => r.text())
                .then(msg => {
                    alert("Du Monster hast es vollbracht... Konto Erfolgreich gelöscht...");
                    window.location.href = "/";
                })
                .catch(err => alert("Fehler: " + err));
        } 

        // Backdrop-Klick schließt den Dialog
        document.getElementById("deleteDialogBackdrop").addEventListener("click", function(e) {
            if (e.target === this) cancelDelete();
        });

