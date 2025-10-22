from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from ..extensions.db import db
from ..models import Role, Hotel, HotelPackage


hotel_bp = Blueprint("hotel", __name__)


def require_hotel_manager():
    return current_user.is_authenticated and current_user.role == Role.hotel


@hotel_bp.before_request
def ensure_hotel_role():
    # Allow public access to non-modifying endpoints if desired
    protected_paths = {"/hotel/dashboard", "/hotel/packages", "/hotel/package", "/hotel/hotel"}
    if request.path.startswith("/hotel") and request.method != "GET":
        if not require_hotel_manager():
            return redirect(url_for("auth.login"))


@hotel_bp.route("/dashboard")
@login_required
def dashboard():
    if not require_hotel_manager():
        return redirect(url_for("auth.post_login_redirect"))
    hotel = Hotel.query.filter_by(user_id=current_user.id).first()
    if not hotel:
        # Auto-provision a placeholder hotel to satisfy templates
        hotel = Hotel(
            user_id=current_user.id,
            name=f"{current_user.username}'s Hotel",
            location="",
            description="",
            contact_info="",
            amenities="",
        )
        db.session.add(hotel)
        db.session.commit()
    packages = []
    if hotel:
        packages = HotelPackage.query.filter_by(hotel_id=hotel.id).all()
    return render_template("hotel/dashboard.html", hotel=hotel, packages=packages)


@hotel_bp.route("/hotel", methods=["POST"])
@login_required
def create_hotel():
    if not require_hotel_manager():
        return {"error": "Unauthorized"}, 403
    data = request.form if request.form else (request.json or {})
    hotel = Hotel(
        user_id=current_user.id,
        name=data.get("name"),
        location=data.get("location"),
        description=data.get("description"),
        contact_info=data.get("contact_info"),
        amenities=data.get("amenities"),
    )
    db.session.add(hotel)
    db.session.commit()
    flash("Hotel created.", "success")
    return redirect(url_for("hotel.dashboard"))


@hotel_bp.route("/hotel/<int:hotel_id>", methods=["PUT", "PATCH"])
@login_required
def update_hotel(hotel_id):
    if not require_hotel_manager():
        return {"error": "Unauthorized"}, 403
    hotel = Hotel.query.filter_by(id=hotel_id, user_id=current_user.id).first_or_404()
    data = request.form if request.form else (request.json or {})
    for field in ["name", "location", "description", "contact_info", "amenities"]:
        if field in data and data.get(field) is not None:
            setattr(hotel, field, data.get(field))
    db.session.commit()
    return {"message": "Hotel updated"}


@hotel_bp.route("/hotel/<int:hotel_id>", methods=["DELETE"])
@login_required
def delete_hotel(hotel_id):
    if not require_hotel_manager():
        return {"error": "Unauthorized"}, 403
    hotel = Hotel.query.filter_by(id=hotel_id, user_id=current_user.id).first_or_404()
    db.session.delete(hotel)
    db.session.commit()
    return {"message": "Hotel deleted"}


@hotel_bp.route("/packages")
@login_required
def list_packages():
    if not require_hotel_manager():
        return redirect(url_for("auth.post_login_redirect"))
    hotel = Hotel.query.filter_by(user_id=current_user.id).first()
    packages = []
    if hotel:
        packages = HotelPackage.query.filter_by(hotel_id=hotel.id).all()
    return render_template("hotel/dashboard.html", hotel=hotel, packages=packages)


@hotel_bp.route("/package", methods=["POST"])
@login_required
def create_hotel_package():
    if not require_hotel_manager():
        return {"error": "Unauthorized"}, 403
    data = request.form if request.form else (request.json or {})
    package = HotelPackage(
        hotel_id=int(data.get("hotel_id")),
        title=data.get("title"),
        description=data.get("description"),
        price=data.get("price"),
        amenities=data.get("amenities"),
    )
    db.session.add(package)
    db.session.commit()
    flash("Hotel package created.", "success")
    return redirect(url_for("hotel.dashboard"))


@hotel_bp.route("/package/<int:package_id>", methods=["PUT", "PATCH"])
@login_required
def update_hotel_package(package_id):
    if not require_hotel_manager():
        return {"error": "Unauthorized"}, 403
    pkg = (
        HotelPackage.query.join(Hotel, HotelPackage.hotel_id == Hotel.id)
        .filter(HotelPackage.id == package_id, Hotel.user_id == current_user.id)
        .first_or_404()
    )
    data = request.form if request.form else (request.json or {})
    for field in ["title", "description", "price", "amenities"]:
        if field in data and data.get(field) is not None:
            setattr(pkg, field, data.get(field))
    db.session.commit()
    return {"message": "Hotel package updated"}


@hotel_bp.route("/package/<int:package_id>", methods=["DELETE"])
@login_required
def delete_hotel_package(package_id):
    if not require_hotel_manager():
        return {"error": "Unauthorized"}, 403
    pkg = (
        HotelPackage.query.join(Hotel, HotelPackage.hotel_id == Hotel.id)
        .filter(HotelPackage.id == package_id, Hotel.user_id == current_user.id)
        .first_or_404()
    )
    db.session.delete(pkg)
    db.session.commit()
    return {"message": "Hotel package deleted"}
