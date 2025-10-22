from flask import Blueprint, request, render_template, jsonify, redirect, url_for
from flask_login import login_required, current_user
from ..models import TourismPackage, Booking, Hotel
from ..extensions.db import db


customer_bp = Blueprint("customer", __name__)


@customer_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("customer/dashboard.html", user=current_user)


@customer_bp.route("/packages", methods=["GET"])
@login_required
def list_packages():
    q = request.args.get("q")
    query = TourismPackage.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            (TourismPackage.title.ilike(like))
            | (TourismPackage.destination.ilike(like))
            | (TourismPackage.description.ilike(like))
        )
    packages = query.order_by(TourismPackage.created_at.desc()).all()
    return render_template("customer/packages.html", packages=packages)


@customer_bp.route("/api/packages", methods=["GET"])
@login_required
def api_packages():
    q = request.args.get("q")
    query = TourismPackage.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            (TourismPackage.title.ilike(like))
            | (TourismPackage.destination.ilike(like))
            | (TourismPackage.description.ilike(like))
        )
    packages = query.order_by(TourismPackage.created_at.desc()).all()
    return jsonify(
        [
            {
                "id": p.id,
                "title": p.title,
                "destination": p.destination,
                "description": p.description,
                "price": float(p.price),
                "duration_days": p.duration_days,
            }
            for p in packages
        ]
    )


@customer_bp.route("/book", methods=["POST"])
@login_required
def book_package():
    package_id = request.form.get("package_id") or (request.json or {}).get("package_id")
    if not package_id:
        return {"error": "package_id is required"}, 400
    package = TourismPackage.query.get(package_id)
    if not package:
        return {"error": "Package not found"}, 404
    booking = Booking(user_id=current_user.id, package_id=package.id, status="pending")
    db.session.add(booking)
    db.session.commit()
    return {"message": "Booked successfully", "booking_id": booking.id}


@customer_bp.route("/search-hotels")
@login_required
def search_hotels():
    location = request.args.get("location", "")
    hotels = []
    if location:
        like = f"%{location}%"
        hotels = Hotel.query.filter(Hotel.location.ilike(like)).order_by(Hotel.created_at.desc()).all()
    return render_template(
        "customer/search_hotels.html",
        hotels=hotels,
        search_location=location,
    )


# Aliases to match template endpoint names
@customer_bp.app_url_value_preprocessor
def _noop(endpoint, values):
    pass
