# Main flask application for the ServiceFinder project

import os
import sys
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import joblib

from database import get_db
import html_helpers as hh

sys.path.append(os.path.join(os.path.dirname(__file__), "models"))
from text_utils import clean_text

app = Flask(__name__)
app.secret_key = "servicefinder_secret_key_123"

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
category_model = joblib.load(os.path.join(MODELS_DIR, "category_model.pkl"))
cost_model = joblib.load(os.path.join(MODELS_DIR, "cost_model.pkl"))

REGIONS = ["Kozhikode", "Kochi", "Thiruvananthapuram", "Kannur"]


def render(template_name, **context):
    context["navbar"] = hh.build_navbar()
    context["flash_html"] = hh.build_flash()
    return render_template(template_name, **context)


def login_required(role=None):
    def decorator(f):
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                flash("Please login first.")
                return redirect(url_for("login"))
            if role is not None and session.get("role") != role:
                flash("You are not allowed to view that page.")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        wrapped.__name__ = f.__name__
        return wrapped
    return decorator


def get_avg_rating(provider_id, db):
    row = db.execute(
        "SELECT AVG(rating) as avg_rating, COUNT(*) as total FROM reviews WHERE provider_id = ?",
        (provider_id,)
    ).fetchone()
    if row["total"] == 0:
        return None, 0
    return round(row["avg_rating"], 1), row["total"]


@app.route("/")
def index():
    return render("index.html", index_section=hh.build_index_section())


@app.route("/signup", methods=["GET", "POST"])
def signup():
    db = get_db()
    services = db.execute("SELECT * FROM services").fetchall()

    if request.method == "POST":
        role = request.form["role"]
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        phone = request.form["phone"]
        region = request.form["region"]
        hashed_pw = generate_password_hash(password)

        if role == "provider":
            service_category = request.form["service_category"]
            experience = request.form["experience"]
            bio = request.form["bio"]

            existing = db.execute("SELECT * FROM providers WHERE email = ?", (email,)).fetchone()
            if existing:
                flash("An account with this email already exists.")
                db.close()
                return redirect(url_for("signup"))

            db.execute("""
                INSERT INTO providers (name, email, password, phone, region, service_category, experience, bio, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
            """, (name, email, hashed_pw, phone, region, service_category, experience, bio))
            db.commit()
            db.close()
            flash("Signup successful! Please wait for admin approval before logging in.")
            return redirect(url_for("login"))

        else:
            existing = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            if existing:
                flash("An account with this email already exists.")
                db.close()
                return redirect(url_for("signup"))

            db.execute(
                "INSERT INTO users (name, email, password, phone, region) VALUES (?, ?, ?, ?, ?)",
                (name, email, hashed_pw, phone, region)
            )
            db.commit()
            db.close()
            flash("Signup successful! Please login.")
            return redirect(url_for("login"))

    services_options = hh.build_service_options(services)
    region_options = hh.build_region_options(REGIONS)
    db.close()
    return render("signup.html", services_options=services_options, region_options=region_options)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form["role"]
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()

        if role == "user":
            account = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        elif role == "provider":
            account = db.execute("SELECT * FROM providers WHERE email = ?", (email,)).fetchone()
        else:
            account = db.execute("SELECT * FROM admin WHERE email = ?", (email,)).fetchone()

        db.close()

        if account is None or not check_password_hash(account["password"], password):
            flash("Invalid email or password.")
            return redirect(url_for("login"))

        if role == "provider" and account["status"] != "Approved":
            flash("Your provider account is still " + account["status"] + " by the admin.")
            return redirect(url_for("login"))

        session["user_id"] = account["id"]
        session["role"] = role
        session["name"] = account["name"] if role != "admin" else "Admin"

        if role == "user":
            return redirect(url_for("user_dashboard"))
        elif role == "provider":
            return redirect(url_for("provider_dashboard"))
        else:
            return redirect(url_for("admin_dashboard"))

    return render("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/user/dashboard")
@login_required(role="user")
def user_dashboard():
    return render("user_dashboard.html", user_name=session.get("name"))


@app.route("/search", methods=["GET", "POST"])
@login_required(role="user")
def search():
    db = get_db()
    services = db.execute("SELECT * FROM services").fetchall()
    db.close()

    if request.method == "POST":
        service = request.form["service"]
        region = request.form["region"]
        return redirect(url_for("providers_list", service=service, region=region))

    services_options = hh.build_service_options(services)
    region_options = hh.build_region_options(REGIONS)
    return render("search.html", services_options=services_options, region_options=region_options)


