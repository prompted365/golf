"""Refund payment tool"""

from pydantic import BaseModel
from .common import payment_client


class Output(BaseModel):
    """Response from the refund payment tool."""
    
    success: bool
    refund_id: str
    message: str


async def refund(
    charge_id: str,
    amount: float,
    reason: str = "customer_request"
) -> Output:
    """Process a payment refund.
    
    This example demonstrates nested directory organization where related tools
    are grouped in subdirectories (tools/payments/refund.py).
    
    The resulting tool ID will be: refund-payments
    
    Args:
        charge_id: Original charge ID to refund
        amount: Amount to refund in USD
        reason: Reason for refund
    """
    # The framework will add a context object automatically
    # You can log using regular print during development
    print(f"Processing refund of ${amount:.2f} for charge {charge_id}...")
    
    # Use the shared payment client from common.py
    refund_result = await payment_client.create_refund(
        charge_id=charge_id,
        amount=amount,
        reason=reason
    )
    
    # Create and return the response
    return Output(
        success=True,
        refund_id=refund_result["id"],
        message=f"Successfully refunded ${amount:.2f}"
    ) 

export = refund