from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from ..extensions.db import db
from ..models import Role, TourismPackage, TouristGuide, PackageGuide


pkg_mgr_bp = Blueprint("pkg_mgr", __name__)


def require_package_manager():
    return current_user.is_authenticated and current_user.role == Role.package_manager


@pkg_mgr_bp.before_request
def ensure_pkg_role():
    if request.path.startswith("/manager") and request.method != "GET":
        if not require_package_manager():
            return redirect(url_for("auth.login"))


@pkg_mgr_bp.route("/dashboard")
@login_required
def dashboard():
    if not require_package_manager():
        return redirect(url_for("auth.post_login_redirect"))
    packages = TourismPackage.query.filter_by(created_by=current_user.id).all()
    guides = TouristGuide.query.order_by(TouristGuide.created_at.desc()).all()
    return render_template("package_manager/dashboard.html", packages=packages, guides=guides)


@pkg_mgr_bp.route("/package", methods=["POST"])
@login_required
def create_package():
    if not require_package_manager():
        return {"error": "Unauthorized"}, 403
    data = request.form if request.form else (request.json or {})
    pkg = TourismPackage(
        title=data.get("title"),
        destination=data.get("destination"),
        description=data.get("description"),
        price=data.get("price"),
        duration_days=data.get("duration_days"),
        created_by=current_user.id,
    )
    db.session.add(pkg)
    db.session.flush()

    # Optionally attach guides from form checkbox list
    guide_ids = request.form.getlist("guide_ids") if request.form else []
    for gid in guide_ids:
        try:
            assoc = PackageGuide(package_id=pkg.id, guide_id=int(gid))
            db.session.add(assoc)
        except ValueError:
            continue

    db.session.commit()
    flash("Package created.", "success")
    return redirect(url_for("pkg_mgr.dashboard"))


@pkg_mgr_bp.route("/package/<int:package_id>", methods=["PUT", "PATCH"])
@login_required
def update_package(package_id):
    if not require_package_manager():
        return {"error": "Unauthorized"}, 403
    pkg = TourismPackage.query.filter_by(id=package_id, created_by=current_user.id).first_or_404()
    data = request.form if request.form else (request.json or {})
    for field in ["title", "destination", "description", "price", "duration_days"]:
        if field in data and data.get(field) is not None:
            setattr(pkg, field, data.get(field))
    db.session.commit()
    return {"message": "Package updated"}


@pkg_mgr_bp.route("/package/<int:package_id>", methods=["DELETE"])
@login_required
def delete_package(package_id):
    if not require_package_manager():
        return {"error": "Unauthorized"}, 403
    pkg = TourismPackage.query.filter_by(id=package_id, created_by=current_user.id).first_or_404()
    db.session.delete(pkg)
    db.session.commit()
    return {"message": "Package deleted"}


@pkg_mgr_bp.route("/guide", methods=["POST"])
@login_required
def create_guide():
    if not require_package_manager():
        return {"error": "Unauthorized"}, 403
    data = request.form if request.form else (request.json or {})
    guide = TouristGuide(
        name=data.get("name"),
        contact_info=data.get("contact_info"),
        rate_per_day=data.get("rate_per_day"),
        specialization=data.get("specialization"),
        experience_years=data.get("experience_years"),
    )
    db.session.add(guide)
    db.session.commit()
    flash("Guide created.", "success")
    return redirect(url_for("pkg_mgr.dashboard"))


@pkg_mgr_bp.route("/guide/<int:guide_id>", methods=["PUT", "PATCH"])
@login_required
def update_guide(guide_id):
    if not require_package_manager():
        return {"error": "Unauthorized"}, 403
    guide = TouristGuide.query.get_or_404(guide_id)
    data = request.form if request.form else (request.json or {})
    for field in ["name", "contact_info", "rate_per_day", "specialization", "experience_years"]:
        if field in data and data.get(field) is not None:
            setattr(guide, field, data.get(field))
    db.session.commit()
    return {"message": "Guide updated"}


@pkg_mgr_bp.route("/guide/<int:guide_id>", methods=["DELETE"])
@login_required
def delete_guide(guide_id):
    if not require_package_manager():
        return {"error": "Unauthorized"}, 403
    guide = TouristGuide.query.get_or_404(guide_id)
    db.session.delete(guide)
    db.session.commit()
    return {"message": "Guide deleted"}


@pkg_mgr_bp.route("/package/<int:package_id>/guides", methods=["POST"])
@login_required
def attach_guide(package_id):
    if not require_package_manager():
        return {"error": "Unauthorized"}, 403
    pkg = TourismPackage.query.filter_by(id=package_id, created_by=current_user.id).first_or_404()
    data = request.form if request.form else (request.json or {})
    guide_id = data.get("guide_id")
    if not guide_id:
        return {"error": "guide_id required"}, 400
    assoc = PackageGuide(package_id=pkg.id, guide_id=int(guide_id))
    db.session.add(assoc)
    db.session.commit()
    return {"message": "Guide attached"}


@pkg_mgr_bp.route("/package/<int:package_id>/guides/<int:guide_id>", methods=["DELETE"])
@login_required
def detach_guide(package_id, guide_id):
    if not require_package_manager():
        return {"error": "Unauthorized"}, 403
    assoc = PackageGuide.query.filter_by(package_id=package_id, guide_id=guide_id).first_or_404()
    db.session.delete(assoc)
    db.session.commit()
    return {"message": "Guide detached"}
