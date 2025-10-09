from typing import Dict, Optional
from datetime import datetime
import razorpay
from fastapi import HTTPException, status
from .config import settings


class PaymentService:
    def __init__(self):
        self.razorpay_client = razorpay.Client(
            auth=(
                settings.RAZORPAY_KEY_ID,
                settings.RAZORPAY_KEY_SECRET,
            )
        )

    def create_razorpay_order(
        self, username: str, email: str, product: str, amount: float
    ) -> Dict:
        """
        Creates an order in Razorpay and returns order info.
        Raises HTTPException on failure.
        """
        try:
            parsed_amount = float(amount)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amount must be a number",
            )

        if parsed_amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amount must be greater than zero",
            )

        total_amount = int(parsed_amount * 100)

        options = {
            "amount": total_amount,
            "currency": "INR",
            "receipt": str(email),
            "payment_capture": 1,
            "notes": {
                "product_name": product,
                "username": username,
                "email": email,
            },
        }

        try:
            order = self.razorpay_client.order.create(data=options)
        except Exception as e:
            print("Error creating order:", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create Razorpay order",
            )

        if not order or not order.get("id"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order creation failed",
            )

        return {
            "order_id": order["id"],
            "amount": order["amount"],
            "receipt": order.get("receipt"),
            "currency": order.get("currency"),
            "notes": order.get("notes", {}),
        }

    async def create_order(
        self,
        amount: float,
        currency: str = "INR",
        receipt: Optional[str] = None,
        notes: Optional[Dict] = None,
    ) -> Dict:
        """
        Creates a mock order (useful for testing without Razorpay)
        """
        try:
            order = {
                "order_id": f"ORDER_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "amount": amount,
                "currency": currency,
                "status": "created",
                "created_at": datetime.now().isoformat(),
                "receipt": receipt,
                "notes": notes or {},
            }
            return order
        except Exception as e:
            print(f"Error creating test order: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create mock order",
            )

    async def verify_payment(
        self, payment_id: str, order_id: str, signature: str
    ) -> bool:
        """
        Verify Razorpay payment signature
        """
        try:
            params_dict = {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            }

            self.razorpay_client.utility.verify_payment_signature(params_dict)
            return True
        except razorpay.errors.SignatureVerificationError:
            return False
        except Exception as e:
            print(f"Payment verification failed: {str(e)}")
            return False

    async def create_razorpay_refund(
        self, payment_id: str, amount_float: float, notes: dict = None
    ):
        if not payment_id:
            raise HTTPException(
                status_code=400, detail="No payment id provided for refund"
            )

        try:
            amount_paise = int(round(amount_float * 100))

            payload = {"amount": amount_paise}
            if notes:
                payload["notes"] = notes

            refund_resp = self.razorpay_client.payment.refund(payment_id, payload)
            return refund_resp
        except razorpay.errors.BadRequestError as e:
            raise HTTPException(
                status_code=400, detail=f"Razorpay bad request: {str(e)}"
            )
        except razorpay.errors.ServerError as e:
            raise HTTPException(
                status_code=502, detail=f"Razorpay server error: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to create refund: {str(e)}"
            )