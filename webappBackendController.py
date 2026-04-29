from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from functools import wraps
from DatabaseOperationClasses import *
from ModuleOperationClasses import *
from datetime import datetime, timedelta
import os, hashlib, random
from dotenv import load_dotenv

# Load .env File
load_dotenv()

# Generate Random Secret Key for the current Session
salt = os.urandom(16)
key = random.randint(0,10000)
secret_key = hashlib.sha512(salt + str(key).encode('utf-8')).hexdigest()


app = Flask(__name__)
app.secret_key = secret_key
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)


# ================================================================
# Login-Check-Decorator
# ================================================================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


# ================================================================
# Index / Modul-Auswahl
# ================================================================
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    return render_template("index.html")


# ================================================================
# LOGIN / LOGOUT
# ================================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        

        # Über GeneralOperations prüfen, ob User existiert
        DataProvider = userDBOperations()
        HelperClass = Helper()
        LoginClass = loginClass(DataProvider, HelperClass)
        user_id, is_valid = LoginClass.procValidateLogin(username, password)

        if is_valid and user_id is not None:
            session["user_id"] = user_id  
            session["username"] = username
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Ungültiger Benutzername oder Passwort.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/create_user", methods=["POST"])
def create_user():
    username = request.form.get("new_username")
    password = request.form.get("new_password")
    email = request.form.get("new_email")

    DataProvider = userDBOperations()
    HelperClass = Helper()
    ops = loginClass(DataProvider, HelperClass)

    try:
        # procCreateNewUser hasht intern bereits das Passwort
        success = ops.procCreateNewUser(username, password, email)
        
        if success:
            return render_template("login.html", success="Benutzer erfolgreich erstellt! Bitte einloggen.")
        else:
            return render_template("login.html", error="Benutzername existiert bereits.")
    except Exception as e:
        return render_template("login.html", error=f"Fehler beim Erstellen: {str(e)}")

# Reset Password
@app.route("/reset_password", methods=["POST"])
def reset_password():
    email = request.form.get("email")
    DataProvider = userDBOperations()
    helperObject = Helper()
    loginObject = loginClass(DataProvider, helperObject)
    
    try:
        
        found_user = DataProvider.getUserByUsernameOrEmail(email)
        
        if not found_user:
            return jsonify({"success": True, "message": "Wenn die E-Mail-Adresse mit einem Konto verknüpft ist, wird eine Reset-E-Mail gesendet."}), 200
        else:
            user_id = found_user[0]
            
        token = hashlib.sha512(os.urandom(16) + str(random.randint(0,10000)).encode('utf-8')).hexdigest()
        DataProvider.doUpdateCredentialsPassword(user_id, helperObject.generateHash(token))
        loginObject.sentResetPasswordEmail(email, token)
        
        return jsonify({"success": True, "message": "Wenn die E-Mail-Adresse mit einem Konto verknüpft ist, wird eine Reset-E-Mail gesendet."}), 200
    
    except Exception as e:
        print(f"Fehler beim Zurücksetzen des Passworts: {str(e)}")
        return jsonify({"success": False, "message": "Fehler beim Verarbeiten der Anfrage."}), 500
    
    
    
# ================================================================
# MONTHLY BUDGET 
# ================================================================

@app.route("/monthlyBudget")
@login_required
def monthly_budget():
    return render_template("monthlyBudget.html")

