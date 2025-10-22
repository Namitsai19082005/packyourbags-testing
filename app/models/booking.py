from datetime import datetime
from ..extensions.db import db


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    package_id = db.Column(
        db.Integer, db.ForeignKey("tourism_packages.id", ondelete="CASCADE"), nullable=False
    )
    status = db.Column(db.String(20), default="pending")
    booked_at = db.Column(db.DateTime, default=datetime.utcnow)
