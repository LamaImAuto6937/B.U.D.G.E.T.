from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from functools import wraps
from DatabaseOperationClass import DatabaseOperations
from generalOperationClass import GeneralOperations
from datetime import datetime, timedelta
import os, hashlib, random


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
    if request.method == "POST":
        module = request.form.get("module")

        if module == "monthlyBudget":
            return redirect(url_for("monthly_budget"))
        elif module == "expensePlanner":
            return redirect(url_for("expense_planner"))
        else:
            return render_template("index.html", error="Unbekanntes Modul gewählt.")

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
        DataProvider = DatabaseOperations()
        ops = GeneralOperations(DataProvider)
        user_id, is_valid = ops.procValidateLogin(username, password)

        if is_valid and user_id is not None:
            session["user_id"] = user_id  # ← nur die Zahl speichern
            session["username"] = username
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Ungültiger Benutzername oder Passwort.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ================================================================
# MONTHLY BUDGET
# ================================================================
@app.route("/monthlyBudget")
@login_required
def monthly_budget():
    return render_template("monthlyBudget.html")


@app.route("/add_entry", methods=["POST"])
@login_required
def add_entry():
    DataProvider = DatabaseOperations()
    user_id = session["user_id"]
    betrag = request.form.get("betrag")
    description = request.form.get("description")
    expense_flag = request.form.get("flag")

    if not betrag or not description or not expense_flag:
        return "FEHLER: Ungültige Eingabe!"

    try:
        DataProvider.doAppendToMonthlyBudget(float(betrag), description, expense_flag, user_id)
        return "Eintrag erfolgreich hinzugefügt!"
    except Exception as e:
        return f"Fehler beim Hinzufügen: {str(e)}", 500


@app.route("/remove_entry", methods=["POST"])
@login_required
def remove_entry():
    DataProvider = DatabaseOperations()
    user_id = session["user_id"]
    value = request.form.get("entry")

    if not value:
        return "FEHLER: Kein Eintrag ausgewählt!"

    try:
        amount, description, flag = value.split("|")
        DataProvider.doDeleteFromMonthlyBudget(float(amount), description, flag, user_id)
        return "Eintrag erfolgreich entfernt!"
    except Exception as e:
        return f"Fehler beim Entfernen: {str(e)}", 500


@app.route("/get_records")
@login_required
def get_records():
    DataProvider = DatabaseOperations()
    user_id = session["user_id"]

    try:
        rows = DataProvider.getAusgabenFromMonthlyBudget(user_id)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    rev, exp, all_entries = [], [], []
    for row in rows:
        amount, description, flag = row
        entry = {"amount": amount, "description": description, "flag": flag}
        all_entries.append(entry)
        if flag == "REV":
            rev.append(entry)
        else:
            exp.append(entry)

    return jsonify({"rev": rev, "exp": exp, "all_entries": all_entries})


@app.route("/get_totals")
@login_required
def get_totals():
    DataProvider = DatabaseOperations()
    GeneralOps = GeneralOperations(DataProvider)
    user_id = session["user_id"]

    try:
        monthlyRevenue, monthlyExpense, monthlyBudget = GeneralOps.procCalculateMonthlyBudget(user_id)
        return jsonify({
            "monthlyRevenue": monthlyRevenue,
            "monthlyExpense": monthlyExpense,
            "monthlyBudget": monthlyBudget
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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

    DataProvider = DatabaseOperations()
    ops = GeneralOperations(DataProvider)

    try:
        monthlyBudget, monthlyExpense, monthlySaved, monthlyExpensePercentage = ops.expensePlannerSummaryHelpValues(month, year, user_id)
        return jsonify({
            "budget": monthlyBudget,
            "expenseSum": monthlyExpense,
            "saved": monthlySaved,
            "expensePercentage": monthlyExpensePercentage
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/expensePlanner/add", methods=["POST"])
@login_required
def add_expense():
    DataProvider = DatabaseOperations()
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
    DataProvider = DatabaseOperations()
    user_id = session["user_id"]
    value = request.form.get("entry")

    if not value:
        return "Kein Eintrag ausgewählt!", 400

    try:
        description, day, month, year = value.split("|")
        day, month, year = int(day), int(month), int(year)
        DataProvider.doDeleteFromExpensePlanner(description, day, month, year, user_id)
        return "Ausgabe erfolgreich entfernt!"
    except Exception as e:
        return f"Fehler beim Entfernen: {str(e)}", 500


@app.route("/expensePlanner/get", methods=["GET"])
@login_required
def get_expenses():
    DataProvider = DatabaseOperations()
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
                "description": r[1]
            }
            for r in rows
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================================================================
# STARTEN
# ================================================================
if __name__ == "__main__":
    app.run(debug=True)