@app.route("/api/budget/monthly-totals")
@login_required
def api_monthly_totals():
    """
    GET /api/budget/monthly-totals
    Gibt die monatlichen Gesamtbeträge zurück
    """
    DataProvider = monthlyBudgetDBOperations()
    HelperClass = Helper()
    GeneralOps = monthlyBudget(HelperClass, DataProvider)
    user_id = session["user_id"]
    
    try:
        Revenue = GeneralOps.procCalculateRevenue(user_id)
        Expense = GeneralOps.procCalculateExpense(user_id)
        
        return jsonify({
            "monthlyRevenue": Revenue,
            "monthlyExpense": Expense
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/budget/items")
@login_required
def api_budget_items():
    """
    GET /api/budget/items
    Gibt alle Budget Items separiert nach Revenue/Expense zurück
    """
    DataProvider = monthlyBudgetDBOperations()
    HelperOps = Helper()
    MonthlyBudgetOps = monthlyBudget(HelperOps, DataProvider)
    user_id = session["user_id"]
    
    try:

        # Hinzufügen der Monthly Rate in die einzelnen Listen innerhalb der Liste
        revenue_items = HelperOps.convertNestedTupleIntoList(DataProvider.getRevenueData(user_id))
        for i in range(len(revenue_items)):
            revenue_items[i].append(MonthlyBudgetOps.procCalculateDebitRate(revenue_items[i][0],revenue_items[i][5])) # Monthly Rate
            revenue_items[i].append(MonthlyBudgetOps.procCalculateYearlyRate(revenue_items[i][0],revenue_items[i][5]))
        print(revenue_items)

        expense_items = HelperOps.convertNestedTupleIntoList(DataProvider.getExpenseData(user_id))
        for i in range(len(expense_items)):
            expense_items[i].append(MonthlyBudgetOps.procCalculateDebitRate(expense_items[i][0],expense_items[i][5]))
            expense_items[i].append(MonthlyBudgetOps.procCalculateYearlyRate(expense_items[i][0],expense_items[i][5]))

        #print(f"Rev: {revenue_items} \n Exp: {expense_items}")
        return jsonify({
                    "revenue": revenue_items,
                    "expense": expense_items
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/add_entry", methods=["POST"])
@login_required
def add_entry():
    """
    POST /add_entry
    Fügt einen neuen Budget-Eintrag hinzu
    """
    DataProvider = monthlyBudgetDBOperations()
    HelperOps = Helper()
    MonthlyBudgetOps = monthlyBudget(HelperOps, DataProvider)
    user_id = session["user_id"]
    
    betrag = request.form.get("betrag")
    description = request.form.get("description")
    flag = request.form.get("flag")
    duration = request.form.get("duration")
    start_date = request.form.get("start_date")
    
    if not betrag or not description or flag is None:
        return "FEHLER: Ungültige Eingabe!", 400
    
    try:
        DataProvider.doAppendToMonthlyBudget(float(betrag), description, int(flag), user_id, int(duration), str(start_date))
        return "Eintrag erfolgreich hinzugefügt!"
    except Exception as e:
        return f"Fehler beim Hinzufügen: {str(e)}", 500

@app.route("/remove_entry", methods=["POST"])
@login_required
def remove_entry():
    """
    POST /remove_entry
    Entfernt einen Budget-Eintrag
    """
    DataProvider = monthlyBudgetDBOperations()
    monthlyBudgetID = request.form.get("monthlyBudgetID")
    
    if not monthlyBudgetID:
        return "FEHLER: Kein Eintrag ausgewählt!", 400
    
    try:
        DataProvider.doDeleteFromMonthlyBudget(monthlyBudgetID)
        return "Eintrag erfolgreich entfernt!"
    except Exception as e:
        return f"Fehler beim Entfernen: {str(e)}", 500


@app.route("/monthlyBudget/update_entry", methods=["POST"])
@login_required
def monthlyBudget_update_entry():
    """
    POST /monthlyBudget/update_entry
    Aktualisiert einen Budget-Eintrag
    """
    DataProvider = monthlyBudgetDBOperations()
    
    betrag = request.form.get("betrag")
    description = request.form.get("description")
    flag = request.form.get("flag")
    duration = request.form.get("duration")
    start_date = request.form.get("start_date")
    monthlyBudgetID = request.form.get("monthlyBudgetID")
    
    if not betrag or not description or flag is None or not monthlyBudgetID:
        return "FEHLER: Ungültige Eingabe!", 400
    
    try:
        DataProvider.doUpdateMonthlyBudgetEntry(float(betrag), description, int(flag), int(duration), str(start_date), int(monthlyBudgetID))
        return "Eintrag erfolgreich aktualisiert!"
    except Exception as e:
        return f"Fehler beim Aktualisieren: {str(e)}", 500

# ================================================================
# EXPENSE PLANNER
# ================================================================
@app.route("/expensePlanner")
@login_required
def expense_planner():
    return render_template("expensePlanner.html")


@app.route("/expensePlanner/summary")
@login_required
def get_expense_summary_values():
    user_id = session["user_id"]
    month = int(request.args.get("month"))
    year = int(request.args.get("year"))

    ExpensePlannerDataProvider = expensePlannerDBOperations()
    MonthlyBudgetDataProvider = monthlyBudgetDBOperations()
    HelperClass = Helper()

    MonthlyBudgetOps = monthlyBudget(HelperClass, MonthlyBudgetDataProvider)
    ExpensePlannerOps = expensePlanner(MonthlyBudgetOps, ExpensePlannerDataProvider, HelperClass)

    try:

        budgetFound, Budget = ExpensePlannerOps.procCheckIfBudgetIsAvailable(user_id, month, year)
        Expense = ExpensePlannerOps.procCalculateExpense(user_id, month, year)
        Saved = ExpensePlannerOps.procCalculateSaved(Budget, Expense)
        ExpensePercentage = ExpensePlannerOps.procCalculatePercentage(Budget, Expense)
        

        return jsonify({
            "budget": Budget,
            "expenseSum": Expense,
            "saved": Saved,
            "expensePercentage": ExpensePercentage,
            "needsBudget": not budgetFound,
            "globalBudget": Budget
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/expensePlanner/add", methods=["POST"])
@login_required
def add_expense():
    DataProvider = expensePlannerDBOperations()
    user_id = session["user_id"]

    try:
        amount = float(request.form.get("amount"))
        description = request.form.get("description")
        day = int(request.form.get("day"))
        month = int(request.form.get("month"))
        year = int(request.form.get("year"))

        DataProvider.doAppendToExpensePlanner(day, month, year, amount, description, user_id)
        return "Expense hinzugefügt!"
    except Exception as e:
        return f"Fehler beim Hinzufügen: {str(e)}", 500


@app.route("/expensePlanner/remove", methods=["POST"])
@login_required
def expense_remove():
    DataProvider = expensePlannerDBOperations()

    

    try:
        entry_id = request.form.get("entry_id")
        
        if not entry_id:
            return "Kein Eintrag ausgewählt!", 400
        
        DataProvider.doDeleteFromExpensePlanner(int(entry_id))
        return "Ausgabe erfolgreich entfernt!"
    except Exception as e:
        return f"Fehler beim Entfernen: {str(e)}", 500

@app.route("/expensePlanner/update", methods=["POST"])
@login_required
def update_entry():
    DataProvider = expensePlannerDBOperations()
    
    
    try:
        amount = float(request.form.get("amount"))
        description = request.form.get("description")
        day = int(request.form.get("day"))
        month = int(request.form.get("month"))
        year = int(request.form.get("year"))
        entry_id = int(request.form.get("entry_id"))
        
        DataProvider.doUpdateExpensePlannerEntry(float(amount), str(description), int(day), int(month), int(year), int(entry_id))
        return "Eintrag aktualisiert!"
    except Exception as e:
        return f"Fehler beim Hinzufügen: {str(e)}", 500
    
    

@app.route("/expensePlanner/get", methods=["GET"])
@login_required
def get_expenses():
    DataProvider = expensePlannerDBOperations()
    user_id = session["user_id"]

    try:
        month = int(request.args.get("month"))
        year = int(request.args.get("year"))
        rows = DataProvider.getAusgabenFromExpensePlanner(month, year, user_id)

        return jsonify([
            {
                "day": int(r[2]),
                "month": int(r[3]),
                "year": int(r[4]),
                "amount": float(r[0]),
                "description": r[1],
                "id" : r[6]
            }
            for r in rows
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/expensePlanner/setBudget", methods=["POST"])
@login_required
def expensePlanner_setBudget():
    DataProvider = expensePlannerDBOperations()
    user_id = session["user_id"]

    try:
        amount = float(request.form.get("amount"))
        month = int(request.form.get("month"))
        year = int(request.form.get("year"))

        DataProvider.doAppendToSetBudgetForSelectedMonth(user_id, amount, month, year)

        return "Budget gespeichert!"
    except Exception as e:
        return f"Fehler beim Speichern: {str(e)}", 500


# ================================================================
# SETTINGS
# ================================================================
@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html")

@app.route("/settings/user_info", methods=["GET"])
@login_required
def api_user_info():
    """
    GET /settings/user_info
    Gibt die aktuellen Benutzerdaten zurück
    """
    user_id = session["user_id"]
    Dataprovider = userDBOperations()
    
    try:
        # Get user data from database
        user = Dataprovider.getUserByUserId(user_id)
        
        if user:
            return jsonify({
                "success": True,
                "username": user[0], 
                "email": user[1]      
            })
        else:
            return jsonify({"success": False, "error": "User nicht gefunden"}), 404
    
    except Exception as e:
        print(str(e))
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/settings/resetBudgetForCurrentMonth", methods=["GET"])
@login_required
def resetBudget():
    user_id = session["user_id"]
    Dataprovider = expensePlannerDBOperations()
    today = datetime.now()
    
    try:
        
        Dataprovider.doDeleteFromSetBudgetForSelectedMonth(user_id, today.month, today.year)

    except Exception as e:
        print(str(e))
        
@app.route("/settings/deleteAccount", methods=["GET"])
@login_required

def deleteAccount():
    user_id = session["user_id"]
    Dataprovider = userDBOperations()
    
    try:
        
        session.clear()
        Dataprovider.doDeleteFromUsers(user_id)
        return (f"Konto [{user_id}] erfolgreich gelöscht", 200)
    
    except Exception as e:
        print(str(e))
        return ("Fehler beim Löschen", 500)
    
# ================================================================
# UPDATE CREDENTIALS
# ================================================================
@app.route("/settings/updateCredentials/username", methods=["POST"])
@login_required
def updateCredentialsUsername():
    user_id = session["user_id"]
    Dataprovider = userDBOperations()

    try:
        new_username = request.form.get("new_username")
        
        Dataprovider.doUpdateCredentialsUsername(user_id, new_username)

        return (f"Konto [{user_id}] erfolgreich aktualisiert", 200)
    
    except Exception as e:
        print(str(e))
        return ("Fehler beim Aktualisieren", 500)

@app.route("/settings/updateCredentials/password", methods=["POST"])
@login_required
def updateCredentialsPassword():
    user_id = session["user_id"]
    Dataprovider = userDBOperations()
    helper = Helper()
    
    try:
        new_password = request.form.get("new_password")
        
        # Hash the password using scrypt (via werkzeug.security.generate_password_hash)
        # This uses default scrypt parameters (N=2^15, r=8, p=1)
        hashed_password = helper.generateHash(new_password)
        
        Dataprovider.doUpdateCredentialsPassword(user_id, hashed_password)

        return (f"Konto [{user_id}] erfolgreich aktualisiert", 200)
    
    except Exception as e:
        print(str(e))
        return ("Fehler beim Aktualisieren", 500)

@app.route("/settings/updateCredentials/email", methods=["POST"])
@login_required
def updateCredentialsEmail():
    user_id = session["user_id"]
    Dataprovider = userDBOperations()
    
    try:
        new_email = request.form.get("new_email")
        Dataprovider.doUpdateCredentialsEmail(user_id, new_email)

        return (f"Konto [{user_id}] erfolgreich aktualisiert", 200)
    
    except Exception as e:
        print(str(e))
        return ("Fehler beim Aktualisieren", 500)
# ================================================================
# Savings Plan
# ================================================================
@app.route("/savingsPlan")
@login_required
def savingsPlan():
    return render_template("savingsPlan.html")

@app.route("/api/savings/plans", methods=["GET"])
@login_required
def api_get_savings_plans():
    """
    GET /api/savings/plans
    Gibt alle Sparpläne des aktuellen Benutzers mit aktuellem Stand zurück
    """
    try:
        user_id = session["user_id"]
        
        # Sparpläne vom Backend abrufen
        db_ops = savingPlanDBOperations()
        plans_data = db_ops.getPlanDetails(user_id)
        
        if not plans_data:
            return jsonify({"success": True, "plans": []})
        
        # Für jeden Plan den aktuellen Betrag berechnen
        plans = []
        HelperClass = Helper()
        Dataprovider = savingPlanDBOperations()
        saving_plan = SavingPlan(HelperClass, Dataprovider)
        
        for plan in plans_data:
            plan_id = plan[0]  # Tuple: id
            current_amount = saving_plan.procCalculateSavedAmount(plan_id)
            
            plans.append({
                "id": plan[0],
                "plan_name": plan[2],
                "description": plan[3],
                "target_amount": plan[4],
                "current_amount": current_amount,
                "created_at": str(plan[5])
            })
        
        return jsonify({"success": True, "plans": plans})
    
    except Exception as e:
        print(f"Fehler beim Abrufen der Sparpläne: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/savings/plan/<int:plan_id>", methods=["GET"])
@login_required
def api_get_savings_plan_details(plan_id):
    """
    GET /api/savings/plan/<plan_id>
    Gibt Details eines spezifischen Sparplans mit allen Transaktionen zurück
    """
    try:
        user_id = session["user_id"]
        
        # Plan Details direkt nach plan_id abrufen (mit user_id Sicherheitscheck)
        db_ops = savingPlanDBOperations()
        plan = db_ops.getPlanById(plan_id, user_id)
        
        #print(f"Gesuchte plan_id: {plan_id}, Gefundener plan: {plan}")
        if not plan:
            return jsonify({"success": False, "error": "Plan nicht gefunden"}), 404
        
        # Aktuellen Betrag berechnen
        HelperClass = Helper()
        saving_plan = SavingPlan(HelperClass, db_ops)
        current_amount = saving_plan.procCalculateSavedAmount(plan_id)
        
        # Transaktionen abrufen
        transactions_data = db_ops.getAccountingSummary(int(plan_id))
        
        # Transaktionen formatieren und sortieren (neueste zuerst)
        transactions = []
        for tx in transactions_data:
            transactions.append({
                "id": tx[0],
                "plan_id": tx[1],
                "amount": float(tx[2]),
                "expense_flag": tx[3],  # 0 = Abhebung, 1 = Einzahlung
                "created_at": str(tx[4]),
                "description": tx[5]
            })
        
        # Transaktionen nach Datum absteigend sortieren (neueste zuerst)
        transactions.sort(key=lambda x: x["created_at"], reverse=True)
        
        return jsonify({
            "success": True,
            "plan": {
                "id": plan[0],
                "plan_name": plan[2],
                "description": plan[3],
                "target_amount": float(plan[4]),
                "current_amount": float(current_amount),
                "created_at": str(plan[5])
            },
            "transactions": transactions
        })
    
    except Exception as e:
        print(f"Fehler beim Abrufen der Plan Details: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/savings/plan/<int:plan_id>", methods=["DELETE"])
@login_required
def api_delete_savings_plan(plan_id):
    """
    DELETE /api/savings/plan/<plan_id>
    Löscht einen Sparplan und alle zugehörigen Transaktionen
    """
    try:
        user_id = session["user_id"]
        
        # Sicherheitscheck: Prüfen ob der Plan dem aktuellen Benutzer gehört
        db_ops = savingPlanDBOperations()
        plan = db_ops.getPlanById(plan_id, user_id)
        
        if not plan:
            return jsonify({"success": False, "error": "Plan nicht gefunden"}), 404
        
        db_ops.doDeleteAllPlanEntriesFromAccounting(plan_id)
        db_ops.doDeletePlan(plan_id)
        
        print(f"Sparplan gelöscht: ID={plan_id}, User={user_id}")
        return jsonify({"success": True})
    
    except Exception as e:
        print(f"Fehler beim Löschen des Sparplans: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/savings/plan", methods=["POST"])
@login_required
def api_create_savings_plan():

    try:
        Dataprovider = savingPlanDBOperations()

        user_id = session.get("user_id")
        data = request.get_json()
        
        plan_name = data.get("plan_name")
        description = data.get("description", "")
        target_amount = data.get("target_amount")
        
        if not plan_name or not target_amount:
            return jsonify({"success": False, "error": "Plan Name und Zielbetrag erforderlich"}), 400
        
        # Validierung
        try:
            target_amount = float(target_amount)
            if target_amount <= 0:
                return jsonify({"success": False, "error": "Zielbetrag muss größer als 0 sein"}), 400
        except ValueError:
            return jsonify({"success": False, "error": "Zielbetrag muss eine Zahl sein"}), 400
        
        
        Dataprovider.doCreateNewPlan(int(user_id), str(plan_name), str(description), float(target_amount))

        return jsonify({"success": True})
    
    except Exception as e:
        print(f"Fehler beim Erstellen des Sparplans: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/savings/transaction-from-expense", methods=["POST"])
@login_required
def api_add_savings_transaction_from_expense():

    try:
        user_id = session.get("user_id")
        data = request.get_json()
        
        plan_id = data.get("plan_id")
        amount = data.get("amount")
        description = data.get("description", "")
        
        if not plan_id or not amount:
            return jsonify({"success": False, "error": "Plan ID und Betrag erforderlich"}), 400
        

        # Validierung
        try:
            amount = float(amount)
            if amount <= 0:
                return jsonify({"success": False, "error": "Betrag muss größer als 0 sein"}), 400
        except ValueError:
            return jsonify({"success": False, "error": "Betrag muss eine Zahl sein"}), 400
        

        # Sicherheitscheck: Prüfen ob der Plan dem aktuellen Benutzer gehört
        db_ops = savingPlanDBOperations()
        plan = db_ops.getPlanById(plan_id, user_id)
        
        if not plan:
            return jsonify({"success": False, "error": "Plan nicht gefunden"}), 404
        
        # ================================================================
        # 1. Transaktion zum Sparplan hinzufügen (EINNAHME = expense_flag: 1)
        # ================================================================

        db_ops.doAppendToAccounting(plan_id, amount, 1, description)
        
        # ================================================================
        # 2. Ausgabe im Expense Planner für den heutigen Tag erzeugen
        # ================================================================
        from datetime import datetime
        today = datetime.now()
        day = today.day
        month = today.month
        year = today.year
        
        expense_planner_db = expensePlannerDBOperations()
        expense_planner_db.doAppendToExpensePlanner(
            day=day,
            month=month,
            year=year,
            betragAusgabe=amount,
            bezeichnungDerAusgabe=description if description else "Sparplan Transfer",
            user_id=user_id
        )
        
        print(f"Sparplan Transaktion erstellt: Plan ID={plan_id}, Amount={amount}, Description={description}")
        print(f"Expense Planner Ausgabe erzeugt: {amount}€ am {day}.{month}.{year}")
        
        return jsonify({"success": True})
    
    except Exception as e:
        print(f"Fehler beim Hinzufügen der Transaktion vom Expense Planner: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/savings/transaction", methods=["POST"])
@login_required
def api_add_savings_transaction():

    try:
        data = request.get_json()
        Dataprovider = savingPlanDBOperations()
        plan_id = data.get("plan_id")
        amount = data.get("amount")
        expense_flag = data.get("expense_flag")
        description = data.get("description", "")
        
        if not plan_id or not amount or expense_flag is None:
            return jsonify({"success": False, "error": "Plan ID, Betrag und Expense Flag erforderlich"}), 400
        

        Dataprovider.doAppendToAccounting(plan_id, amount, expense_flag, description)
        
        return jsonify({"success": True})
    
    except Exception as e:
        print(f"Fehler beim Hinzufügen der Transaktion: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/savings/transaction/<int:transaction_id>", methods=["DELETE"])
@login_required
def api_delete_savings_transaction(transaction_id):
    """
    DELETE /api/savings/transaction/<transaction_id>
    Löscht eine Transaktion aus einem Sparplan
    
    Sicherheitscheck: Prüft ob die Transaktion dem aktuellen Benutzer gehört
    """
    try:
        user_id = session.get("user_id")
        Dataprovider = savingPlanDBOperations()
        print(transaction_id)
        
        # ================================================================
        # Transaktion löschen
        # ================================================================
        Dataprovider.doDeleteFromAccounting(int(transaction_id))
        
        print(f"Transaktion gelöscht: ID={transaction_id}, User={user_id}")
        return jsonify({"success": True})
    
    except Exception as e:
        print(f"Fehler beim Löschen der Transaktion: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
# ================================================================
# STARTEN
# ================================================================
if __name__ == "__main__":
    app.run(debug=True)
