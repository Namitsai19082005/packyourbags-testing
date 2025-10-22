import os


def load_config(app):
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change")
    mysql_user = os.getenv("MYSQL_USER", "root")
    mysql_password = os.getenv("MYSQL_PASSWORD", "Namit#123")
    mysql_host = os.getenv("MYSQL_HOST", "127.0.0.1")
    mysql_port = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_db = os.getenv("MYSQL_DB", "tourism_management")

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_db}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
