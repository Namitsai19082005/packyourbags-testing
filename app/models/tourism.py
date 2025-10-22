from datetime import datetime
from ..extensions.db import db


class TourismPackage(db.Model):
    __tablename__ = "tourism_packages"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    duration_days = db.Column(db.Integer)
    created_by = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    guides = db.relationship(
        "PackageGuide", backref="package", cascade="all, delete-orphan"
    )


class TouristGuide(db.Model):
    __tablename__ = "tourist_guides"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_info = db.Column(db.String(100), nullable=False)
    rate_per_day = db.Column(db.Numeric(10, 2), nullable=False)
    specialization = db.Column(db.String(100))
    experience_years = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PackageGuide(db.Model):
    __tablename__ = "package_guides"

    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(
        db.Integer, db.ForeignKey("tourism_packages.id", ondelete="CASCADE")
    )
    guide_id = db.Column(
        db.Integer, db.ForeignKey("tourist_guides.id", ondelete="CASCADE")
    )
