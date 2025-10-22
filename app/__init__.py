from flask import Flask
from .extensions.db import db
from .extensions.migrate import migrate
from .extensions.login import login_manager
from .utils.config import load_config
from flask import redirect, url_for, render_template, request, flash
from flask_login import login_required, current_user
from .models import Role


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    load_config(app)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Register blueprints
    from .auth.routes import auth_bp
    from .customer.routes import customer_bp
    from .hotel.routes import hotel_bp
    from .package_manager.routes import pkg_mgr_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp, url_prefix="/customer")
    app.register_blueprint(hotel_bp, url_prefix="/hotel")
    app.register_blueprint(pkg_mgr_bp, url_prefix="/manager")

    @app.route("/health")
    def health():
        return {"status": "ok"}

    # --- Template endpoint aliases ---
    # Landing and role selection used in templates
    @app.route("/landing")
    def landing():
        return redirect(url_for("auth.index"))

    @app.route("/select-role", methods=["POST"])
    def select_role():
        return auth_bp.view_functions["select_role"]()

    # Customer aliases
    @app.route("/customer/dashboard")
    def customer_dashboard():
        return customer_bp.view_functions["dashboard"]()

    @app.route("/customer/packages")
    def customer_packages():
        return customer_bp.view_functions["list_packages"]()

    @app.route("/customer/profile")
    def customer_profile():
        return render_template("customer/profile.html", user=current_user)

    @app.route("/customer/search-hotels")
    def customer_search_hotels():
        return customer_bp.view_functions["search_hotels"]()

    # Auth aliases referenced by templates
    @app.route("/login")
    def login():
        return auth_bp.view_functions["login"]()

    @app.route("/logout")
    def logout():
        return auth_bp.view_functions["logout"]()

    @app.route("/signup")
    def signup():
        return auth_bp.view_functions["signup"]()

    @app.route("/customer/login", methods=["GET", "POST"])
    def customer_login():
        return auth_bp.view_functions["customer_login"]()

    @app.route("/customer/signup", methods=["GET", "POST"])
    def customer_signup():
        return auth_bp.view_functions["customer_signup"]()

    @app.route("/hotel/login", methods=["GET", "POST"])
    def hotel_login():
        return auth_bp.view_functions["hotel_login"]()

    @app.route("/hotel/signup", methods=["GET", "POST"])
    def hotel_signup():
        return auth_bp.view_functions["hotel_signup"]()

    @app.route("/manager/login", methods=["GET", "POST"])
    def package_manager_login():
        return auth_bp.view_functions["package_manager_login"]()

    @app.route("/manager/signup", methods=["GET", "POST"])
    def package_manager_signup():
        return auth_bp.view_functions["package_manager_signup"]()

    # Templates use 'package_manager_register' action on signup form
    @app.route("/manager/register", methods=["POST"])
    def package_manager_register():
        return auth_bp.view_functions["package_manager_signup"]()

    # Hotel aliases used in templates
    @app.route("/hotel/dashboard")
    def hotel_dashboard():
        return hotel_bp.view_functions["dashboard"]()

    @app.route("/hotel/add-package", methods=["GET", "POST"])
    @login_required
    def hotel_add_package():
        if current_user.role != Role.hotel:
            flash("Unauthorized", "danger")
            return redirect(url_for("auth.post_login_redirect"))
        if request.method == "GET":
            return render_template("hotel/add_package.html")
        # Handle create via form submit
        from .models import Hotel, HotelPackage
        hotel = Hotel.query.filter_by(user_id=current_user.id).first()
        if not hotel:
            flash("Please create your hotel first.", "warning")
            return redirect(url_for("hotel_dashboard"))
        pkg = HotelPackage(
            hotel_id=hotel.id,
            title=request.form.get("title"),
            description=request.form.get("description"),
            price=request.form.get("price"),
            amenities=request.form.get("amenities"),
        )
        from .extensions.db import db
        db.session.add(pkg)
        db.session.commit()
        flash("Hotel package created.", "success")
        return redirect(url_for("hotel_dashboard"))

    @app.route("/hotel/edit-package/<int:package_id>", methods=["GET", "POST"])
    def hotel_edit_package(package_id: int):
        from .models import HotelPackage, Hotel
        from .extensions.db import db
        if current_user.role != Role.hotel:
            flash("Unauthorized", "danger")
            return redirect(url_for("auth.post_login_redirect"))
        if request.method == "POST":
            pkg = HotelPackage.query.get_or_404(package_id)
            # Ensure ownership
            hotel = Hotel.query.filter_by(id=pkg.hotel_id, user_id=current_user.id).first()
            if not hotel:
                flash("Unauthorized", "danger")
                return redirect(url_for("hotel_dashboard"))
            for field in ["title", "description", "price", "amenities"]:
                if field in request.form and request.form.get(field) is not None:
                    setattr(pkg, field, request.form.get(field))
            db.session.commit()
            flash("Hotel package updated.", "success")
            return redirect(url_for("hotel_dashboard"))
        pkg = HotelPackage.query.get_or_404(package_id)
        # Build a view model with optional fields used by template
        view_pkg = {
            "id": pkg.id,
            "title": pkg.title,
            "description": pkg.description,
            "price": pkg.price,
            "amenities": pkg.amenities,
            "created_at": pkg.created_at,
            # Optional fields not present in model
            "duration": None,
            "terms": None,
            "start_date": None,
            "end_date": None,
            "featured": False,
        }
        return render_template("hotel/edit_package.html", package=view_pkg)

    @app.route("/hotel/delete-package/<int:package_id>")
    def hotel_delete_package(package_id: int):
        from .models import HotelPackage, Hotel
        from .extensions.db import db
        if current_user.role != Role.hotel:
            flash("Unauthorized", "danger")
            return redirect(url_for("auth.post_login_redirect"))
        pkg = HotelPackage.query.get_or_404(package_id)
        # Ensure ownership
        hotel = Hotel.query.filter_by(id=pkg.hotel_id, user_id=current_user.id).first()
        if not hotel:
            flash("Unauthorized", "danger")
            return redirect(url_for("hotel_dashboard"))
        db.session.delete(pkg)
        db.session.commit()
        flash("Hotel package deleted.", "success")
        return redirect(url_for("hotel_dashboard"))

    # Package manager aliases used in templates
    @app.route("/manager/dashboard")
    def package_manager_dashboard():
        return pkg_mgr_bp.view_functions["dashboard"]()

    @app.route("/manager/add-package", methods=["GET", "POST"])
    @login_required
    def package_manager_add_package():
        from .models import TouristGuide
        if current_user.role != Role.package_manager:
            flash("Unauthorized", "danger")
            return redirect(url_for("auth.post_login_redirect"))
        if request.method == "GET":
            guides = TouristGuide.query.order_by(TouristGuide.created_at.desc()).all()
            return render_template("package_manager/add_package.html", guides=guides)
        # Delegate to blueprint create handler
        return pkg_mgr_bp.view_functions["create_package"]()

    @app.route("/manager/add-guide", methods=["GET", "POST"])
    @login_required
    def package_manager_add_guide():
        if current_user.role != Role.package_manager:
            flash("Unauthorized", "danger")
            return redirect(url_for("auth.post_login_redirect"))
        if request.method == "GET":
            return render_template("package_manager/add_guide.html")
        return pkg_mgr_bp.view_functions["create_guide"]()

    @app.route("/manager/edit-package/<int:package_id>", methods=["GET", "POST"])
    @login_required
    def package_manager_edit_package(package_id: int):
        from .models import TourismPackage
        if current_user.role != Role.package_manager:
            flash("Unauthorized", "danger")
            return redirect(url_for("auth.post_login_redirect"))
        if request.method == "POST":
            return pkg_mgr_bp.view_functions["update_package"](package_id)
        pkg = TourismPackage.query.get_or_404(package_id)
        return render_template("package_manager/edit_package.html", package=pkg)

    @app.route("/manager/delete-package/<int:package_id>")
    @login_required
    def package_manager_delete_package(package_id: int):
        if current_user.role != Role.package_manager:
            flash("Unauthorized", "danger")
            return redirect(url_for("auth.post_login_redirect"))
        # Delete and redirect with flash
        response = pkg_mgr_bp.view_functions["delete_package"](package_id)
        flash("Package deleted.", "success")
        return redirect(url_for("package_manager_dashboard"))

    @app.route("/manager/edit-guide/<int:guide_id>", methods=["GET", "POST"])
    @login_required
    def package_manager_edit_guide(guide_id: int):
        from .models import TouristGuide
        if current_user.role != Role.package_manager:
            flash("Unauthorized", "danger")
            return redirect(url_for("auth.post_login_redirect"))
        if request.method == "POST":
            return pkg_mgr_bp.view_functions["update_guide"](guide_id)
        guide = TouristGuide.query.get_or_404(guide_id)
        return render_template("package_manager/edit_guide.html", guide=guide)

    @app.route("/manager/delete-guide/<int:guide_id>")
    @login_required
    def package_manager_delete_guide(guide_id: int):
        if current_user.role != Role.package_manager:
            flash("Unauthorized", "danger")
            return redirect(url_for("auth.post_login_redirect"))
        pkg_mgr_bp.view_functions["delete_guide"](guide_id)
        flash("Guide deleted.", "success")
        return redirect(url_for("package_manager_dashboard"))

    # Ensure tables exist (validates DB connection and schema)
    with app.app_context():
        try:
            db.create_all()
        except Exception as exc:
            # Do not crash on startup; errors will surface on first DB usage
            app.logger.error("Database initialization failed: %s", exc)

    return app
