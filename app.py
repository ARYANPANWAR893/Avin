from flask import Flask, request, jsonify, render_template, session, redirect
from flask_cors import CORS
from services.ai_service import predict_resolution_time_and_process
from datetime import datetime

from models import db, Issue, Mission, LedgerEntry, User, Reward

from services.ai_service import (
    classify_issue,
    predict_risk,
    ai_rewrite_complaint,
    extract_location_from_text,
    reverse_geocode
)

from services.mission_service import generate_missions
from services.ledger_service import add_ledger_entry
from services.blockchain_service import write_proof_to_blockchain

from services.ai_service import (
    classify_issue,
    predict_risk,
    ai_rewrite_complaint,
    extract_location_from_text,
    reverse_geocode,
    detect_language,
    translate_to_english
)


app = Flask(__name__)
app.secret_key = "dev-secret-key"

CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


# -------------------------------------------------------------------
# -------------------------- FRONTEND -------------------------------
# -------------------------------------------------------------------

@app.route("/")
def landing():

    if "user_id" in session:
        return redirect("/report")

    return render_template("home.html")


@app.route("/issue/<int:issue_id>/view")
def view_issue(issue_id):
    return render_template("issue.html", issue_id=issue_id)


@app.route("/user/<int:user_id>/ledger/view")
def ledger_view(user_id):
    return render_template("ledger.html", user_id=user_id)


# -------------------------------------------------------------------
# ---------------------- PREFILL (POPUP STEP) ------------------------
# -------------------------------------------------------------------

@app.route("/api/issue/prefill", methods=["POST"])
def prefill_issue():

    if "user_id" not in session:
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json() or {}

    text = (data.get("text") or "").strip()
    text = (data.get("text") or "").strip()

    lang = detect_language(text)
    if lang != "en" and lang != "unknown":
        text = translate_to_english(text)

    browser_location = data.get("browser_location")

    if not text:
        return jsonify({
            "category": "",
            "subcategory": "",
            "location": "",
            "description": ""
        })

    classification = classify_issue(text)
    ai_location = extract_location_from_text(text)

    final_location = None

    if ai_location:
        final_location = ai_location

    elif browser_location:
        lat = browser_location.get("lat")
        lng = browser_location.get("lng")

        if lat is not None and lng is not None:
            geo = reverse_geocode(lat, lng)
            final_location = geo if geo else f"{lat},{lng}"
        else:
            final_location = "Unknown"

    else:
        final_location = "Unknown"

    return jsonify({
        "category": classification["category"],
        "subcategory": classification["subcategory"],
        "location": final_location,
        "description": text
    })


# -------------------------------------------------------------------
# ------------------------- FINAL REPORT -----------------------------
# -------------------------------------------------------------------

@app.route("/report")
def report_page():

    if "user_id" not in session:
        return redirect("/login")

    # officers must NOT access citizen dashboard
    if session.get("is_officer"):
        return redirect("/officer")

    user_id = session["user_id"]

    issues = Issue.query.filter_by(user_id=user_id)\
        .order_by(Issue.created_at.desc())\
        .all()

    return render_template(
        "report.html",
        issues=issues
    )

@app.route("/api/map/issues")
def map_issues():

    if "user_id" not in session:
        return jsonify({"error": "unauthorized"}), 401

    location = request.args.get("location")

    q = Issue.query

    if location:
        q = q.filter(Issue.location == location)

    issues = q.all()

    # IMPORTANT:
    # We only have text locations, not lat/lng stored.
    # So we rely on reverse geocode lookup at report time
    # OR fallback to stored lat/lng if you add them later.

    return jsonify([
        {
            "id": i.id,
            "category": i.category,
            "subcategory": i.subcategory,
            "location": i.location,
            "lat": getattr(i, "lat", None),
            "lng": getattr(i, "lng", None),
            "status": i.status
        }
        for i in issues
        if getattr(i, "lat", None) and getattr(i, "lng", None)
    ])

from collections import defaultdict
from flask import jsonify, session
from models import Issue


@app.route("/api/map/regions")
def map_regions():

    rows = db.session.query(
        Issue.location,
        db.func.count(Issue.id)
    ).group_by(Issue.location).all()

    results = []

    for loc, count in rows:

        cats = db.session.query(
            Issue.category,
            db.func.count(Issue.id)
        ).filter(Issue.location == loc)\
         .group_by(Issue.category).all()

        breakdown = {c: n for c, n in cats}

        dominant = max(breakdown, key=breakdown.get) if breakdown else None

        results.append({
            "location": loc,
            "count": count,
            "dominant_category": dominant,
            "category_breakdown": breakdown
        })

    return jsonify(results)


