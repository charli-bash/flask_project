import os


class Config:
    # -------------------
    # Core
    # -------------------
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "this-is-a-secret"
    )

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///site.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # -------------------
    # Uploads
    # -------------------
    UPLOAD_FOLDER = "static/uploads"
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

    # -------------------
    # Paystack
    # -------------------
    PAYSTACK_SECRET_KEY = os.getenv(
        "PAYSTACK_SECRET_KEY",
        "sk_test_xxxxx"
    )

    # -------------------
    # OPay
    # -------------------
    OPAY_MERCHANT_ID = os.getenv("OPAY_MERCHANT_ID")
    OPAY_API_KEY = os.getenv("OPAY_API_KEY")
