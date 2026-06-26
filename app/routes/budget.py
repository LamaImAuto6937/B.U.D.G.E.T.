from flask import Blueprint, render_template, request, jsonify, session
from app.decorators import login_required
from DatabaseOperationClasses import monthlyBudgetDBOperations
from ModuleOperationClasses import monthlyBudget, Helper

budget_bp = Blueprint("budget", __name__)

# ================================================================
# MONTHLY BUDGET
# ================================================================
@budget_bp.route("/monthlyBudget")
@login_required
def monthly_budget():
    return render_template("monthlyBudget.html")

@budget_bp.route("/api/budget/monthly-totals")
@login_required
def api_monthly_totals():
    DataProvider = monthlyBudgetDBOperations()
    HelperClass = Helper()
    GeneralOps = monthlyBudget(HelperClass, DataProvider)
    user_id = session["user_id"]
    try:
        return jsonify({"monthlyRevenue": GeneralOps.procCalculateRevenue(user_id), "monthlyExpense": GeneralOps.procCalculateExpense(user_id)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@budget_bp.route("/api/budget/items")
@login_required
def api_budget_items():
    DataProvider = monthlyBudgetDBOperations()
    HelperOps = Helper()
    MonthlyBudgetOps = monthlyBudget(HelperOps, DataProvider)
    user_id = session["user_id"]
    try:
        revenue_items = HelperOps.convertNestedTupleIntoList(DataProvider.getRevenueData(user_id))
        for i in range(len(revenue_items)):
            revenue_items[i].append(MonthlyBudgetOps.procCalculateDebitRate(revenue_items[i][0], revenue_items[i][5]))
            revenue_items[i].append(MonthlyBudgetOps.procCalculateYearlyRate(revenue_items[i][0], revenue_items[i][5]))

        expense_items = HelperOps.convertNestedTupleIntoList(DataProvider.getExpenseData(user_id))
        for i in range(len(expense_items)):
            expense_items[i].append(MonthlyBudgetOps.procCalculateDebitRate(expense_items[i][0], expense_items[i][5]))
            expense_items[i].append(MonthlyBudgetOps.procCalculateYearlyRate(expense_items[i][0], expense_items[i][5]))

        return jsonify({"revenue": revenue_items, "expense": expense_items})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@budget_bp.route("/add_entry", methods=["POST"])
@login_required
def add_entry():
    DataProvider = monthlyBudgetDBOperations()
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

@budget_bp.route("/remove_entry", methods=["POST"])
@login_required
def remove_entry():
    DataProvider = monthlyBudgetDBOperations()
    monthlyBudgetID = request.form.get("monthlyBudgetID")
    if not monthlyBudgetID:
        return "FEHLER: Kein Eintrag ausgewählt!", 400
    try:
        DataProvider.doDeleteFromMonthlyBudget(monthlyBudgetID)
        return "Eintrag erfolgreich entfernt!"
    except Exception as e:
        return f"Fehler beim Entfernen: {str(e)}", 500

@budget_bp.route("/monthlyBudget/update_entry", methods=["POST"])
@login_required
def monthlyBudget_update_entry():
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
