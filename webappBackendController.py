from flask import Flask, render_template, request, jsonify
from DatabaseOperationClass import DatabaseOperations
from generalOperationClass import GeneralOperations
from datetime import datetime

app = Flask(__name__)

# ----------------------------
# Fake-Daten (Demo-Zwecke)
# ----------------------------


# ----------------------------
# Index Route (Modulauswahl)
# ----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        module = request.form.get("module")

        # ----------------------------
        # Hier steuerst du, welches Modul gerendert wird
        # Füge für neue Module einfach ein case hinzu
        # ----------------------------
        match module:
            case "monthlyBudget":
                return render_template("monthlyBudget.html")
            case "expensePlanner":
                return render_template("expensePlanner.html")
            case _:
                return render_template("index.html", error="Unbekanntes Modul gewählt.")

    # GET → einfach Auswahlseite anzeigen
    return render_template("index.html")

# ----------------------------
# Backend-Logik: Monthly Budget
# ----------------------------
@app.route("/add_entry", methods=["POST"])
def add_entry():
    DataDataProvider = DatabaseOperations()
    betrag = request.form.get("betrag")
    description = request.form.get("description")
    expense_flag = request.form.get("flag")

    if not betrag or not description or not expense_flag:
        return "FEHLER: Ungültige Eingabe!"

    DataDataProvider.doAppendToMonthlyBudget(float(betrag), description, expense_flag)
    return "Eintrag erfolgreich hinzugefügt!"

@app.route("/remove_entry", methods=["POST"])
def remove_entry():
    DataDataProvider = DatabaseOperations()
    value = request.form.get("entry")
    if not value:
        return "FEHLER: Kein Eintrag ausgewählt!"
    try:
        amount, description, flag = value.split("|")
        DataDataProvider.doDeleteFromMonthlyBudget(float(amount), description, flag)
        return "Eintrag erfolgreich entfernt!"
    except Exception as e:
        return f"Fehler beim Entfernen: {str(e)}"

@app.route("/get_records")
def get_records():
    DataDataProvider = DatabaseOperations()
    rows = DataDataProvider.getAusgabenFromMonthlyBudget()

    # Split nach Einnahmen/Ausgaben
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
    DataDataProvider = DatabaseOperations()
    GeneralOps = GeneralOperations(DataDataProvider)
    monthlyRevenue, monthlyExpense, monthlyBudget = GeneralOps.procCalculateMonthlyBudget()
    return jsonify({
        "monthlyRevenue": monthlyRevenue,
        "monthlyExpense": monthlyExpense,
        "monthlyBudget": monthlyBudget
    })

# ----------------------------
# Backend-Logik: Expense Planner
# ----------------------------
# Monthly Expense Summary
@app.route("/expensePlanner/summary")
def get_expense_summary_values():
    month = int(request.args.get("month"))
    year = int(request.args.get("year"))

    # Werte aus GeneralOperations holen
    from generalOperationClass import GeneralOperations
    DataProvider = DatabaseOperations()
    ops = GeneralOperations(DataProvider)
    monthlyBudget, monthlyExpense, monthlySaved, monthlyExpensePercentage = ops.expensePlannerSummaryHelpValues(month, year)

    return jsonify({
        "budget": monthlyBudget,
        "expenseSum": monthlyExpense,
        "saved": monthlySaved,
        "expensePercentage": monthlyExpensePercentage
    })
# Add Expense
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


# Remove Expense
@app.route("/expensePlanner/remove", methods=["POST"])
def expense_remove():
    DataProvider = DatabaseOperations()
    value = request.form.get("entry")
    if not value:
        return "Kein Eintrag ausgewählt!", 400

    try:
        # frontend liefert "day|month|year"
        day, month, year = map(int, value.split("|"))
    except Exception:
        return "Ungültiges Format für Eintrag!", 400

    try:
        # rows kommt direkt aus deiner DataProvider-Methode und ist sehr wahrscheinlich eine Liste von Tupeln:
        # z.B. (amount, description, day, month, year)
        rows = DataProvider.getAusgabenFromExpensePlanner(month, year)

        # Suche passendes Entry (unterstützt Tupel oder Dicts)
        found_description = None
        for r in rows:
            if isinstance(r, dict):
                # falls Provider bereits Dicts liefert
                try:
                    r_day = int(r.get("day", r.get("Day", 0)))
                    r_month = int(r.get("month", r.get("Month", 0)))
                    r_year = int(r.get("year", r.get("Year", 0)))
                    r_desc = r.get("description") or r.get("Description")
                except Exception:
                    continue
            else:
                # Tupel-Fall: (amount, description, day, month, year)
                # passe die Indizes an, falls deine Tupel anders aufgebaut sind
                try:
                    r_day = int(r[2])
                    r_month = int(r[3])
                    r_year = int(r[4])
                    r_desc = r[1]
                except Exception:
                    # Tupel hat anderes Format -> überspringen
                    continue

            if r_day == day and r_month == month and r_year == year:
                found_description = r_desc
                break

        if not found_description:
            return "Eintrag nicht gefunden!", 404

        # DataProvider erwartet (description, day, month, year) laut deiner Angabe
        DataProvider.doDeleteFromExpensePlanner(found_description, day, month, year)
        return "Ausgabe erfolgreich entfernt!"
    except Exception as e:
        return f"Fehler beim Entfernen: {str(e)}", 500


# Get Expenses (für Remove-Dropdown und Summary-Tabelle)
@app.route("/expensePlanner/get", methods=["GET"])
def get_expenses():
    DataProvider = DatabaseOperations()
    try:
        month = int(request.args.get("month"))
        year = int(request.args.get("year"))
        rows = DataProvider.getAusgabenFromExpensePlanner(month, year)

        # rows = [(amount, description, day, month, year), ...]
        # (10.0, 'test', 19, 8, 2025)
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
