from flask import *
app = Flask(__name__)

# Beispiel-Datenbank (in echt würdest du hier z. B. SQLite nutzen)
entries = []

@app.route("/add", methods=["POST"])
def add_entry():
    data = request.json  # erwartet JSON
    entries.append(data)
    return jsonify({"status": "ok"})

@app.route("/list", methods=["GET"])
def list_entries():
    return jsonify(entries)

if __name__ == "__main__":
    app.run(debug=True)