@app.route("/providers")
@login_required(role="user")
def providers_list():
    service = request.args.get("service", "")
    region = request.args.get("region", "")

    db = get_db()
    query = "SELECT * FROM providers WHERE status = 'Approved'"
    params = []
    if service:
        query += " AND service_category = ?"
        params.append(service)
    if region:
        query += " AND region = ?"
        params.append(region)

    providers = db.execute(query, params).fetchall()

    provider_list = []
    for p in providers:
        avg_rating, total_reviews = get_avg_rating(p["id"], db)
        provider_list.append({
            "id": p["id"], "name": p["name"], "region": p["region"],
            "service_category": p["service_category"], "experience": p["experience"],
            "bio": p["bio"], "avg_rating": avg_rating, "total_reviews": total_reviews
        })

    db.close()
    providers_html = hh.build_provider_cards(provider_list)
    return render("providers_list.html", providers_html=providers_html, service=service, region=region)


@app.route("/provider/<int:provider_id>")
@login_required(role="user")
def provider_details(provider_id):
    db = get_db()
    provider = db.execute("SELECT * FROM providers WHERE id = ?", (provider_id,)).fetchone()

    if provider is None:
        db.close()
        flash("Provider not found.")
        return redirect(url_for("search"))

    avg_rating, total_reviews = get_avg_rating(provider_id, db)
    reviews = db.execute("""
        SELECT reviews.*, users.name as user_name FROM reviews
        JOIN users ON reviews.user_id = users.id
        WHERE reviews.provider_id = ? ORDER BY reviews.created_at DESC
    """, (provider_id,)).fetchall()
    db.close()

    if avg_rating:
        rating_html = "<p><b>Rating:</b> " + str(avg_rating) + " / 5 (" + str(total_reviews) + " reviews)</p>"
    else:
        rating_html = '<p class="small-text">This provider has no reviews yet.</p>'

    return render(
        "provider_details.html",
        provider_id=provider["id"],
        provider_name=provider["name"],
        provider_service=provider["service_category"],
        provider_region=provider["region"],
        provider_experience=provider["experience"],
        provider_phone=provider["phone"],
        provider_bio=provider["bio"],
        rating_html=rating_html,
        reviews_html=hh.build_reviews_html(reviews)
    )


@app.route("/book/<int:provider_id>", methods=["GET", "POST"])
@login_required(role="user")
def book_service(provider_id):
    db = get_db()
    provider = db.execute("SELECT * FROM providers WHERE id = ?", (provider_id,)).fetchone()

    if request.method == "POST":
        description = request.form["description"]
        booking_date = request.form["booking_date"]
        booking_time = request.form["booking_time"]

        db.execute("""
            INSERT INTO bookings (user_id, provider_id, service_name, description, booking_date, booking_time, status)
            VALUES (?, ?, ?, ?, ?, ?, 'Pending')
        """, (session["user_id"], provider_id, provider["service_category"], description, booking_date, booking_time))
        db.commit()
        db.close()
        flash("Service request sent! You can track it from My Bookings.")
        return redirect(url_for("my_bookings"))

    db.close()
    return render("book_service.html", provider_id=provider_id, provider_name=provider["name"])


@app.route("/my_bookings")
@login_required(role="user")
def my_bookings():
    db = get_db()
    bookings = db.execute("""
        SELECT bookings.*, providers.name as provider_name FROM bookings
        JOIN providers ON bookings.provider_id = providers.id
        WHERE bookings.user_id = ?
        ORDER BY bookings.created_at DESC
    """, (session["user_id"],)).fetchall()

    reviewed_ids = set()
    reviewed_rows = db.execute("SELECT booking_id FROM reviews WHERE user_id = ?", (session["user_id"],)).fetchall()
    for r in reviewed_rows:
        reviewed_ids.add(r["booking_id"])

    db.close()
    bookings_html = hh.build_my_bookings_html(bookings, reviewed_ids)
    return render("my_bookings.html", bookings_html=bookings_html)


