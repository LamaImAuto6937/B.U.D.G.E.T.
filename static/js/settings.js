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
        const sidebar = document.querySelector('.settings-sidebar');
        const sidebarToggle = document.getElementById('sidebarToggle');
        const sidebarBackdrop = document.getElementById('sidebarBackdrop');

        function openSidebar() {
            if (sidebar) {
                sidebar.classList.add('open');
            }
            if (sidebarBackdrop) {
                sidebarBackdrop.classList.add('open');
            }
            document.body.classList.add('sidebar-open');
        }

        function closeSidebar() {
            if (sidebar) {
                sidebar.classList.remove('open');
            }
            if (sidebarBackdrop) {
                sidebarBackdrop.classList.remove('open');
            }
            document.body.classList.remove('sidebar-open');
        }

        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                if (sidebar && sidebar.classList.contains('open')) {
                    closeSidebar();
                } else {
                    openSidebar();
                }
            });
        }

        if (sidebarBackdrop) {
            sidebarBackdrop.addEventListener('click', closeSidebar);
        }

        settingsBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                // Remove active class from all buttons and panels
                settingsBtns.forEach(b => b.classList.remove('active'));
                panels.forEach(p => p.classList.remove('active'));

                // Add active class to clicked button and corresponding panel
                btn.classList.add('active');
                const panelId = btn.getAttribute('data-panel');
                document.getElementById(panelId).classList.add('active');

                // On mobile, close the sidebar after selection
                if (window.innerWidth <= 768) {
                    closeSidebar();
                }
            });
        });

        // Close sidebar on resize to avoid stuck state
        window.addEventListener('resize', () => {
            if (window.innerWidth > 768) {
                if (sidebar) {
                    sidebar.classList.remove('open');
                }
            } else {
                closeSidebar();
            }
        });

        // Ensure initial mobile sidebar state is closed
        if (window.innerWidth <= 768) {
            closeSidebar();
        }

        // Theme Selection
        const themeSelect = document.getElementById('themeSelect');
        if (themeSelect) {
            themeSelect.addEventListener('change', (e) => {
                localStorage.setItem('theme', e.target.value);
                // Hier könnten weitere CSS-Variable geändert werden
                console.log('Theme gewechselt zu:', e.target.value);
            });

            // Load saved theme
            const savedTheme = localStorage.getItem('theme') || 'blue';
            themeSelect.value = savedTheme;
        }

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

