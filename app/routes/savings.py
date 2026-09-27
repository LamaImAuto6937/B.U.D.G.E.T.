from flask import Blueprint, render_template, request, jsonify, session
from app.decorators import login_required
from DatabaseOperationClasses import savingPlanDBOperations, expensePlannerDBOperations
from ModuleOperationClasses import SavingPlan, Helper
from datetime import datetime

savings_bp = Blueprint("savings", __name__)

# ================================================================
# SAVINGS PLAN
# ================================================================
@savings_bp.route("/savingsPlan")
@login_required
def savingsPlan():
    return render_template("savingsPlan.html")

@savings_bp.route("/api/savings/plans", methods=["GET"])
@login_required
def api_get_savings_plans():
    try:
        user_id = session["user_id"]
        db_ops = savingPlanDBOperations()
        plans_data = db_ops.getPlanDetails(user_id)
        if not plans_data:
            return jsonify({"success": True, "plans": []})

        HelperClass = Helper()
        saving_plan = SavingPlan(HelperClass, db_ops)
        plans = []
        for plan in plans_data:
            plans.append({"id": plan[0], "plan_name": plan[2], "description": plan[3], "target_amount": plan[4], "current_amount": saving_plan.procCalculateSavedAmount(plan[0]), "created_at": str(plan[5])})
        return jsonify({"success": True, "plans": plans})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@savings_bp.route("/api/savings/plan/<plan_id>", methods=["GET"])
@login_required
def api_get_savings_plan_details(plan_id):
    try:
        user_id = session["user_id"]
        db_ops = savingPlanDBOperations()
        plan = db_ops.getPlanById(plan_id, user_id)
        if not plan:
            return jsonify({"success": False, "error": "Plan nicht gefunden"}), 404

        saving_plan = SavingPlan(Helper(), db_ops)
        current_amount = saving_plan.procCalculateSavedAmount(plan_id)
        transactions_data = db_ops.getAccountingSummary(int(plan_id))
        transactions = sorted([{"id": tx[0], "plan_id": tx[1], "amount": float(tx[2]), "expense_flag": tx[3], "created_at": str(tx[4]), "description": tx[5]} for tx in transactions_data], key=lambda x: x["created_at"], reverse=True)
        return jsonify({"success": True, "plan": {"id": plan[0], "plan_name": plan[2], "description": plan[3], "target_amount": float(plan[4]), "current_amount": float(current_amount), "created_at": str(plan[5])}, "transactions": transactions})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@savings_bp.route("/api/savings/plan/<plan_id>", methods=["DELETE"])
@login_required
def api_delete_savings_plan(plan_id):
    try:
        user_id = session["user_id"]
        db_ops = savingPlanDBOperations()
        if not db_ops.getPlanById(plan_id, user_id):
            return jsonify({"success": False, "error": "Plan nicht gefunden"}), 404
        db_ops.doDeleteAllPlanEntriesFromAccounting(plan_id)
        db_ops.doDeletePlan(plan_id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@savings_bp.route("/api/savings/plan", methods=["POST"])
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
        try:
            target_amount = float(target_amount)
            if target_amount <= 0:
                return jsonify({"success": False, "error": "Zielbetrag muss größer als 0 sein"}), 400
        except ValueError:
            return jsonify({"success": False, "error": "Zielbetrag muss eine Zahl sein"}), 400
        Dataprovider.doCreateNewPlan(int(user_id), str(plan_name), str(description), float(target_amount))
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@savings_bp.route("/api/savings/transaction-from-expense", methods=["POST"])
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
        try:
            amount = float(amount)
            if amount <= 0:
                return jsonify({"success": False, "error": "Betrag muss größer als 0 sein"}), 400
        except ValueError:
            return jsonify({"success": False, "error": "Betrag muss eine Zahl sein"}), 400
        db_ops = savingPlanDBOperations()
        if not db_ops.getPlanById(plan_id, user_id):
            return jsonify({"success": False, "error": "Plan nicht gefunden"}), 404
        db_ops.doAppendToAccounting(plan_id, amount, 1, description)
        today = datetime.now()
        expensePlannerDBOperations().doAppendToExpensePlanner(day=today.day, month=today.month, year=today.year, betragAusgabe=amount, bezeichnungDerAusgabe=description if description else "Sparplan Transfer", user_id=user_id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@savings_bp.route("/api/savings/transaction", methods=["POST"])
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
        return jsonify({"success": False, "error": str(e)}), 500

@savings_bp.route("/api/savings/transaction/<transaction_id>", methods=["DELETE"])
@login_required
def api_delete_savings_transaction(transaction_id):
    try:
        savingPlanDBOperations().doDeleteFromAccounting(int(transaction_id))
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
