from flask import Blueprint, render_template, request, jsonify, session
from app.decorators import login_required
from DatabaseOperationClasses import expensePlannerDBOperations, monthlyBudgetDBOperations
from ModuleOperationClasses import expensePlanner, monthlyBudget, Helper

expense_bp = Blueprint("expense", __name__)

# ================================================================
# EXPENSE PLANNER
# ================================================================
@expense_bp.route("/expensePlanner")
@login_required
def expense_planner():
    return render_template("expensePlanner.html")

@expense_bp.route("/expensePlanner/summary")
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
        return jsonify({"budget": Budget, "expenseSum": Expense, "saved": Saved, "expensePercentage": ExpensePercentage, "needsBudget": not budgetFound, "globalBudget": Budget})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@expense_bp.route("/expensePlanner/add", methods=["POST"])
@login_required
def add_expense():
    DataProvider = expensePlannerDBOperations()
    user_id = session["user_id"]
    try:
        DataProvider.doAppendToExpensePlanner(int(request.form.get("day")), int(request.form.get("month")), int(request.form.get("year")), float(request.form.get("amount")), request.form.get("description"), user_id)
        return "Expense hinzugefügt!"
    except Exception as e:
        return f"Fehler beim Hinzufügen: {str(e)}", 500

@expense_bp.route("/expensePlanner/remove", methods=["POST"])
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

@expense_bp.route("/expensePlanner/update", methods=["POST"])
@login_required
def update_entry():
    DataProvider = expensePlannerDBOperations()
    try:
        DataProvider.doUpdateExpensePlannerEntry(float(request.form.get("amount")), str(request.form.get("description")), int(request.form.get("day")), int(request.form.get("month")), int(request.form.get("year")), int(request.form.get("entry_id")))
        return "Eintrag aktualisiert!"
    except Exception as e:
        return f"Fehler beim Aktualisieren: {str(e)}", 500

@expense_bp.route("/expensePlanner/get", methods=["GET"])
@login_required
def get_expenses():
    DataProvider = expensePlannerDBOperations()
    user_id = session["user_id"]
    try:
        month = int(request.args.get("month"))
        year = int(request.args.get("year"))
        rows = DataProvider.getAusgabenFromExpensePlanner(month, year, user_id)
        return jsonify([{"day": int(r[2]), "month": int(r[3]), "year": int(r[4]), "amount": float(r[0]), "description": r[1], "id": r[6]} for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@expense_bp.route("/expensePlanner/setBudget", methods=["POST"])
@login_required
def expensePlanner_setBudget():
    DataProvider = expensePlannerDBOperations()
    user_id = session["user_id"]
    try:
        DataProvider.doAppendToSetBudgetForSelectedMonth(user_id, float(request.form.get("amount")), int(request.form.get("month")), int(request.form.get("year")))
        return "Budget gespeichert!"
    except Exception as e:
        return f"Fehler beim Speichern: {str(e)}", 500
