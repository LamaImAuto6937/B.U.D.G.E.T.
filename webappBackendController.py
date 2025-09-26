from flask import Flask, render_template, request, jsonify
from DatabaseOperationClass import DatabaseOperations
from generalOperationClass import GeneralOperations
from datetime import datetime

app = Flask(__name__)

# ----------------------------
# Index Route (Modulauswahl)
# ----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        module = request.form.get("module")

        match module:
            case "monthlyBudget":
                return render_template("monthlyBudget.html")
            case "expensePlanner":
                return render_template("expensePlanner.html")
            case _:
                return render_template("index.html", error="Unbekanntes Modul gewählt.")

    return render_template("index.html")

# ----------------------------
# Backend-Logik: Monthly Budget
# ----------------------------
@app.route("/add_entry", methods=["POST"])
def add_entry():
    DataProvider = DatabaseOperations()
    betrag = request.form.get("betrag")
    description = request.form.get("description")
    expense_flag = request.form.get("flag")

    if not betrag or not description or not expense_flag:
        return "FEHLER: Ungültige Eingabe!"

    DataProvider.doAppendToMonthlyBudget(float(betrag), description, expense_flag)
    return "Eintrag erfolgreich hinzugefügt!"

@app.route("/remove_entry", methods=["POST"])
def remove_entry():
    DataProvider = DatabaseOperations()
    value = request.form.get("entry")
    if not value:
        return "FEHLER: Kein Eintrag ausgewählt!"
    try:
        amount, description, flag = value.split("|")
        DataProvider.doDeleteFromMonthlyBudget(float(amount), description, flag)
        return "Eintrag erfolgreich entfernt!"
    except Exception as e:
        return f"Fehler beim Entfernen: {str(e)}"

@app.route("/get_records")
def get_records():
    DataProvider = DatabaseOperations()
    rows = DataProvider.getAusgabenFromMonthlyBudget()

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
def get_totals():
    DataProvider = DatabaseOperations()
    GeneralOps = GeneralOperations(DataProvider)
    monthlyRevenue, monthlyExpense, monthlyBudget = GeneralOps.procCalculateMonthlyBudget()
    return jsonify({
        "monthlyRevenue": monthlyRevenue,
        "monthlyExpense": monthlyExpense,
        "monthlyBudget": monthlyBudget
    })

# ----------------------------
# Backend-Logik: Expense Planner
# ----------------------------
@app.route("/expensePlanner/summary")
def get_expense_summary_values():
    month = int(request.args.get("month"))
    year = int(request.args.get("year"))

    DataProvider = DatabaseOperations()
    ops = GeneralOperations(DataProvider)
    monthlyBudget, monthlyExpense, monthlySaved, monthlyExpensePercentage = ops.expensePlannerSummaryHelpValues(month, year)

    return jsonify({
        "budget": monthlyBudget,
        "expenseSum": monthlyExpense,
        "saved": monthlySaved,
        "expensePercentage": monthlyExpensePercentage
    })

@app.route("/expensePlanner/add", methods=["POST"])
def add_expense():
    DataProvider = DatabaseOperations()
    amount = request.form.get("amount")
    description = request.form.get("description")
    day = int(request.form.get("day"))
    month = int(request.form.get("month"))
    year = int(request.form.get("year"))
    try:
        DataProvider.doAppendToExpensePlanner(day, month, year, amount, description)
        return "Expense hinzugefügt!"
    except Exception as e:
        return f"Fehler beim Hinzufügen: {str(e)}", 500

@app.route("/expensePlanner/remove", methods=["POST"])
def expense_remove():
    DataProvider = DatabaseOperations()
    value = request.form.get("entry")
    if not value:
        return "Kein Eintrag ausgewählt!", 400

    try:
        # Jetzt mit description im value
        description, day, month, year = value.split("|")
        day, month, year = int(day), int(month), int(year)
    except Exception:
        return "Ungültiges Format für Eintrag!", 400

    try:
        # Löschen eindeutig über description + day + month + year
        DataProvider.doDeleteFromExpensePlanner(description, day, month, year)
        return "Ausgabe erfolgreich entfernt!"
    except Exception as e:
        return f"Fehler beim Entfernen: {str(e)}", 500

@app.route("/expensePlanner/get", methods=["GET"])
def get_expenses():
    DataProvider = DatabaseOperations()
    try:
        month = int(request.args.get("month"))
        year = int(request.args.get("year"))
        rows = DataProvider.getAusgabenFromExpensePlanner(month, year)

        # rows = [(amount, description, day, month, year), ...]
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

# ----------------------------
# Starten
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)
