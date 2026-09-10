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
        Expense, Saved, ExpensePercentage = 0, 0, 0

        if budgetFound: 
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
        category_id = request.form.get("category_id") or None
        tags = request.form.getlist("tags[]")
        print(tags)
        DataProvider.doAppendToExpensePlanner(
            day=int(request.form.get("day")),
            month=int(request.form.get("month")),
            year=int(request.form.get("year")),
            betragAusgabe=float(request.form.get("amount")),
            bezeichnungDerAusgabe=request.form.get("description"),
            user_id=user_id,
            category_id=category_id,
            tags=tags,
        )
        return "Expense hinzugefügt!"
    except Exception as e:
        return f"Fehler beim Hinzufügen: {str(e)}", 500

@expense_bp.route("/expensePlanner/remove", methods=["POST"])
@login_required
def expense_remove():
    DataProvider = expensePlannerDBOperations()
    try:
        entry_id = request.form.get("entryid") or request.form.get("entry_id")
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
        category_id = request.form.get("category_id") or None
        entry_id = request.form.get("entryid") or request.form.get("entry_id")
        tags =  request.form.getlist("tags[]")

        DataProvider.doUpdateExpensePlannerEntry(
            betragAusgabe=float(request.form.get("amount")),
            bezeichnungAusgabe=str(request.form.get("description")),
            day=int(request.form.get("day")),
            monat=int(request.form.get("month")),
            jahr=int(request.form.get("year")),
            entry_id=int(entry_id),
            category_id=category_id,
            tags=tags,
            user_id = session["user_id"]
        )
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

        result = []
        for r in rows:
            row_id, amount, description, day, _, _, _, category_id = r
            category = None
            if category_id:
                category = DataProvider.getCategoryById(category_id)
            if row_id:
                tags = DataProvider.getTagByExpenseId(expense_id=int(row_id))
            result.append({
                "id": row_id,
                "day": int(day if day is not None else 1),
                "month": int(month),
                "year": int(year),
                "amount": float(amount),
                "description": description,
                "category": category,
                "tags": tags,
            })
        return jsonify(result)
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

@expense_bp.route("/expensePlanner/tags/suggest", methods=["GET"])
@login_required
def expensePlanner_suggestTags():
    try:
        Dataprovider = expensePlannerDBOperations()
        tagQuery = request.args.get("q") # Holt sich den Suchbegriff aus der Anfrage
        user_id = session["user_id"]

        suggestions = Dataprovider.getTags(int(user_id), str(tagQuery))

        if not suggestions:
            return jsonify({"success": False}), 404

        return jsonify({"success": True, "suggestions": suggestions}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
    
    
