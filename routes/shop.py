from flask import Blueprint, render_template, redirect, url_for, session, flash, g, current_app, has_request_context
from flask_login import current_user, login_required
from models.product import Product
from models.cart import Cart, CartItem
from models.order import Order, OrderItem
from extensions import db
import requests  # move import to top

shop_bp = Blueprint('shop', __name__)

# ---------------------------
# Home / Products
# ---------------------------
@shop_bp.route('/')
def index():
    products = Product.query.all()
    return render_template('shop/index.html', products=products)

# ---------------------------
# Add to Cart
# ---------------------------
@shop_bp.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if current_user.is_authenticated:
        cart = Cart.query.filter_by(user_id=current_user.id).first()
        if not cart:
            cart = Cart(user_id=current_user.id)
            db.session.add(cart)
            db.session.commit()

        item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
        if item:
            item.quantity += 1
        else:
            item = CartItem(cart_id=cart.id, product_id=product_id, quantity=1)
            db.session.add(item)
        db.session.commit()
    else:
        cart = session.get("cart", {})
        cart[str(product_id)] = cart.get(str(product_id), 0) + 1
        session["cart"] = cart

    flash("Item added to cart", "success")
    return redirect(url_for("shop.index"))

# ---------------------------
# View Cart
# ---------------------------
@shop_bp.before_app_request
def load_cart_count():
    g.cart_count = 0
    if not has_request_context() or not hasattr(current_user, "is_authenticated"):
        return  # Skip if no active request or user object missing

    if current_user.is_authenticated:
        cart = Cart.query.filter_by(user_id=current_user.id).first()
        if cart:
            g.cart_count = sum(item.quantity for item in cart.items)
    else:
        session_cart = session.get("cart", {})
        g.cart_count = sum(session_cart.values())
@shop_bp.route('/cart')
def cart():
    products_in_cart = []
    total = 0

    if current_user.is_authenticated:
        cart = Cart.query.filter_by(user_id=current_user.id).first()
        if cart:
            for item in cart.items:
                products_in_cart.append({
                    "product": item.product,
                    "quantity": item.quantity
                })
                total += item.product.price * item.quantity
    else:
        session_cart = session.get("cart", {})
        for product_id, qty in session_cart.items():
            product = Product.query.get(int(product_id))
            if product:
                products_in_cart.append({
                    "product": product,
                    "quantity": qty
                })
                total += product.price * qty

    return render_template("shop/cart.html", products=products_in_cart, total=total)

# ---------------------------
# Load Cart Count for Navbar
# ---------------------------
@shop_bp.before_app_request
def load_cart_count():
    g.cart_count = 0
    if not has_request_context():
        return  # Skip if no active request

    if current_user.is_authenticated:
        cart = Cart.query.filter_by(user_id=current_user.id).first()
        if cart:
            g.cart_count = sum(item.quantity for item in cart.items)
    else:
        session_cart = session.get("cart", {})
        g.cart_count = sum(session_cart.values())

# ---------------------------
# Remove Item from Cart
# ---------------------------
@shop_bp.route('/remove_from_cart/<int:product_id>')
@login_required
def remove_from_cart(product_id):
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if cart:
        item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
        if item:
            db.session.delete(item)
            db.session.commit()
            flash("Product removed from cart!", "info")
    return redirect(url_for('shop.cart'))

# ---------------------------
# Checkout
# ---------------------------
@shop_bp.route('/checkout')
@login_required
def checkout():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart or not cart.items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for('shop.index'))

    order = Order(user_id=current_user.id, total_amount=0)
    db.session.add(order)
    db.session.commit()

    total = 0
    for item in cart.items:
        total += item.product.price * item.quantity
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product.id,
            quantity=item.quantity,
            price=item.product.price
        )
        db.session.add(order_item)
        db.session.delete(item)

    order.total_amount = total
    db.session.commit()
    flash("Checkout complete! Your order has been placed.", "success")
    return redirect(url_for('shop.orders'))

# ---------------------------
# User Orders
# ---------------------------
@shop_bp.route('/orders')
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('shop/orders.html', orders=user_orders)

# ---------------------------
# Opay Payment
# ---------------------------
@shop_bp.route('/pay/<int:order_id>')
@login_required
def pay(order_id):
    order = Order.query.get_or_404(order_id)

    merchant_id = current_app.config.get('OPAY_MERCHANT_ID')
    api_key = current_app.config.get('OPAY_API_KEY')

    if not merchant_id or not api_key:
        flash("Payment configuration missing.", "danger")
        return redirect(url_for('shop.orders'))

    payload = {
        "merchant_id": merchant_id,
        "amount": int(order.total_amount * 100),
        "currency": "NGN",
        "callback_url": url_for('shop.verify_payment', order_id=order.id, _external=True),
        "customer_email": current_user.email
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post("https://api.opay.com/payment/initiate", json=payload, headers=headers)
        data = response.json()

        if data.get("status") == "success":
            return redirect(data["payment_url"])
        else:
            flash("Payment initialization failed.", "danger")
    except Exception as e:
        flash(f"Payment error: {str(e)}", "danger")

    return redirect(url_for('shop.orders'))

# ---------------------------
# Verify Payment (Opay Callback)
# ---------------------------
@shop_bp.route('/verify_payment/<int:order_id>')
@login_required
def verify_payment(order_id):
    order = Order.query.get_or_404(order_id)

    # For now, mark order as paid for testing
    order.status = "Paid"
    db.session.commit()
    flash("Payment successful!", "success")
    return redirect(url_for('shop.orders'))
