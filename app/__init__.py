from flask import Flask
from .extensions.db import db
from .extensions.migrate import migrate
from .extensions.login import login_manager
from .utils.config import load_config
from flask import redirect, url_for


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
        from flask_login import current_user
        return __import__("flask").flask.render_template("customer/profile.html", user=current_user)

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

    # Hotel aliases used in templates
    @app.route("/hotel/dashboard")
    def hotel_dashboard():
        return hotel_bp.view_functions["dashboard"]()

    @app.route("/hotel/add-package")
    def hotel_add_package():
        # Render add package template; POST handled by /hotel/package
        return __import__("flask").flask.render_template("hotel/add_package.html")

    @app.route("/hotel/edit-package/<int:package_id>")
    def hotel_edit_package(package_id: int):
        from .models import HotelPackage
        pkg = HotelPackage.query.get_or_404(package_id)
        return __import__("flask").flask.render_template("hotel/edit_package.html", package=pkg)

    @app.route("/hotel/delete-package/<int:package_id>")
    def hotel_delete_package(package_id: int):
        return hotel_bp.view_functions["delete_hotel_package"](package_id)

    # Package manager aliases used in templates
    @app.route("/manager/dashboard")
    def package_manager_dashboard():
        return pkg_mgr_bp.view_functions["dashboard"]()

    @app.route("/manager/add-package")
    def package_manager_add_package():
        from .models import TouristGuide
        guides = TouristGuide.query.order_by(TouristGuide.created_at.desc()).all()
        return __import__("flask").flask.render_template("package_manager/add_package.html", guides=guides)

    @app.route("/manager/add-guide")
    def package_manager_add_guide():
        return __import__("flask").flask.render_template("package_manager/add_guide.html")

    @app.route("/manager/edit-package/<int:package_id>")
    def package_manager_edit_package(package_id: int):
        from .models import TourismPackage
        pkg = TourismPackage.query.get_or_404(package_id)
        return __import__("flask").flask.render_template("package_manager/edit_package.html", package=pkg)

    @app.route("/manager/delete-package/<int:package_id>")
    def package_manager_delete_package(package_id: int):
        return pkg_mgr_bp.view_functions["delete_package"](package_id)

    @app.route("/manager/edit-guide/<int:guide_id>")
    def package_manager_edit_guide(guide_id: int):
        from .models import TouristGuide
        guide = TouristGuide.query.get_or_404(guide_id)
        return __import__("flask").flask.render_template("package_manager/edit_guide.html", guide=guide)

    @app.route("/manager/delete-guide/<int:guide_id>")
    def package_manager_delete_guide(guide_id: int):
        return pkg_mgr_bp.view_functions["delete_guide"](guide_id)

    return app
