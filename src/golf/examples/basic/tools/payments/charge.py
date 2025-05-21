"""Charge payment tool"""

from pydantic import BaseModel
from .common import payment_client


class Output(BaseModel):
    """Response from the charge payment tool."""
    
    success: bool
    charge_id: str
    message: str


async def charge(
    amount: float,
    card_token: str,
    description: str = ""
) -> Output:
    """Process a payment charge.
    
    This example demonstrates nested directory organization where related tools
    are grouped in subdirectories (tools/payments/charge.py).
    
    The resulting tool ID will be: charge-payments
    
    Args:
        amount: Amount to charge in USD
        card_token: Tokenized payment card
        description: Optional payment description
    """
    # The framework will add a context object automatically
    # You can log using regular print during development
    print(f"Processing charge for ${amount:.2f}...")
    
    # Use the shared payment client from common.py
    charge_result = await payment_client.create_charge(
        amount=amount,
        token=card_token,
        description=description
    )
    
    # Create and return the response
    return Output(
        success=True,
        charge_id=charge_result["id"],
        message=f"Successfully charged ${amount:.2f}"
    ) 

export = charge