from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from ..extensions.db import db
from ..extensions.login import login_manager
from ..models import User, Role


auth_bp = Blueprint("auth", __name__)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@auth_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("auth.post_login_redirect"))
    return render_template("landing.html")


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("customer/signup.html")

    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")
    role = request.form.get("role", Role.customer.value)

    if not username or not email or not password or role not in {r.value for r in Role}:
        flash("Invalid input.", "danger")
        return redirect(url_for("auth.signup"))

    if User.query.filter((User.username == username) | (User.email == email)).first():
        flash("Username or email already exists.", "warning")
        return redirect(url_for("auth.signup"))

    user = User(username=username, email=email, role=Role(role))
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash("Signup successful. Please log in.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Generic login page (defaults to customer view) with role-agnostic authentication
    if request.method == "GET":
        return render_template("customer/login.html")

    username_or_email = request.form.get("username") or request.form.get("email")
    password = request.form.get("password")

    user = (
        User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        )
        .limit(1)
        .first()
    )
    if not user:
        flash("Invalid credentials.", "danger")
        return redirect(url_for("auth.login"))

    # Check hashed password first
    if not user.check_password(password):
        # Fallback: plaintext password in DB (upgrade on success)
        if user.password == password:
            user.set_password(password)
            db.session.commit()
        else:
            flash("Invalid credentials.", "danger")
            return redirect(url_for("auth.login"))

    login_user(user)
    session["user_id"] = user.id
    session["username"] = user.username
    session["role"] = user.role.value if hasattr(user.role, "value") else str(user.role)
    return redirect(url_for("auth.post_login_redirect"))


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("auth.login"))


@auth_bp.route("/post-login")
@login_required
def post_login_redirect():
    if current_user.role == Role.customer:
        return redirect(url_for("customer.dashboard"))
    if current_user.role == Role.hotel:
        return redirect(url_for("hotel.dashboard"))
    if current_user.role == Role.package_manager:
        return redirect(url_for("pkg_mgr.dashboard"))
    return redirect(url_for("auth.login"))


# -------- Role selection from landing -------- #
@auth_bp.route("/select-role", methods=["POST"])
def select_role():
    role = request.form.get("role")
    if role == Role.customer.value:
        return redirect(url_for("auth.customer_login"))
    if role == Role.hotel.value:
        return redirect(url_for("auth.hotel_login"))
    if role == Role.package_manager.value:
        return redirect(url_for("auth.package_manager_login"))
    flash("Invalid role selected.", "danger")
    return redirect(url_for("auth.index"))


# -------- Role-specific signup -------- #
def _handle_signup(role: Role, template_name: str):
    if request.method == "GET":
        return render_template(template_name)

    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    if not username or not email or not password:
        flash("Invalid input.", "danger")
        return redirect(request.url)

    if User.query.filter((User.username == username) | (User.email == email)).first():
        flash("Username or email already exists.", "warning")
        return redirect(request.url)

    user = User(username=username, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash("Signup successful. Please log in.", "success")

    if role == Role.customer:
        return redirect(url_for("auth.customer_login"))
    if role == Role.hotel:
        return redirect(url_for("auth.hotel_login"))
    return redirect(url_for("auth.package_manager_login"))


@auth_bp.route("/signup/customer", methods=["GET", "POST"])
def customer_signup():
    return _handle_signup(Role.customer, "customer/signup.html")


@auth_bp.route("/signup/hotel", methods=["GET", "POST"])
def hotel_signup():
    # Hotel signup collects hotel info as well; user record is created here.
    if request.method == "GET":
        return render_template("hotel/signup.html")

    # First create the user
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")
    if not username or not email or not password:
        flash("Invalid input.", "danger")
        return redirect(request.url)

    if User.query.filter((User.username == username) | (User.email == email)).first():
        flash("Username or email already exists.", "warning")
        return redirect(request.url)

    user = User(username=username, email=email, role=Role.hotel)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    # Also create a default Hotel using provided fields if any
    from ..models import Hotel

    hotel = Hotel(
        user_id=user.id,
        name=request.form.get("hotel_name") or f"{username}'s Hotel",
        location=request.form.get("location") or "",
        description=request.form.get("description") or "",
        contact_info=request.form.get("contact_info") or "",
        amenities=request.form.get("amenities") or "",
    )
    db.session.add(hotel)
    db.session.commit()
    flash("Hotel account created. Please log in.", "success")
    return redirect(url_for("auth.hotel_login"))


@auth_bp.route("/signup/manager", methods=["GET", "POST"])
def package_manager_signup():
    return _handle_signup(Role.package_manager, "package_manager/signup.html")


# -------- Role-specific login -------- #
def _handle_login(template_name: str, expected_role: Role | None):
    if request.method == "GET":
        return render_template(template_name)

    username_or_email = request.form.get("username") or request.form.get("email")
    password = request.form.get("password")

    user = (
        User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        )
        .limit(1)
        .first()
    )
    if not user:
        flash("Invalid credentials.", "danger")
        return redirect(request.url)

    if not user.check_password(password):
        # Fallback to plaintext (legacy seed data) and upgrade
        if user.password == password:
            user.set_password(password)
            db.session.commit()
        else:
            flash("Invalid credentials.", "danger")
            return redirect(request.url)

    if expected_role and (user.role != expected_role):
        flash("Invalid role for this login page.", "danger")
        return redirect(request.url)

    login_user(user)
    session["user_id"] = user.id
    session["username"] = user.username
    session["role"] = user.role.value if hasattr(user.role, "value") else str(user.role)
    return redirect(url_for("auth.post_login_redirect"))


@auth_bp.route("/login/customer", methods=["GET", "POST"])
def customer_login():
    return _handle_login("customer/login.html", Role.customer)


@auth_bp.route("/login/hotel", methods=["GET", "POST"])
def hotel_login():
    return _handle_login("hotel/login.html", Role.hotel)


@auth_bp.route("/login/manager", methods=["GET", "POST"])
def package_manager_login():
    return _handle_login("package_manager/login.html", Role.package_manager)
