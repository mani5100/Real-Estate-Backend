import os
import requests
from functools import wraps
from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
API_BASE_URL = os.getenv("API_BASE_URL")


# ── API Helper ───────────────────────────────────────────────────────────────

def api(method: str, endpoint: str, token: str = None, **kwargs):
    """
    Central API caller. All requests to FastAPI go through here.
    Automatically attaches Bearer token if present.
    Returns (data, status_code) tuple.
    """
    headers = kwargs.pop("headers", {})

    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"{API_BASE_URL}{endpoint}"

    response = requests.request(
        method,
        url,
        headers=headers,
        **kwargs,
    )

    try:
        data = response.json()
    except Exception:
        data = {}

    return data, response.status_code


# ── Auth Decorators ──────────────────────────────────────────────────────────

def login_required(f):
    """Redirects to login if no token in session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "token" not in session:
            flash("Please login to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def customer_required(f):
    """Only allows customers through. Agents get redirected to chatbot."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "token" not in session:
            flash("Please login to continue.", "warning")
            return redirect(url_for("login"))
        if session.get("role") != "customer":
            flash("Access denied.", "danger")
            return redirect(url_for("chatbot"))
        return f(*args, **kwargs)
    return decorated


def agent_required(f):
    """Only allows agents through. Customers get redirected to properties."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "token" not in session:
            flash("Please login to continue.", "warning")
            return redirect(url_for("login"))
        if session.get("role") != "agent":
            flash("Access denied.", "danger")
            return redirect(url_for("properties"))
        return f(*args, **kwargs)
    return decorated


# ── Auth Routes ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    if "token" in session:
        if session.get("role") == "agent":
            return redirect(url_for("chatbot"))
        return redirect(url_for("properties"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data, status = api("POST", "/auth/login", json={
            "email": request.form["email"],
            "password": request.form["password"],
        })

        if status == 200:
            session["token"] = data["access_token"]
            session["role"] = data["role"]
            session["user_id"] = data["user_id"]

            if data["role"] == "agent":
                return redirect(url_for("chatbot"))

            elif data["role"] == "customer":
                return redirect(url_for("properties"))

            elif data["role"] == "admin":
                return redirect(url_for("admin_applications"))

            else:
                # USER role — check if customer profile exists
                profile, profile_status = api(
                    "GET",
                    "/customers/me",
                    token=data["access_token"],
                )

                if profile_status == 200:
                    session["role"] = "customer"
                    return redirect(url_for("properties"))

                # Check agent application and its status
                application, app_status = api(
                    "GET",
                    "/agents/applications/me",
                    token=data["access_token"],
                )

                if app_status == 200:
                    status_value = application.get("status", "")

                    if status_value == "pending":
                        return redirect(url_for("onboarding_pending"))

                    elif status_value == "rejected":
                        session.clear()
                        flash("Your agent application has been rejected. Please contact support.", "danger")
                        return redirect(url_for("login"))

                    elif status_value == "approved":
                        session.clear()
                        flash("Your application is approved. Please contact support to activate your account.", "info")
                        return redirect(url_for("login"))

                # Nothing found — fresh user, needs to pick a role
                return redirect(url_for("signup_role"))

        else:
            flash(data.get("detail", "Invalid credentials."), "danger")

    return render_template("auth/login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        data, status = api("POST", "/auth/signup", json={
            "full_name": request.form["full_name"],
            "email": request.form["email"],
            "password": request.form["password"],
        })

        if status == 201:
            flash("Account created. Please login.", "success")
            return redirect(url_for("login"))
        else:
            flash(data.get("detail", "Signup failed."), "danger")

    return render_template("auth/signup.html")


@app.route("/signup/role")
@login_required
def signup_role():
    return render_template("auth/signup_role.html")


@app.route("/onboarding/customer", methods=["GET", "POST"])
@login_required
def onboarding_customer():
    if request.method == "POST":
        data, status = api(
            "POST",
            "/customers/me",
            token=session["token"],
            json={"phone": request.form.get("phone")},
        )

        if status == 201:
            session["role"] = "customer"
            return redirect(url_for("properties"))
        else:
            flash(data.get("detail", "Failed to create profile."), "danger")

    return render_template("auth/signup_customer.html")


@app.route("/onboarding/agent", methods=["GET", "POST"])
@login_required
def onboarding_agent():
    if request.method == "POST":
        data, status = api(
            "POST",
            "/agents/applications/me",
            token=session["token"],
            json={
                "license_number": request.form["license_number"],
                "phone": request.form["phone"],
            },
        )

        if status == 201:
            return redirect(url_for("onboarding_pending"))
        else:
            flash(data.get("detail", "Application failed."), "danger")

    return render_template("auth/signup_agent.html")  # ← must be here, not inside POST block

@app.route("/onboarding/pending")
@login_required
def onboarding_pending():
    return render_template("auth/signup_pending.html")


# ── Customer Routes ──────────────────────────────────────────────────────────

@app.route("/properties")
@customer_required
def properties():
    params = {
    "city": request.args.get("city"),
    "min_price": request.args.get("min_price"),
    "max_price": request.args.get("max_price"),
    "min_bedrooms": request.args.get("min_bedrooms"),
    "is_available": True,
}

# Remove None AND empty strings
    params = {k: v for k, v in params.items() if v is not None and v != ""} 

    data, status = api(
        "GET",
        "/properties/",
        token=session["token"],
        params=params,
    )

    properties_list = data.get("results", []) if status == 200 else []

    print("STATUS:", status)
    print("DATA:", data)
    return render_template(
        "customer/properties.html",
        properties=properties_list,
        filters=request.args,
    )


@app.route("/properties/<int:property_id>")
@customer_required
def property_detail(property_id):
    data, status = api(
        "GET",
        f"/properties/{property_id}",
        token=session["token"],
    )

    if status != 200:
        flash("Property not found.", "danger")
        return redirect(url_for("properties"))

    # Check if customer already expressed interest
    interests, int_status = api(
        "GET",
        "/customers/me/interests",
        token=session["token"],
    )

    already_interested = False
    if int_status == 200:
        lead_property_ids = [lead["property"]["id"] for lead in interests.get("leads", [])]
        already_interested = property_id in lead_property_ids

    return render_template(
        "customer/property_detail.html",
        property=data,
        already_interested=already_interested,
    )


@app.route("/properties/<int:property_id>/interested", methods=["POST"])
@customer_required
def express_interest(property_id):
    data, status = api(
        "POST",
        f"/properties/{property_id}/interested",
        token=session["token"],
        json={
            "budget": request.form.get("budget"),
            "payment_method": request.form.get("payment_method"),
            "notes": request.form.get("notes"),
        },
    )

    if status == 201:
        flash("Your interest has been registered successfully.", "success")
    else:
        flash(data.get("detail", "Something went wrong."), "danger")

    return redirect(url_for("property_detail", property_id=property_id))


@app.route("/my-leads")
@customer_required
def my_leads():
    data, status = api(
        "GET",
        "/customers/me/interests",
        token=session["token"],
    )

    leads = data.get("leads", []) if status == 200 else []

    return render_template("customer/my_leads.html", leads=leads)


# ── Agent Routes ─────────────────────────────────────────────────────────────

@app.route("/chatbot")
@agent_required
def chatbot():
    return render_template("agent/chatbot.html")


@app.route("/chatbot/message", methods=["POST"])
@agent_required
def chatbot_message():
    payload = request.get_json()

    data, status = api(
        "POST",
        "/ai/chat",
        token=session["token"],
        json=payload,
    )

    return data, status


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "token" not in session:
            flash("Please login to continue.", "warning")
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            session.clear()
            flash("Admin access only.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

@app.route("/admin/applications")
@admin_required
def admin_applications():
    data, status = api(
        "GET",
        "/agents/applications",
        token=session["token"],
    )


    applications = data.get("results", []) if status == 200 else []

    return render_template("admin/applications.html", applications=applications)


@app.route("/admin/applications/<int:application_id>/approve", methods=["POST"])
@admin_required
def admin_approve(application_id):
    data, status = api(
        "POST",
        f"/agents/applications/{application_id}/approve",
        token=session["token"],
    )

    if status == 200:
        flash("Agent approved successfully.", "success")
    else:
        flash(data.get("detail", "Approval failed."), "danger")

    return redirect(url_for("admin_applications"))


@app.route("/admin/applications/<int:application_id>/reject", methods=["POST"])
@admin_required
def admin_reject(application_id):
    data, status = api(
        "POST",
        f"/agents/applications/{application_id}/reject",
        token=session["token"],
    )

    if status == 200:
        flash("Application rejected.", "success")
    else:
        flash(data.get("detail", "Rejection failed."), "danger")

    return redirect(url_for("admin_applications"))


@app.route("/agent/properties")
@agent_required
def agent_properties():
    data, status = api(
        "GET",
        "/properties/my",
        token=session["token"],
    )

    properties_list = data if status == 200 else []

    return render_template("agent/properties.html", properties=properties_list)


@app.route("/agent/properties/add", methods=["GET", "POST"])
@agent_required
def agent_add_property():
    if request.method == "POST":
        data, status = api(
            "POST",
            "/properties/",
            token=session["token"],
            json={
                "title": request.form["title"],
                "city": request.form["city"],
                "address": request.form["address"],
                "price": int(request.form["price"]),
                "bedrooms": int(request.form["bedrooms"]),
                "bathrooms": int(request.form["bathrooms"]),
                "area_sqft": float(request.form["area_sqft"]),
                "description": request.form.get("description"),
                "property_type": request.form.get("property_type"),
                "is_available": True,
            },
        )

        if status == 201:
            flash("Property added successfully.", "success")
            return redirect(url_for("agent_properties"))
        else:
            flash(data.get("detail", "Failed to add property."), "danger")

    return render_template("agent/add_property.html")

# ── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=5000)