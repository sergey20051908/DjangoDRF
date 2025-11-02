import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_stripe_product(name: str, description: str = None, metadata: dict = None):
    data = {"name": name}
    if description:
        data["description"] = description
    if metadata:
        data["metadata"] = metadata
    product = stripe.Product.create(**data)
    return product

def create_stripe_price(product_id: str, unit_amount: int, currency: str = "usd", recurring: dict = None):
    data = {
        "product": product_id,
        "unit_amount": int(unit_amount),  # уже в центах
        "currency": currency,
    }
    if recurring:
        data["recurring"] = recurring
    price = stripe.Price.create(**data)
    return price

def create_checkout_session(price_id: str, success_url: str, cancel_url: str, customer_email: str = None):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="payment",
        success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=cancel_url,
        customer_email=customer_email,
    )
    return session