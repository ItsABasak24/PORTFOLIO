import os
from dotenv import load_dotenv

# Load env BEFORE importing modules that use env (defensive)
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, flash, session
from . import normal  # normal expects MONGO_URI / DB_NAME from env
from . import temp
app = Flask(__name__)

temp.admin_credentials()
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")  # ensure SECRET_KEY exists in .env

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- SUBMIT FORM ----------------
@app.route("/submit", methods=["POST"])
def submit():
    username = request.form.get("name")
    email = request.form.get("email")
    subject = request.form.get("subject")
    message = request.form.get("message")

    # Validation: require (name OR email) AND message
    if not (username or email) or not message:
        # show error and keep user on submit page
        return render_template("submit.html", error="Please provide a name or email AND a message",
                               username=username, email=email)

    # Build document and insert into MongoDB
    doc = {
        "name": username,
        "email": email,
        "subject": subject,
        "message": message
    }

    try:
        res = normal.my_information.insert_one(doc)
        inserted_id = str(res.inserted_id)
        print("Inserted document id:", inserted_id)
    except Exception as e:
        # If DB insert fails, show a helpful error
        print("DB insert error:", e)
        return render_template("submit.html", error="Failed to save your message. Try again later.",
                               username=username, email=email)

    # Show confirmation page (or you can redirect to a success page)
    return render_template("submit.html", username=username, email=email, success=True)


# ---------------- ADMIN LOGIN ----------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        ADMIN_USER = os.getenv("ADMIN_USER")
        ADMIN_PASS = os.getenv("ADMIN_PASS")

        # Defensive: if ADMIN_USER/ADMIN_PASS not set, fail with message
        if not ADMIN_USER or not ADMIN_PASS:
            flash("Admin credentials are not configured on the server.", "error")
            return redirect(url_for("admin_login"))

        if username == ADMIN_USER and password == ADMIN_PASS:
            session["admin_logged_in"] = True
            flash("Logged in successfully", "success")
            return redirect(url_for("admin"))
        else:
            flash("Invalid credentials", "error")
            return redirect(url_for("admin_login"))

    return render_template("admin.html")


# ---------------- ADMIN LOGOUT ----------------
@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    flash("Logged out", "info")
    return redirect(url_for("admin_login"))


# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin")
def admin():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    submissions = []
    try:
        for d in normal.my_information.find().sort("_id", -1):
            submissions.append(normal.fix_doc_ids(d))
    except Exception as e:
        print("DB read error:", e)
        flash("Unable to fetch submissions from the database.", "error")
        submissions = []

    return render_template("admin_dashboard.html", submissions=submissions)


if __name__ == "__main__":
    app.run(debug=True)
