from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from itsdangerous import URLSafeTimedSerializer
from DatabaseOperationClasses import userDBOperations
from ModuleOperationClasses import loginClass, Helper

auth_bp = Blueprint("auth", __name__)

# ================================================================
# LOGIN / LOGOUT
# ================================================================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        DataProvider = userDBOperations()
        HelperClass = Helper()
        from flask import current_app
        LoginClass = loginClass(DataProvider, HelperClass, current_app.secret_key)
        user_id, is_valid = LoginClass.procValidateLogin(username, password)

        if is_valid and user_id is not None:
            session["user_id"] = user_id
            session["username"] = username
            return redirect(url_for("dashboard.index"))
        else:
            return render_template("login.html", error="Ungültiger Benutzername oder Passwort.")

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

@auth_bp.route("/create_user", methods=["POST"])
def create_user():
    username = request.form.get("new_username")
    password = request.form.get("new_password")
    email = request.form.get("new_email")

    DataProvider = userDBOperations()
    HelperClass = Helper()
    from flask import current_app
    ops = loginClass(DataProvider, HelperClass, current_app.secret_key)

    try:
        success = ops.procCreateNewUser(username, password, email)
        token = ops.generate_verification_token(email)
        verify_url = url_for('auth.verify_email', token=token, _external=True)
        ops.sendVerficationEmail(email, verify_url)

        if success:
            return render_template("login.html", success="Eine Bestätigungsemail wurde an " + email + " gesendet.")
        else:
            return render_template("login.html", error="Benutzername existiert bereits.")
    except Exception as e:
        return render_template("login.html", error=f"Fehler beim Erstellen: {str(e)}")

# ================================================================
# RESET PASSWORD
# ================================================================
@auth_bp.route("/reset_password", methods=["POST"])
def reset_password():
    email = request.form.get("email")
    DataProvider = userDBOperations()
    helperObject = Helper()
    from flask import current_app
    loginObject = loginClass(DataProvider, helperObject, current_app.secret_key)

    try:
        found_user = DataProvider.getUserByUsernameOrEmail(email)
        if not found_user:
            return jsonify({"success": True, "message": "Wenn die E-Mail-Adresse mit einem Konto verknüpft ist, wird eine Reset-E-Mail gesendet."}), 200
        else:
            user_id = found_user[0]
            token = loginObject.generate_password_reset_token(user_id)
            loginObject.sentResetPasswordEmail(email, url_for("auth.confirm_reset_password", token=token, _external=True))
            return jsonify({"success": True, "message": "Wenn die E-Mail-Adresse mit einem Konto verknüpft ist, wird eine Reset-E-Mail gesendet."}), 200
    except Exception as e:
        print(e)
        return jsonify({"success": False, "message": "Fehler beim Verarbeiten der Anfrage."}), 500

@auth_bp.route("/reset_password/confirm/<token>", methods=["GET", "POST"])
def confirm_reset_password(token):
    DataProvider = userDBOperations()
    HelperClass = Helper()
    from flask import current_app
    loginObject = loginClass(DataProvider, HelperClass, current_app.secret_key)

    if request.method == "GET":
        user_id = loginObject.confirm_password_reset_token(token)
        if not user_id:
            return redirect(url_for("auth.login", error="Ungültiger oder abgelaufener Link."))
        return render_template("components/reset_password_confirm.html", token=token)

    if request.method == "POST":
        user_id = loginObject.confirm_password_reset_token(token)
        if not user_id:
            return jsonify({"error": "Ungültiger Link"})

        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if not new_password or not confirm_password:
            return jsonify({"error": "Prüfe deine Eingabe!"}), 400
        if new_password != confirm_password:
            return render_template("components/reset_password_confirm.html", token=token, error="Passwörter stimmen nicht überein!"), 400

        DataProvider.doUpdateCredentialsPassword(user_id, HelperClass.generateHash(new_password))
        return redirect(url_for("auth.login", success="Passwort erfolgreich geändert!"))

@auth_bp.route("/verfy_user/<token>")
def verify_email(token):
    DataProvider = userDBOperations()
    from flask import current_app
    ops = loginClass(DataProviderClass=DataProvider, Helper=Helper(), SECRET_KEY=current_app.secret_key)

    email = ops.confirm_verification_token(token)
    if not email:
        return redirect(url_for("auth.login", error="Ungültiger oder abgelaufener Verifizierungslink."))

    user_id = DataProvider.getUserByUsernameOrEmail(email)[0]
    validaten_state = DataProvider.getValidationStateFromUsers(user_id)[0]

    if validaten_state == 1:
        return redirect(url_for("auth.login", error="Konto bereits verifiziert."))
    elif validaten_state == 0:
        DataProvider.doUpdateValidationState(user_id, 1)
        return redirect(url_for("auth.login", success="Konto erfolgreich verifiziert!"))
    else:
        return redirect(url_for("auth.login", error="Ungültiger Verifizierungsstatus."))