@app.route("/api/admin/leaderboard")
def admin_leaderboard():

    if "user_id" not in session:
        return jsonify({"error":"unauthorized"}),401

    user = User.query.get(session["user_id"])

    if not user.email.endswith("@delhi.gov.in"):
        return jsonify({"error":"forbidden"}),403

    users = (
        User.query
        .filter(~User.email.endswith("@delhi.gov.in"))
        .order_by(User.credits.desc())
        .limit(50)
        .all()
    )

    return jsonify([
        {
            "id": u.id,
            "name": u.name,
            "credits": u.credits
        }
        for u in users
    ])


@app.route("/api/issue/report", methods=["POST"])
def report_issue():

    if "user_id" not in session:
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json() or {}

    user_id = session["user_id"]

    description = (data.get("description") or "").strip()
    lang = detect_language(description)

    if lang != "en" and lang != "unknown":
        description = translate_to_english(description)

    category = data.get("category")
    subcategory = data.get("subcategory")
    location = data.get("location")

    if not description:
        return jsonify({"error": "description required"}), 400

    classification = classify_issue(description)

    # safety fallback if popup was edited badly
    final_category = category or classification["category"]
    final_subcategory = subcategory or classification["subcategory"]

    risk = predict_risk(classification, location)

    issue = Issue(
        user_id=user_id,
        original_text=description,
        category=final_category,
        subcategory=final_subcategory,
        location=location,
        severity=risk["severity"],
        status="SUBMITTED",
        created_at=datetime.utcnow()
    )

    db.session.add(issue)
    db.session.commit()

    missions = generate_missions(issue)

    return jsonify({
        "issue_id": issue.id,
        "category": issue.category,
        "subcategory": issue.subcategory,
        "location_used": issue.location,
        "missions": missions
    })


# -------------------------------------------------------------------
# --------------------------- AUTH ----------------------------------
# -------------------------------------------------------------------

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        if not name or not email or not password:
            return "Missing fields"

        existing = User.query.filter_by(email=email).first()
        if existing:
            return "User already exists"

        user = User(name=name, email=email, password=password)

        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id
        return redirect("/")

    return render_template("signup.html")

@app.route("/api/me/impact")
def my_impact():

    uid = session["user_id"]

    areas = db.session.query(
        Issue.location,
        db.func.count(Issue.id)
    ).filter(Issue.user_id == uid)\
     .group_by(Issue.location)\
     .all()

    return jsonify(dict(areas))

from sqlalchemy import func

from sqlalchemy import func

@app.route("/api/me/rank")
def my_rank():

    if "user_id" not in session:
        return jsonify({"error": "unauthorized"}), 401

    uid = session["user_id"]

    # officers should not use ranking
    me = User.query.get(uid)
    if me.email.endswith("@delhi.gov.in"):
        return jsonify({"error": "officers have no public rank"}), 403

    # -----------------------------
    # find user's main area
    # -----------------------------
    area_row = db.session.query(
        Issue.location,
        func.count(Issue.id).label("c")
    ).filter(Issue.user_id == uid)\
     .group_by(Issue.location)\
     .order_by(func.count(Issue.id).desc())\
     .first()

    if not area_row or not area_row[0]:
        return jsonify({
            "area": None,
            "rank_in_area": None,
            "total_users_in_area": 0,
            "rank_in_delhi": None,
            "total_users_in_delhi":
                User.query.filter(~User.email.endswith("@delhi.gov.in")).count()
        })

    area = area_row[0]

    # -----------------------------
    # area ranking
    # -----------------------------
    users_in_area = db.session.query(
        User.id,
        User.credits
    ).join(Issue, Issue.user_id == User.id)\
     .filter(Issue.location == area)\
     .filter(~User.email.endswith("@delhi.gov.in"))\
     .group_by(User.id)\
     .order_by(User.credits.desc())\
     .all()

    area_rank = None
    for idx, row in enumerate(users_in_area, start=1):
        if row.id == uid:
            area_rank = idx
            break

    # -----------------------------
    # delhi ranking
    # -----------------------------
    all_users = User.query\
        .filter(~User.email.endswith("@delhi.gov.in"))\
        .order_by(User.credits.desc())\
        .all()

    delhi_rank = None
    for idx, u in enumerate(all_users, start=1):
        if u.id == uid:
            delhi_rank = idx
            break

    return jsonify({
        "area": area,
        "rank_in_area": area_rank,
        "total_users_in_area": len(users_in_area),
        "rank_in_delhi": delhi_rank,
        "total_users_in_delhi": len(all_users)
    })


@app.route("/profile")
def profile_page():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("profile.html")

