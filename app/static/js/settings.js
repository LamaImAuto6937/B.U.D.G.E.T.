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

        // Store current user data
        let currentUserData = {
            username: '',
            email: ''
        };

        // Load and display account information
        async function loadAccountInfo() {
            try {
                const response = await fetch('/settings/user_info');
                const data = await response.json();
                
                if (data.success) {
                    currentUserData.username = data.username || '';
                    currentUserData.email = data.email || '';
                    
                    document.getElementById('display-username').textContent = currentUserData.username;
                    document.getElementById('display-email').textContent = currentUserData.email;
                    document.getElementById('display-password').textContent = '********';
                } else {
                    console.error('Fehler beim Laden der Konto-Informationen:', data.error);
                }
            } catch (err) {
                console.error('Fehler beim Abrufen der Konto-Informationen:', err);
            }
        }

        // Load account info when page loads
        window.addEventListener('load', loadAccountInfo);

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

        // ==========================================
        // UPDATE CREDENTIALS DIALOG
        // ==========================================

        // Password visibility toggle for credentials dialog
        function toggleCredPw(id, btn) {
            const inp = document.getElementById(id);
            const show = inp.type === 'text';
            inp.type = show ? 'password' : 'text';
            const EYE_OPEN = '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12S5 5 12 5s11 7 11 7-4 7-11 7S1 12 1 12z"/><circle cx="12" cy="12" r="3"/></svg>';
            const EYE_OFF = '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';
            btn.innerHTML = show ? EYE_OPEN : EYE_OFF;
            btn.setAttribute('aria-label', show ? 'Passwort anzeigen' : 'Passwort verbergen');
        }

        // Password strength evaluation (Kriterien)
        function evalCredentialCriteria(pw) {
            return {
                len: pw.length >= 8,
                upper: /[A-ZÄÖÜ]/.test(pw),
                lower: /[a-zäöüß]/.test(pw),
                digit: /[0-9]/.test(pw),
                special: /[^A-Za-z0-9äöüÄÖÜß]/.test(pw) || /[äöüÄÖÜß]/.test(pw),
            };
        }

        // Calculate password strength
        function calcCredentialStrength(pw) {
            if (!pw) return 0;
            const c = evalCredentialCriteria(pw);
            let score = 0;

            // Complexity points (max 5)
            if (c.len) score++;
            if (c.upper) score++;
            if (c.lower) score++;
            if (c.digit) score++;
            if (c.special) score++;

            // Bonus for longer passwords
            if (pw.length >= 12) score++;
            if (pw.length >= 16) score++;

            // Hard penalties
            const COMMON = /passwort|password|passw0rt|123456|qwertz|qwerty|abcdef|letmein|willkommen|hallo|login|admin|berlin/i;
            const SEQ_NUM = /01234|12345|23456|34567|45678|56789|67890/;
            if (COMMON.test(pw)) score -= 4;
            if (SEQ_NUM.test(pw)) score -= 1;

            // Must have minimum length
            if (!c.len) score = Math.min(score, 1);

            score = Math.max(0, score);

            if (score <= 1) return 1; // Sehr schwach
            if (score <= 3) return 2; // Schwach
            if (score <= 5) return 3; // Mittel
            return 4;                 // Stark
        }

        // Strength config
        const STRENGTH_CONFIG = [
            null,
            { label: 'Sehr schwach', cls: 's1', color: '#e05c4b' },
            { label: 'Schwach', cls: 's2', color: '#e08a3b' },
            { label: 'Mittel', cls: 's3', color: '#b8a000' },
            { label: 'Stark', cls: 's4', color: 'var(--color-success)' },
        ];

        // Toggle criteria badge
        function toggleCrit(id, met) {
            const badge = document.getElementById(id);
            if (badge) {
                badge.classList.toggle('met', met);
            }
        }

        // Password visibility toggle
        function togglePw(id, btn) {
            const inp = document.getElementById(id);
            const show = inp.type === 'text';
            inp.type = show ? 'password' : 'text';
            const EYE_OPEN = '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12S5 5 12 5s11 7 11 7-4 7-11 7S1 12 1 12z"/><circle cx="12" cy="12" r="3"/></svg>';
            const EYE_OFF = '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';
            btn.innerHTML = show ? EYE_OPEN : EYE_OFF;
            btn.setAttribute('aria-label', show ? 'Passwort anzeigen' : 'Passwort verbergen');
        }

        // ==========================================
        // ACCOUNT INFO HOVER EFFECTS
        // ==========================================
        
        function showEditIcon(element) {
            const editBtn = element.querySelector('.account-edit-btn');
            if (editBtn) {
                editBtn.style.display = 'flex';
            }
        }

        function hideEditIcon(element) {
            const editBtn = element.querySelector('.account-edit-btn');
            if (editBtn) {
                editBtn.style.display = 'none';
            }
        }

        // ==========================================
        // USERNAME DIALOG
        // ==========================================
        
        function openUsernameDialog() {
            document.getElementById("usernameDialogBackdrop").classList.add("open");
            document.getElementById("usernameForm").reset();
            document.getElementById("username-input").focus();
        }

        function openUsernameDialogWithValue() {
            document.getElementById("usernameDialogBackdrop").classList.add("open");
            document.getElementById("usernameForm").reset();
            document.getElementById("username-input").value = currentUserData.username;
            document.getElementById("username-input").focus();
        }

        function cancelUsernameDialog() {
            document.getElementById("usernameDialogBackdrop").classList.remove("open");
        }

        async function handleUpdateUsername(event) {
            event.preventDefault();
            
            const newUsername = document.getElementById('username-input').value.trim();
            const msgElement = document.getElementById('username-msg');
            
            // Validation
            if (!newUsername) {
                msgElement.textContent = 'Benutzername erforderlich';
                msgElement.className = 'field-msg error';
                return;
            }
            
            msgElement.textContent = '';
            msgElement.className = 'field-msg';
            
            try {
                const submitBtn = event.target.querySelector('button[type="submit"]');
                const originalText = submitBtn.textContent;
                submitBtn.textContent = 'Wird verarbeitet...';
                submitBtn.disabled = true;
                
                const formData = new FormData();
                formData.append('new_username', newUsername);
                
                const response = await fetch('/settings/updateCredentials/username', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    alert('Benutzername erfolgreich aktualisiert!');
                    cancelUsernameDialog();
                    loadAccountInfo();
                } else {
                    msgElement.textContent = 'Fehler beim Aktualisieren';
                    msgElement.className = 'field-msg error';
                }
                
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            } catch (err) {
                msgElement.textContent = 'Fehler: ' + err.message;
                msgElement.className = 'field-msg error';
            }
        }

        // ==========================================
        // EMAIL DIALOG
        // ==========================================
        
        function openEmailDialog() {
            document.getElementById("emailDialogBackdrop").classList.add("open");
            document.getElementById("emailForm").reset();
            document.getElementById("email-input").focus();
        }

        function openEmailDialogWithValue() {
            document.getElementById("emailDialogBackdrop").classList.add("open");
            document.getElementById("emailForm").reset();
            document.getElementById("email-input").value = currentUserData.email;
            document.getElementById("email-input").focus();
        }

        function cancelEmailDialog() {
            document.getElementById("emailDialogBackdrop").classList.remove("open");
        }

        async function handleUpdateEmail(event) {
            event.preventDefault();
            
            const newEmail = document.getElementById('email-input').value.trim();
            const msgElement = document.getElementById('email-msg');
            
            // Validation
            if (!newEmail || !newEmail.includes('@')) {
                msgElement.textContent = 'Gültige E-Mail erforderlich';
                msgElement.className = 'field-msg error';
                return;
            }
            
            msgElement.textContent = '';
            msgElement.className = 'field-msg';
            
            try {
                const submitBtn = event.target.querySelector('button[type="submit"]');
                const originalText = submitBtn.textContent;
                submitBtn.textContent = 'Wird verarbeitet...';
                submitBtn.disabled = true;
                
                const formData = new FormData();
                formData.append('new_email', newEmail);
                
                const response = await fetch('/settings/updateCredentials/email', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    alert('E-Mail erfolgreich aktualisiert!');
                    cancelEmailDialog();
                    loadAccountInfo();
                } else {
                    msgElement.textContent = 'Fehler beim Aktualisieren';
                    msgElement.className = 'field-msg error';
                }
                
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            } catch (err) {
                msgElement.textContent = 'Fehler: ' + err.message;
                msgElement.className = 'field-msg error';
            }
        }

        // ==========================================
        // PASSWORD DIALOG
        // ==========================================
        
        function openPasswordDialog() {
            document.getElementById("passwordDialogBackdrop").classList.add("open");
            document.getElementById("passwordForm").reset();
            document.getElementById("password-strength-fill").style.width = '0%';
            document.getElementById("password-strength-label").textContent = 'Passwort eingeben';
            document.getElementById("password-confirm").classList.remove('input-success', 'input-error');
            document.getElementById("password-confirm-msg").className = 'field-msg muted';
            document.getElementById("password-input").focus();
        }

        function cancelPasswordDialog() {
            document.getElementById("passwordDialogBackdrop").classList.remove("open");
        }

        // On password input - update strength bar and criteria
        function onPasswordInput() {
            const pw = document.getElementById('password-input').value;
            const fill = document.getElementById('password-strength-fill');
            const lbl = document.getElementById('password-strength-label');
            const crit = evalCredentialCriteria(pw);
            const level = calcCredentialStrength(pw);

            // Update bar
            fill.className = 'strength-bar-fill';
            if (!pw) {
                fill.style.width = '0%';
                lbl.textContent = 'Passwort eingeben';
                lbl.style.color = 'var(--color-text-faint)';
            } else {
                const cfg = STRENGTH_CONFIG[level];
                fill.classList.add(cfg.cls);
                fill.style.width = (level * 25) + '%';
                lbl.textContent = cfg.label;
                lbl.style.color = cfg.color;
            }

            // Update criteria badges
            toggleCrit('password-crit-len', crit.len);
            toggleCrit('password-crit-upper', crit.upper);
            toggleCrit('password-crit-lower', crit.lower);
            toggleCrit('password-crit-digit', crit.digit);
            toggleCrit('password-crit-special', crit.special);

            // Check if passwords match
            checkPasswordConfirm();
        }

        // Confirm password match
        function checkPasswordConfirm() {
            const pw1 = document.getElementById('password-input').value;
            const pw2 = document.getElementById('password-confirm').value;
            const inp = document.getElementById('password-confirm');
            const msg = document.getElementById('password-confirm-msg');

            if (!pw2) {
                inp.classList.remove('input-success', 'input-error');
                msg.textContent = '';
                msg.className = 'field-msg muted';
                return;
            }

            const match = pw1 === pw2;
            inp.classList.toggle('input-success', match);
            inp.classList.toggle('input-error', !match);
            msg.textContent = match ? '✓ Passwörter stimmen überein' : '✗ Passwörter stimmen nicht überein';
            msg.className = 'field-msg ' + (match ? 'success' : 'error');
        }

        // Handle blur on password confirm field
        function onPasswordConfirmBlur() {
            const pw2 = document.getElementById('password-confirm');
            const inp = document.getElementById('password-confirm');
            const msg = document.getElementById('password-confirm-msg');

            // If field is empty, clear it on blur
            if (pw2.value.trim() === '') {
                inp.classList.remove('input-success', 'input-error');
                msg.textContent = '';
                msg.className = 'field-msg muted';
            }
        }

        async function handleUpdatePassword(event) {
            event.preventDefault();
            
            const pw1 = document.getElementById('password-input').value;
            const pw2 = document.getElementById('password-confirm').value;
            const msgElement = document.getElementById('password-msg');
            const level = calcCredentialStrength(pw1);
            
            // Validation
            if (!pw1) {
                msgElement.textContent = 'Passwort erforderlich';
                msgElement.className = 'field-msg error';
                return;
            }
            
            if (pw1.length < 8) {
                msgElement.textContent = 'Passwort muss mindestens 8 Zeichen lang sein';
                msgElement.className = 'field-msg error';
                return;
            }
            
            if (level < 2) {
                msgElement.textContent = 'Passwort ist zu schwach';
                msgElement.className = 'field-msg error';
                return;
            }
            
            if (pw1 !== pw2) {
                document.getElementById('password-confirm-msg').textContent = '✗ Passwörter stimmen nicht überein';
                document.getElementById('password-confirm-msg').className = 'field-msg error';
                return;
            }
            
            msgElement.textContent = '';
            msgElement.className = 'field-msg';
            
            try {
                const submitBtn = event.target.querySelector('button[type="submit"]');
                const originalText = submitBtn.textContent;
                submitBtn.textContent = 'Wird verarbeitet...';
                submitBtn.disabled = true;
                
                const formData = new FormData();
                formData.append('new_password', pw1);
                
                const response = await fetch('/settings/updateCredentials/password', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    alert('Passwort erfolgreich aktualisiert!');
                    cancelPasswordDialog();
                    loadAccountInfo();
                } else {
                    msgElement.textContent = 'Fehler beim Aktualisieren';
                    msgElement.className = 'field-msg error';
                }
                
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            } catch (err) {
                msgElement.textContent = 'Fehler: ' + err.message;
                msgElement.className = 'field-msg error';
            }
        }


