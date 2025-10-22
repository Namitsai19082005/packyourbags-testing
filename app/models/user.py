from datetime import datetime
from enum import Enum
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from ..extensions.db import db


class Role(str, Enum):
    customer = "customer"
    hotel = "hotel"
    package_manager = "package_manager"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(Role), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    hotels = db.relationship("Hotel", backref="owner", cascade="all, delete-orphan")
    packages = db.relationship(
        "TourismPackage", backref="creator", cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        self.password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password, password)