@app.route("/review/<int:booking_id>", methods=["GET", "POST"])
@login_required(role="user")
def review(booking_id):
    db = get_db()
    booking = db.execute("SELECT * FROM bookings WHERE id = ? AND user_id = ?",
                         (booking_id, session["user_id"])).fetchone()

    if booking is None or booking["status"] != "Completed":
        flash("You can only review completed bookings.")
        db.close()
        return redirect(url_for("my_bookings"))

    if request.method == "POST":
        rating = request.form["rating"]
        comment = request.form["comment"]
        db.execute("""
            INSERT INTO reviews (booking_id, user_id, provider_id, rating, comment)
            VALUES (?, ?, ?, ?, ?)
        """, (booking_id, session["user_id"], booking["provider_id"], rating, comment))
        db.commit()
        db.close()
        flash("Thanks for your review!")
        return redirect(url_for("my_bookings"))

    db.close()
    return render("review.html", booking_id=booking_id, service_name=booking["service_name"])


@app.route("/chatbot", methods=["GET", "POST"])
@login_required(role="user")
def chatbot():
    result_html = ""
    user_text = ""

    if request.method == "POST":
        user_text = request.form["problem"]
        cleaned = clean_text(user_text)

        predicted_category = category_model.predict([cleaned])[0]

        db = get_db()
        providers = db.execute(
            "SELECT * FROM providers WHERE status = 'Approved' AND service_category = ?",
            (predicted_category,)
        ).fetchall()

        provider_list = []
        for p in providers:
            avg_rating, total_reviews = get_avg_rating(p["id"], db)
            provider_list.append({
                "id": p["id"], "name": p["name"], "region": p["region"],
                "experience": p["experience"], "bio": p["bio"],
                "avg_rating": avg_rating if avg_rating else 0, "total_reviews": total_reviews
            })
        db.close()

        recommended_providers = sorted(provider_list, key=lambda x: x["avg_rating"], reverse=True)

        result_html = hh.build_chatbot_result_html(predicted_category, recommended_providers)

    return render("chatbot.html", result_html=result_html, user_text=user_text)


@app.route("/cost_estimator", methods=["GET", "POST"])
@login_required(role="user")
def cost_estimator():
    db = get_db()
    services = db.execute("SELECT * FROM services").fetchall()
    db.close()

    result_html = ""
    user_text = ""
    selected_service = ""

    if request.method == "POST":
        user_text = request.form["problem"]
        selected_service = request.form["service"]

        combined = selected_service + " " + user_text
        cleaned = clean_text(combined)

        predicted_cost = cost_model.predict([cleaned])[0]
        estimated_cost = round(predicted_cost, -1)

        cost_low = int(estimated_cost * 0.8)
        cost_high = int(estimated_cost * 1.2)

        result_html = hh.build_cost_result_html(estimated_cost, cost_low, cost_high)

    services_options = hh.build_service_options(services, selected=selected_service)
    return render("cost_estimator.html", services_options=services_options, result_html=result_html,
                  user_text=user_text)


@app.route("/provider/dashboard")
@login_required(role="provider")
def provider_dashboard():
    return render("provider_dashboard.html", provider_name=session.get("name"))


@app.route("/provider/profile", methods=["GET", "POST"])
@login_required(role="provider")
def provider_profile():
    db = get_db()
    services = db.execute("SELECT * FROM services").fetchall()
    provider = db.execute("SELECT * FROM providers WHERE id = ?", (session["user_id"],)).fetchone()

    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        region = request.form["region"]
        service_category = request.form["service_category"]
        experience = request.form["experience"]
        bio = request.form["bio"]

        db.execute("""
            UPDATE providers SET name = ?, phone = ?, region = ?, service_category = ?, experience = ?, bio = ?
            WHERE id = ?
        """, (name, phone, region, service_category, experience, bio, session["user_id"]))
        db.commit()
        flash("Profile updated.")
        db.close()
        return redirect(url_for("provider_profile"))

    services_options = hh.build_service_options(services, selected=provider["service_category"])
    region_options = hh.build_region_options(REGIONS, selected=provider["region"])
    db.close()
    return render(
        "provider_profile.html",
        provider_name=provider["name"],
        provider_phone=provider["phone"],
        provider_experience=provider["experience"],
        provider_bio=provider["bio"],
        provider_status=provider["status"],
        services_options=services_options,
        region_options=region_options
    )


@app.route("/provider/requests")
@login_required(role="provider")
def provider_requests():
    db = get_db()
    bookings = db.execute("""
        SELECT bookings.*, users.name as user_name, users.phone as user_phone FROM bookings
        JOIN users ON bookings.user_id = users.id
        WHERE bookings.provider_id = ?
        ORDER BY bookings.created_at DESC
    """, (session["user_id"],)).fetchall()
    db.close()
    requests_html = hh.build_provider_requests_html(bookings)
    return render("provider_requests.html", requests_html=requests_html)


