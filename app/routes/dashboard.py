import os
import json
from flask import Blueprint, render_template, current_app
from app.decorators import login_required

dashboard_bp = Blueprint("dashboard", __name__)


def _load_changelog():
    """Lädt changelog.json. Gibt None zurück, wenn Datei fehlt oder ungültig ist."""
    changelog_path = os.path.join(current_app.static_folder, "changelog.json")
    try:
        with open(changelog_path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _get_version(data):
    if not data:
        return None
    releases = data.get("releases", [])
    if not releases:
        return None
    return releases[0].get("version")


# ================================================================
# Index / Modul-Auswahl
# ================================================================
@dashboard_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    data = _load_changelog()
    return render_template("index.html", version=_get_version(data))


# ================================================================
# Dokumentation / Changelog
# ================================================================
@dashboard_bp.route("/changelog", methods=["GET"])
@login_required
def changelog():
    data = _load_changelog()
    return render_template(
        "changelog.html",
        version=_get_version(data),
        releases=(data or {}).get("releases", []),
    )
