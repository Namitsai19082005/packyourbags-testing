from datetime import datetime
from ..extensions.db import db


class Hotel(db.Model):
    __tablename__ = "hotels"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"))
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    contact_info = db.Column(db.String(100))
    amenities = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    hotel_packages = db.relationship(
        "HotelPackage", backref="hotel", cascade="all, delete-orphan"
    )


class HotelPackage(db.Model):
    __tablename__ = "hotel_packages"

    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(
        db.Integer, db.ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False
    )
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    amenities = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