@app.route("/api/leaderboard")
def api_leaderboard():

    users = User.query\
        .filter(~User.email.endswith("@delhi.gov.in"))\
        .order_by(User.credits.desc())\
        .limit(50)\
        .all()

    return jsonify([
        {
            "id": u.id,
            "name": u.name,
            "credits": u.credits
        }
        for u in users
    ])



@app.route("/impact")
def impact_page():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("impact.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        # -------------------------
        # OFFICER DEMO LOGIN
        # -------------------------
        if email.endswith("@delhi.gov.in"):

            user = User.query.filter_by(email=email).first()

            # auto create officer account if not present
            if not user:
                user = User(
                    name=email.split("@")[0],
                    email=email,
                    password="OFFICER_DEMO"
                )
                db.session.add(user)
                db.session.commit()

            session["user_id"] = user.id
            session["is_officer"] = True

            return redirect("/officer")

        # -------------------------
        # NORMAL USER LOGIN
        # -------------------------
        user = User.query.filter_by(email=email, password=password).first()

        if not user:
            return "Invalid credentials"

        session["user_id"] = user.id
        session["is_officer"] = False

        return redirect("/")

    return render_template("login.html")



@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# -------------------------------------------------------------------
# ----------------------------- API ---------------------------------
# -------------------------------------------------------------------

@app.route("/api/issue/<int:issue_id>", methods=["GET"])
def get_issue(issue_id):

    issue = Issue.query.get_or_404(issue_id)
    return jsonify(issue.to_dict())


@app.route("/api/issue/<int:issue_id>/missions", methods=["GET"])
def issue_missions(issue_id):

    missions = Mission.query.filter_by(issue_id=issue_id).all()

    return jsonify([
        {
            "id": m.id,
            "title": m.title,
            "status": m.status,
            "category": m.category,
            "location": m.location
        } for m in missions
    ])


@app.route("/api/issue/<int:issue_id>/rewrite", methods=["GET"])
def rewrite_complaint(issue_id):

    issue = Issue.query.get_or_404(issue_id)

    rewritten = ai_rewrite_complaint(
    issue.original_text,
    issue.category
)


    return jsonify({"rewritten_complaint": rewritten})


@app.route("/api/mission/<int:mission_id>/complete", methods=["POST"])
def complete_mission(mission_id):

    mission = Mission.query.get_or_404(mission_id)

    data = request.get_json() or {}

    before_hash = data.get("before_hash")
    after_hash = data.get("after_hash")

    mission.status = "COMPLETED"
    mission.completed_at = datetime.utcnow()

    proof = write_proof_to_blockchain(
        mission_id=mission.id,
        before_hash=before_hash,
        after_hash=after_hash
    )

    # FIX: always use the issue owner for ledger
    issue = Issue.query.get(mission.issue_id)

    add_ledger_entry(
        user_id=issue.user_id,
        mission_id=mission.id,
        category=mission.category
    )

    proof = write_proof_to_blockchain(...)
    mission.blockchain_tx = proof["tx_id"]


    user = User.query.get(mission.user_id)

    reward_map = {
        "waste": 10,
        "water": 12,
        "air": 15,
        "roads": 8,
        "greenery": 15
    }

    user.credits += reward_map.get(mission.category, 5)


    db.session.commit()

    return jsonify({
        "status": "completed",
        "blockchain_tx": proof
    })

@app.route("/api/blockchain/verify/<tx>")
def verify_tx(tx):
    return jsonify({"verified": True, "tx": tx})

@app.route("/api/me/rewards")
def my_rewards():

    u = User.query.get(session["user_id"])

    rewards = Reward.query\
        .filter(Reward.min_credits <= u.credits)\
        .all()

    return jsonify([
        {"name": r.name, "description": r.description}
        for r in rewards
    ])


@app.route("/api/user/<int:user_id>/ledger", methods=["GET"])
def user_ledger(user_id):

    entries = LedgerEntry.query.filter_by(user_id=user_id)\
        .order_by(LedgerEntry.timestamp.desc())\
        .all()

    return jsonify([e.to_dict() for e in entries])

@app.route("/leaderboard")
def leaderboard_page():

    if "user_id" not in session:
        return redirect("/login")

    return render_template("leaderboard.html")

@app.route("/api/me")
def my_profile():

    if "user_id" not in session:
        return jsonify({"error":"unauthorized"}),401

    u = User.query.get(session["user_id"])

    return jsonify({
        "name": u.name,
        "email": u.email,
        "credits": u.credits,
        "public_profile": u.public_profile
    })

@app.route("/api/me/metrics")
def my_metrics():

    uid = session.get("user_id")

    total = LedgerEntry.query.filter_by(user_id=uid).count()

    by_cat = db.session.query(
        LedgerEntry.category,
        db.func.count(LedgerEntry.id)
    ).filter_by(user_id=uid).group_by(LedgerEntry.category).all()

    return jsonify({
        "total_actions": total,
        "by_category": dict(by_cat)
    })

@app.route("/api/me/public", methods=["POST"])
def toggle_public():

    u = User.query.get(session["user_id"])
    u.public_profile = bool(request.json.get("public"))
    db.session.commit()
    return jsonify({"ok":True})


@app.route("/api/admin/area-insights", methods=["GET"])
def area_insights():

    location = request.args.get("location")

    if not location:
        return jsonify({"error": "location required"}), 400

    total_missions = Mission.query.filter_by(location=location).count()
    completed = Mission.query.filter_by(
        location=location,
        status="COMPLETED"
    ).count()

    return jsonify({
        "location": location,
        "total_missions": total_missions,
        "completed_missions": completed,
        "participation_rate":
            round((completed / total_missions), 2) if total_missions else 0
    })


@app.route("/api/issue/categories", methods=["GET"])
def issue_categories():
    from services.ai_service import ISSUE_TAXONOMY
    return jsonify(ISSUE_TAXONOMY)

@app.route("/api/issues/nearby", methods=["POST"])
def nearby_issues():

    data = request.get_json() or {}

    lat = data.get("lat")
    lng = data.get("lng")

    if lat is None or lng is None:
        return jsonify([])

    location_name = reverse_geocode(lat, lng)

    if not location_name:
        return jsonify({
            "location": None,
            "issues": []
        })


    # simple locality match
    issues = Issue.query.filter(
        Issue.location.ilike(f"%{location_name}%")
    ).order_by(Issue.created_at.desc()).limit(10).all()

    return jsonify({
    "location": location_name,
    "issues": [
        {
            "id": i.id,
            "category": i.category,
            "subcategory": i.subcategory,
            "location": i.location,
            "created_at": i.created_at.isoformat()
        } for i in issues
    ]
})

@app.route("/officer")
def officer_dashboard():

    if "user_id" not in session or not session.get("is_officer"):
        return redirect("/login")

    return render_template("officer.html")


@app.route("/api/officer/issues", methods=["GET"])
def officer_issues():

    if "user_id" not in session or not session.get("is_officer"):
        return jsonify({"error": "forbidden"}), 403

    if "user_id" not in session:
        return jsonify({"error": "unauthorized"}), 401

    user = User.query.get(session["user_id"])
    if not user or not user.email.endswith("@delhi.gov.in"):
        return jsonify({"error": "forbidden"}), 403

    locality = request.args.get("location")

    query = Issue.query

    if locality:
        query = query.filter(Issue.location.ilike(f"%{locality}%"))

    issues = query.order_by(Issue.created_at.desc()).limit(50).all()

    return jsonify([i.to_dict() for i in issues])


@app.route("/api/officer/issue/<int:issue_id>/update", methods=["POST"])
def officer_update_issue(issue_id):

    # officer only
    if "user_id" not in session or not session.get("is_officer"):
        return jsonify({"error": "forbidden"}), 403

    issue = Issue.query.get_or_404(issue_id)
    data = request.get_json() or {}

    old_status = issue.status

    new_status = data.get("status")
    days = data.get("estimated_days")

    if new_status:
        issue.status = new_status

    if days not in (None, ""):
        try:
            issue.estimated_days = int(days)
        except ValueError:
            pass

    # ------------------------------------------------
    # give credits only once when resolved
    # ------------------------------------------------
    if old_status != "RESOLVED" and new_status == "RESOLVED":

        user = User.query.get(issue.user_id)

        reward_map = {
            "waste": 10,
            "water": 12,
            "air": 15,
            "roads": 8,
            "greenery": 15,
            "transport": 8,
            "public infrastructure": 8,
            "noise": 6,
            "animals": 6
        }

        user.credits = (user.credits or 0) + reward_map.get(issue.category, 5)

    db.session.commit()

    return jsonify({"success": True})


@app.route("/api/issue/<int:issue_id>/prediction", methods=["GET"])
def issue_prediction(issue_id):

    issue = Issue.query.get_or_404(issue_id)

    result = predict_resolution_time_and_process(
        issue.category,
        issue.subcategory
    )

    return jsonify(result)

@app.route("/api/reverse-geocode", methods=["POST"])
def api_reverse_geocode():

    data = request.get_json() or {}

    lat = data.get("lat")
    lng = data.get("lng")

    if lat is None or lng is None:
        return jsonify({"location": None})

    name = reverse_geocode(lat, lng)

    return jsonify({"location": name})

# -------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)