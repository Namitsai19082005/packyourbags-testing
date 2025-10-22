from flask_sqlalchemy import SQLAlchemy

# Global SQLAlchemy instance
# Imported by models and initialized in app factory

db = SQLAlchemy()