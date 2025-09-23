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
@app.route("/expensePlanner/add", methods=["POST"])
def expense_add():
    DataProvider = DatabaseOperations()

    try:
        day = int(request.form.get("day"))
        month = int(request.form.get("month"))
        year = int(request.form.get("year"))
        amount = float(request.form.get("amount"))
        description = request.form.get("description")

        if not description:
            return "FEHLER: Beschreibung fehlt!"

        DataProvider.doAppendToExpensePlanner(day, month, year, amount, description)
        return "Ausgabe erfolgreich hinzugefügt!"
    except Exception as e:
        return f"Fehler: {str(e)}"

@app.route("/expensePlanner/get")
def expense_get():
    DataProvider = DatabaseOperations()
    month = int(request.args.get("month"))
    year = int(request.args.get("year"))

    rows = DataProvider.getAusgabenFromExpensePlanner(month, year)  # musst du implementieren
    entries = []
    for row in rows:
        day, month, year, amount, description = row
        entries.append({
            "day": day,
            "month": month,
            "year": year,
            "amount": amount,
            "description": description
        })
    return jsonify(entries)

@app.route("/expensePlanner/remove", methods=["POST"])
def expense_remove():
    DataProvider = DatabaseOperations()
    value = request.form.get("entry")
    try:
        day, month, year = map(int, value.split("|"))
        DataProvider.doDeleteFromExpensePlanner(day, month, year)
        return "Ausgabe erfolgreich entfernt!"
    except Exception as e:
        return f"Fehler beim Entfernen: {str(e)}"

# ----------------------------
# Starten
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)
