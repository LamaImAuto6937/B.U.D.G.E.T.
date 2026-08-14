from flask import Blueprint, render_template, request, jsonify, session
from app.decorators import login_required
from DatabaseOperationClasses import userDBOperations, expensePlannerDBOperations, settingsDBOperations
from ModuleOperationClasses import Helper
from datetime import datetime

settings_bp = Blueprint("settings", __name__)

# ================================================================
# SETTINGS
# ================================================================
@settings_bp.route("/settings")
@login_required
def settings():
    return render_template("settings.html")

@settings_bp.route("/settings/user_info", methods=["GET"])
@login_required
def api_user_info():
    user_id = session["user_id"]
    Dataprovider = userDBOperations()
    try:
        user = Dataprovider.getUserByUserId(user_id)
        if user:
            return jsonify({"success": True, "username": user[0], "email": user[1]})
        return jsonify({"success": False, "error": "User nicht gefunden"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@settings_bp.route("/settings/resetBudgetForCurrentMonth", methods=["GET"])
@login_required
def resetBudget():
    user_id = session["user_id"]
    Dataprovider = expensePlannerDBOperations()
    today = datetime.now()
    try:
        Dataprovider.doDeleteFromSetBudgetForSelectedMonth(user_id, today.month, today.year)
    except Exception as e:
        print(str(e))

@settings_bp.route("/settings/deleteAccount", methods=["GET"])
@login_required
def deleteAccount():
    user_id = session["user_id"]
    Dataprovider = userDBOperations()
    try:
        session.clear()
        Dataprovider.doDeleteFromUsers(user_id)
        return (f"Konto [{user_id}] erfolgreich gelöscht", 200)
    except Exception as e:
        return ("Fehler beim Löschen", 500)

@settings_bp.route("/settings/updateCredentials/username", methods=["POST"])
@login_required
def updateCredentialsUsername():
    user_id = session["user_id"]
    Dataprovider = userDBOperations()
    try:
        Dataprovider.doUpdateCredentialsUsername(user_id, request.form.get("new_username"))
        return (f"Konto [{user_id}] erfolgreich aktualisiert", 200)
    except Exception as e:
        return ("Fehler beim Aktualisieren", 500)

@settings_bp.route("/settings/updateCredentials/password", methods=["POST"])
@login_required
def updateCredentialsPassword():
    user_id = session["user_id"]
    Dataprovider = userDBOperations()
    helper = Helper()
    try:
        Dataprovider.doUpdateCredentialsPassword(user_id, helper.generateHash(request.form.get("new_password")))
        return (f"Konto [{user_id}] erfolgreich aktualisiert", 200)
    except Exception as e:
        return ("Fehler beim Aktualisieren", 500)

@settings_bp.route("/settings/updateCredentials/email", methods=["POST"])
@login_required
def updateCredentialsEmail():
    user_id = session["user_id"]
    Dataprovider = userDBOperations()
    try:
        Dataprovider.doUpdateCredentialsEmail(user_id, request.form.get("new_email"))
        return (f"Konto [{user_id}] erfolgreich aktualisiert", 200)
    except Exception as e:
        return ("Fehler beim Aktualisieren", 500)

@settings_bp.route("/settings/categories", methods=["GET"])
@login_required
def get_categories():
    user_id = session["user_id"]
    Dataprovider = settingsDBOperations()
    try:
        categories = Dataprovider.getCategoriesForUserId(user_id)
        return jsonify({"success": True, "categories": categories})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
@settings_bp.route("/settings/categories/create", methods=["POST"])
@login_required
def create_categorie():
    user_id = session["user_id"]
    Dataprovider = settingsDBOperations()
    name = str(request.form.get("name"))
    color = request.form.get("color")
    
    if len(name) > 24 or len(name) < 1 or name == None:
        return jsonify({"success": False, "error": "Name muss zwischen 1 und 24 Zeichen liegen"}), 400
    
    for existing_categorie in Dataprovider.getCategoriesForUserId(user_id):
        if name.lower() == existing_categorie["name"].lower():
            return jsonify({"success": False, "error": "Kategorie existiert bereits!"}), 400
    
    try:
        Dataprovider.createNewCategorieForUserId(user_id=user_id, categorie_color=color, categorie_name=name)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@settings_bp.route("/settings/categories/<id>/update", methods=["POST"])
@login_required
def update_categorie(id):
    
    try:
        Dataprovider = settingsDBOperations()
        name = request.form.get("name")
        color = request.form.get("color")
        user_id = session["user_id"]

        if len(name) > 24 or len(name) < 1 or name == None:
            return jsonify({"success": False, "error": "Name muss zwischen 1 und 24 Zeichen liegen"}), 400
        
        for existing_categorie in Dataprovider.getCategoriesForUserId(int(user_id)):
            if name.lower() == existing_categorie["name"].lower():
                return jsonify({"success": False, "error": "Kategorie existiert bereits!"}), 400

        Dataprovider.updateCategorieEntry(categorie_color=str(color), categorie_name=str(name), categorie_id=int(id))
        return jsonify( { "success": True }), 200
        
    except Exception as e:
        return jsonify({ "success": False, "error": str(e) }), 500
    
    
@settings_bp.route("/settings/categories/<id>/delete", methods=["POST"])
@login_required
def delete_categorie(id):
    Dataprovider = settingsDBOperations()
    
    try:
        Dataprovider.deleteFromCategories(int(id))
        return jsonify({"success": True})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500