@app.route("/provider/requests/<int:booking_id>/<action>", methods=["POST"])
@login_required(role="provider")
def update_request(booking_id, action):
    status_map = {
        "accept": "Accepted",
        "reject": "Cancelled",
        "complete": "Completed"
    }
    new_status = status_map.get(action)
    if new_status is None:
        flash("Invalid action.")
        return redirect(url_for("provider_requests"))

    db = get_db()
    db.execute("UPDATE bookings SET status = ? WHERE id = ? AND provider_id = ?",
               (new_status, booking_id, session["user_id"]))
    db.commit()
    db.close()
    flash("Request updated to " + new_status)
    return redirect(url_for("provider_requests"))


@app.route("/provider/history")
@login_required(role="provider")
def provider_history():
    db = get_db()
    total_completed = db.execute(
        "SELECT COUNT(*) as total FROM bookings WHERE provider_id = ? AND status = 'Completed'",
        (session["user_id"],)
    ).fetchone()["total"]

    avg_rating, total_reviews = get_avg_rating(session["user_id"], db)

    reviews = db.execute("""
        SELECT reviews.*, users.name as user_name FROM reviews
        JOIN users ON reviews.user_id = users.id
        WHERE reviews.provider_id = ?
        ORDER BY reviews.created_at DESC
    """, (session["user_id"],)).fetchall()
    db.close()

    if avg_rating:
        rating_summary = "<p>Average Rating: <b>" + str(avg_rating) + " / 5</b> (" + str(total_reviews) + " reviews)</p>"
    else:
        rating_summary = '<p class="small-text">No reviews yet.</p>'

    return render(
        "provider_history.html",
        total_completed=total_completed,
        rating_summary=rating_summary,
        reviews_html=hh.build_reviews_html(reviews)
    )


@app.route("/admin/dashboard")
@login_required(role="admin")
def admin_dashboard():
    db = get_db()
    total_users = db.execute("SELECT COUNT(*) as total FROM users").fetchone()["total"]
    total_providers = db.execute("SELECT COUNT(*) as total FROM providers WHERE status = 'Approved'").fetchone()["total"]
    pending_providers = db.execute("SELECT COUNT(*) as total FROM providers WHERE status = 'Pending'").fetchone()["total"]

    popular_services = db.execute("""
        SELECT service_name, COUNT(*) as total FROM bookings
        GROUP BY service_name ORDER BY total DESC LIMIT 5
    """).fetchall()
    db.close()

    return render(
        "admin_dashboard.html",
        total_users=total_users,
        total_providers=total_providers,
        pending_msg=hh.build_pending_msg(pending_providers),
        popular_services_table=hh.build_popular_services_table(popular_services)
    )


@app.route("/admin/services", methods=["GET", "POST"])
@login_required(role="admin")
def admin_services():
    db = get_db()

    if request.method == "POST":
        new_service = request.form["service_name"].strip()
        if new_service:
            existing = db.execute("SELECT * FROM services WHERE name = ?", (new_service,)).fetchone()
            if existing is None:
                db.execute("INSERT INTO services (name) VALUES (?)", (new_service,))
                db.commit()
                flash("Service added.")
            else:
                flash("That service already exists.")
        db.close()
        return redirect(url_for("admin_services"))

    services = db.execute("SELECT * FROM services").fetchall()
    db.close()
    return render("admin_services.html", services_table=hh.build_admin_services_table(services))


@app.route("/admin/services/delete/<int:service_id>", methods=["POST"])
@login_required(role="admin")
def delete_service(service_id):
    db = get_db()
    db.execute("DELETE FROM services WHERE id = ?", (service_id,))
    db.commit()
    db.close()
    flash("Service removed.")
    return redirect(url_for("admin_services"))


@app.route("/admin/verify")
@login_required(role="admin")
def admin_verify():
    db = get_db()
    pending = db.execute("SELECT * FROM providers WHERE status = 'Pending'").fetchall()
    db.close()
    return render("admin_verify.html", providers_html=hh.build_pending_providers_html(pending))


@app.route("/admin/verify/<int:provider_id>/<action>", methods=["POST"])
@login_required(role="admin")
def verify_provider(provider_id, action):
    new_status = "Approved" if action == "approve" else "Rejected"
    db = get_db()
    db.execute("UPDATE providers SET status = ? WHERE id = ?", (new_status, provider_id))
    db.commit()
    db.close()
    flash("Provider " + new_status.lower() + ".")
    return redirect(url_for("admin_verify"))


if __name__ == "__main__":
    app.run(debug=True)
