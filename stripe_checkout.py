"""
Stripe Checkout integration for Claire Pro subscriptions.

Flow:
1. User clicks "Upgrade" → create_checkout_session()
2. User completes payment on Stripe
3. Stripe redirects back with ?session_id=xxx
4. App calls verify_checkout_session() to show confirmation
5. Stripe webhook → Supabase Edge Function → payments table
6. is_pro_user() reads payments table
"""

import streamlit as st
from typing import Optional

# Price: $9.99/month
PRICE_AMOUNT = 999  # cents
PRICE_CURRENCY = "usd"

# App URL for redirects (from secrets or default)
def _get_app_url():
    try:
        return st.secrets.get("APP_URL", "http://localhost:8501")
    except Exception:
        return "http://localhost:8501"


def _get_stripe():
    """Get Stripe client with secret key."""
    try:
        import stripe
        secret_key = st.secrets.get("STRIPE_SECRET_KEY")
        if not secret_key:
            print("[stripe] No STRIPE_SECRET_KEY found")
            return None
        stripe.api_key = secret_key
        return stripe
    except Exception as e:
        print(f"[stripe] Error initializing: {e}")
        return None


def create_checkout_session(user_id: str, user_email: Optional[str] = None) -> Optional[str]:
    """
    Create a Stripe Checkout session for Pro subscription.

    Args:
        user_id: Supabase user ID (stored in metadata for webhook)
        user_email: Optional email to prefill

    Returns:
        Checkout URL to redirect user to, or None on error
    """
    stripe = _get_stripe()
    if not stripe:
        return None

    try:
        # Create checkout session
        session_params = {
            "mode": "subscription",
            "payment_method_types": ["card"],
            "line_items": [{
                "price_data": {
                    "currency": PRICE_CURRENCY,
                    "unit_amount": PRICE_AMOUNT,
                    "recurring": {"interval": "month"},
                    "product_data": {
                        "name": "Claire Pro",
                        "description": "Unlimited Claude explanations + course-specific problem generation",
                    },
                },
                "quantity": 1,
            }],
            "success_url": f"{_get_app_url()}?upgraded=true&session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": _get_app_url(),
            "metadata": {
                "user_id": user_id,  # Critical: webhook uses this to update Supabase
            },
            "subscription_data": {
                "metadata": {
                    "user_id": user_id,
                },
            },
        }

        # Add email if provided
        if user_email:
            session_params["customer_email"] = user_email

        session = stripe.checkout.Session.create(**session_params)
        print(f"[stripe] Created checkout session: {session.id}")
        return session.url

    except Exception as e:
        print(f"[stripe] Error creating session: {e}")
        return None


def verify_checkout_session(session_id: str) -> dict:
    """
    Verify a checkout session after redirect.

    This is for UI feedback only - actual activation happens via webhook.

    Returns:
        {
            "status": "complete" | "pending" | "error",
            "customer_email": str | None,
            "message": str
        }
    """
    stripe = _get_stripe()
    if not stripe:
        return {"status": "error", "message": "Stripe not configured"}

    try:
        session = stripe.checkout.Session.retrieve(session_id)

        # Debug logging
        print(f"[stripe] Session {session_id[:20]}...")
        print(f"[stripe]   status={session.status}, payment_status={session.payment_status}")

        # Must be BOTH complete AND paid
        if session.status == "complete" and session.payment_status == "paid":
            return {
                "status": "complete",
                "customer_email": session.customer_details.email if session.customer_details else None,
                "message": "Payment successful! Your Pro access is being activated...",
            }
        elif session.status == "open":
            return {
                "status": "pending",
                "customer_email": None,
                "message": "Checkout not completed. Please try again.",
            }
        elif session.status == "expired":
            return {
                "status": "error",
                "customer_email": None,
                "message": "Checkout session expired. Please try again.",
            }
        else:
            # Covers: status=complete but payment_status!=paid (rare edge case)
            return {
                "status": "pending",
                "customer_email": None,
                "message": "Payment processing. Please wait or try again.",
            }

    except Exception as e:
        print(f"[stripe] Error verifying session: {e}")
        return {"status": "error", "message": "Could not verify payment status"}


def get_customer_portal_url(customer_id: str) -> Optional[str]:
    """
    Get Stripe Customer Portal URL for managing subscription.

    Args:
        customer_id: Stripe customer ID (from payments table)

    Returns:
        Portal URL or None
    """
    stripe = _get_stripe()
    if not stripe:
        return None

    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=_get_app_url(),
        )
        return session.url
    except Exception as e:
        print(f"[stripe] Error creating portal session: {e}")
        return None
