from flask import Flask, render_template, request, jsonify
from DatabaseOperationClass import DatabaseOperations
from generalOperationClass import GeneralOperations

app = Flask(__name__)

# Globale DB-Instanzen
DataProvider = DatabaseOperations()
GeneralOps = GeneralOperations(DataProvider)

@app.route("/")
def index():
    return render_template("monthlyBudget.html")

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

if __name__ == "__main__":
    app.run(debug=True)
