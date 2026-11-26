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
        user_id = session["user_id"]
        
        if not entry_id or not user_id:
            return "Kein gültiger Eintrag ausgewählt!", 400
        DataProvider.doDeleteFromExpensePlanner(int(entry_id), int(user_id))
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
        user_id = session["user_id"]

        DataProvider.doUpdateExpensePlannerEntry(
            betragAusgabe=float(request.form.get("amount")),
            bezeichnungAusgabe=str(request.form.get("description")),
            day=int(request.form.get("day")),
            monat=int(request.form.get("month")),
            jahr=int(request.form.get("year")),
            entry_id=int(entry_id),
            category_id=category_id,
            tags=tags,
            user_id = user_id
        )
        return "Eintrag aktualisiert!"
    except Exception as e:
        return f"Fehler beim Aktualisieren: {str(e)}", 500

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
    
@expense_bp.route("/expensePlanner/entries/overview", methods=["GET"])
@login_required
def expensePlanner_filter_overview():
    """
    Gibt Monatseinträge für die Jahresübersicht des Filter Features
    des ExpensePlanners aus
    Welche Monate es gibt, Ausgaben pro Monat, Tage mit Einträgen
    """

    user_id = session["user_id"]
    Dataprovider = expensePlannerDBOperations()

    try:
        months = []
        availableMonths = Dataprovider.getSetBudgets(user_id)
        
        for entry in availableMonths:
            expenses = Dataprovider.getAusgabenFromExpensePlanner(entry["month"], entry["year"], user_id)

            if not expenses:
                continue

            days = sorted(set([row[3] for row in expenses]))
            entryCount = len(expenses)
            expenseSum = round(sum(expense[1] for expense in expenses if expense[1] > 0),2)

            months.append({
                "year": entry["year"],
                "month": entry["month"],
                "entryCount": entryCount,
                "expenseSum": expenseSum,
                "days": days
            })

        if not months:
            return jsonify({"success": False}), 404
        
        return jsonify({"months": months, "success": True}), 200

    except LookupError:
        return jsonify({"error": "Kein Eintrag gefunden!"}), 404

    except:
        return jsonify({"error": "Internal Server Error"}), 500

@expense_bp.route("/expensePlanner/entries/search", methods=["GET"])
@login_required
def expensePlanner_filter_search():
    """
    Gibt gefilterte Einträge plus Summen und Zählungen für die Filter Sidebar
    aus (Kategorien, Tags, Betrags-Histogramm)
    """

    def facetsBuildCategories(filteredEntries:list):
        """Baut eine Liste mit einem Dict pro gefundene Kategorie an und rechnet die Summe in dieser Kategorie zusammen!
        returns: [{"id": category_id, "expenseSum": amount},...]"""
        knownCategories = []
        result = []
        for entry in filteredEntries:
            if entry["category_id"] not in knownCategories:
                # Anlegen der Kategorie wenn noch nicht bekannt
                knownCategories.append(entry["category_id"])
                result.append({"id": entry["category_id"], "expenseSum": entry["amount"]})
            else:
                # Kategorie bekannt und somit bereits angelegt!
                for i in range(len(result)):
                    if result[i]["id"] == entry["category_id"]:
                        result[i]["expenseSum"] += entry["amount"]
                        break

        return result
    def facetsBuildTags(filteredEntries:list):
        """Baut eine Liste mit einem Dict pro gefundenen Tag mit jeweiligem Wert, wie oft dieser Tag vorkommt
        returns: [{"name": tag_name, "count": tag_count},...]"""
        knownTags = []
        result = []

        # tag_name enthält immer eine Liste!
        for entry in filteredEntries:
            for tag in entry["tag_name"]:       
                if tag not in knownTags:
                    knownTags.append(tag)
                    result.append({"name": tag, "count": 1})
                else:
                    for i in range(len(result)):
                        if result[i]["name"] == tag:
                            result[i]["count"] += 1

        return result
    def facetsBuildHistogram(entries) -> list[int]:
        buckets = [0] * 20
        for entry in entries:
            buckets[min(19, int(abs(entry["amount"]) // 10))] += 1
        
        return buckets
    
    try:

        textSearch = request.args.get("q", type=str)
        expenseType = request.args.get("type", type=str) # expense | income
        categories = request.args.getlist("category")
        tags = request.args.getlist("tag")
        tagMode = request.args.get("tagMode", type=str) # any | strict
        noTags = request.args.get("noTags", type=int) # 0 | 1
        amountMin = request.args.get("amountMin", type=float)
        amountMax = request.args.get("amountMax", type=float)
        period = request.args.getlist("period")
        dayFrom = request.args.get("dayFrom", type=int)
        dayTo = request.args.get("dayTo", type=int)
        sort = request.args.get("sort", type=str)

        entries = []
        user_id = session["user_id"]
        Dataprovider = expensePlannerDBOperations()

        foundEntries = Dataprovider.getFilteredExpenseEntries(
                                               user_id=user_id,
                                               search_term=textSearch,
                                               dayFrom=dayFrom,
                                               dayTo=dayTo,
                                               amountMin=amountMin,
                                               amountMax=amountMax,
                                               categories=categories,
                                               expenseType=expenseType,
                                               period=period,
                                               sort=sort,
                                               tags=tags,
                                               tagMode=tagMode,
                                               noTags=noTags
                                               )

        for entry in foundEntries:

            entries.append(
                {
                    "id": entry["expense_id"],
                    "day": entry["day"],
                    "month": entry["month"],
                    "year": entry["year"],
                    "amount": entry["amount"],
                    "description": entry["description"],
                    "category": { "id": entry["category_id"],
                                  "name": entry["category_name"],
                                  "color": entry["category_color"]},
                    "tags": entry["tag_name"]
                }
            )

        return jsonify({"entries": entries,
                        "facets": {
                            "categories": facetsBuildCategories(filteredEntries=foundEntries),
                            "tags": facetsBuildTags(filteredEntries=foundEntries),
                            "amountHistogram": facetsBuildHistogram(Dataprovider.getFilteredExpenseEntries(
                                               user_id=user_id,
                                               search_term=textSearch,
                                               dayFrom=dayFrom,
                                               dayTo=dayTo,
                                               categories=categories,
                                               expenseType=expenseType,
                                               period=period,
                                               sort=sort,
                                               tags=tags,
                                               tagMode=tagMode,
                                               noTags=noTags
                                               ))
                        }
                        }), 200
    except Exception as e:
        return jsonify({"error": str(e) }), 500
