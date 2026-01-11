import os
from flask import Blueprint, current_app, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_required, login_user
from werkzeug.utils import secure_filename
from extensions import db
from models.product import Product
from models.order import Order
from models.user import User
from functools import wraps

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# ---------------------------
# Admin Access Decorator
# ---------------------------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not getattr(current_user, "is_authenticated", False) or not getattr(current_user, "is_admin", False):

# ---------------------------
# Admin Dashboard
# ---------------------------
@admin_bp.route("/")
@admin_required
def dashboard():
    products = Product.query.all()
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template("admin/dashboard.html", products=products, orders=orders)

# ---------------------------
# Add Product
# ---------------------------
@admin_bp.route("/products/add", methods=["GET", "POST"])
@admin_required
def add_product():
    if request.method == "POST":
        name = request.form.get("name")
        price = float(request.form.get("price", 0))
        image = request.form.get("image", "")

        product = Product(
            name=name,
            price=price,
            image=image
        )

        db.session.add(product)
        db.session.commit()
        
        flash("Product added successfully!", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/add_product.html")

# ---------------------------
# Edit Product
# ---------------------------
@admin_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == "POST":
        product.name = request.form.get("name", product.name)
        product.price = float(request.form.get("price", product.price))
        product.image = request.form.get("image", product.image)
        db.session.commit()
        flash("Product updated successfully!", "success")
        return redirect(url_for("admin.dashboard"))
    return render_template("admin/edit_product.html", product=product)

# ---------------------------
# Order Actions
# ---------------------------
@admin_bp.route("/orders/<int:order_id>/process")
@admin_required
def process_order(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = "Processed"
    db.session.commit()
    flash("Order processed successfully!", "success")
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/orders/<int:order_id>/deliver")
@admin_required
def deliver_order(order_id):
    order = Order.query.get_or_404(order_id)
    order.delivery_status = "Delivered"
    db.session.commit()
    flash("Order marked as delivered", "success")
    return redirect(url_for("admin.dashboard"))

# ---------------------------
# Admin Login
# ---------------------------
@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()

        # Use the User model's password check helper
        if user and user.is_admin and user.check_password(password):
            login_user(user)
            return redirect(url_for("admin.dashboard"))
        else:
            flash("Invalid credentials or not an admin", "danger")
            return redirect(url_for("admin.admin_login"))

    return render_template("admin/admin_login.html")
