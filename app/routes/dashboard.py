from flask import Blueprint, render_template
from app.decorators import login_required

dashboard_bp = Blueprint("dashboard", __name__)

# ================================================================
# Index / Modul-Auswahl
# ================================================================
@dashboard_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    return render_template("index.html")
