from flask import Blueprint, request, render_template, jsonify, redirect, url_for
from flask_login import login_required, current_user
from ..models import TourismPackage, Booking, Hotel, PackageGuide, TouristGuide, User
from ..extensions.db import db


customer_bp = Blueprint("customer", __name__)


@customer_bp.route("/dashboard")
@login_required
def dashboard():
    # Show a few featured packages and hotels on dashboard
    packages = TourismPackage.query.order_by(TourismPackage.created_at.desc()).limit(6).all()
    hotels = Hotel.query.order_by(Hotel.created_at.desc()).limit(6).all()

    # Enrich packages with creator name for display
    package_view_models = []
    for pkg in packages:
        creator_name = None
        if pkg.created_by:
            creator = User.query.get(pkg.created_by)
            creator_name = creator.username if creator else None
        package_view_models.append(
            {
                "id": pkg.id,
                "title": pkg.title,
                "destination": pkg.destination,
                "description": pkg.description,
                "price": pkg.price,
                "duration_days": pkg.duration_days,
                "created_by_name": creator_name or "",
            }
        )

    return render_template("customer/dashboard.html", user=current_user, packages=package_view_models, hotels=hotels)


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

    # Build view models expected by the template (includes guides and creator name)
    package_view_models = []
    for pkg in packages:
        # Fetch guides linked to this package
        associations = PackageGuide.query.filter_by(package_id=pkg.id).all()
        guide_ids = [assoc.guide_id for assoc in associations]
        guides = TouristGuide.query.filter(TouristGuide.id.in_(guide_ids)).all() if guide_ids else []
        guide_names = ", ".join([g.name for g in guides]) if guides else None
        guide_contacts = ", ".join([g.contact_info for g in guides]) if guides else None
        guide_rates = ", ".join([f"{float(g.rate_per_day):.2f}" for g in guides]) if guides else None

        creator_name = None
        if pkg.created_by:
            creator = User.query.get(pkg.created_by)
            creator_name = creator.username if creator else None

        package_view_models.append(
            {
                "id": pkg.id,
                "title": pkg.title,
                "destination": pkg.destination,
                "description": pkg.description,
                "price": pkg.price,
                "duration_days": pkg.duration_days,
                "guide_names": guide_names,
                "guide_contacts": guide_contacts,
                "guide_rates": guide_rates,
                "created_by_name": creator_name or "",
                "created_at": pkg.created_at,
            }
        )

    return render_template("customer/packages.html", packages=package_view_models)


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
