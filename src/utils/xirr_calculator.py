"""
XIRR Calculator for Investment Returns

This module implements the XIRR (Extended Internal Rate of Return) calculation,
which is used to measure the performance of investments with irregular cash flows
occurring at irregular intervals.
"""
from datetime import datetime, date
from typing import List, Tuple, Union
import numpy as np
from scipy.optimize import newton
from dataclasses import dataclass
from enum import Enum


class TransactionType(Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class Transaction:
    """Represents a buy/sell transaction"""
    date: Union[datetime, date]
    amount: float  # Positive for sell (cash inflow), negative for buy (cash outflow)
    transaction_type: TransactionType


def xirr(cash_flows: List[Tuple[Union[datetime, date], float]], guess: float = 0.1) -> float:
    """
    Calculate XIRR (Extended Internal Rate of Return) for a series of cash flows
    
    Args:
        cash_flows: List of tuples (date, amount) where:
            - date: Date of the cash flow
            - amount: Cash flow amount (negative for outflows/purchases, positive for inflows/sales)
        guess: Initial guess for the XIRR rate (default 0.1 or 10%)
    
    Returns:
        XIRR as a decimal value (e.g., 0.1234 for 12.34%)
    """
    if len(cash_flows) < 2:
        raise ValueError("At least two cash flows are required for XIRR calculation")
    
    # Sort cash flows by date
    sorted_flows = sorted(cash_flows, key=lambda x: x[0])
    
    # Convert dates to days since the first date
    start_date = sorted_flows[0][0]
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    
    # Calculate days from start date for each cash flow
    days_list = []
    amounts_list = []
    
    for cf_date, amount in sorted_flows:
        if isinstance(cf_date, datetime):
            cf_date = cf_date.date()
        days = (cf_date - start_date).days
        days_list.append(days)
        amounts_list.append(amount)
    
    # Convert to numpy arrays
    days = np.array(days_list)
    amounts = np.array(amounts_list)
    
    # Define the XIRR equation: sum of CF / (1 + rate)^(days/365.25) = 0
    def xirr_equation(rate):
        return np.sum(amounts / np.power(1 + rate, days / 365.25))
    
    # Define the derivative for Newton's method
    def xirr_derivative(rate):
        return np.sum(-days * amounts / (365.25 * np.power(1 + rate, (days / 365.25) + 1)))
    
    try:
        # Use Newton's method to find the rate that makes the equation equal to 0
        result = newton(xirr_equation, guess, fprime=xirr_derivative, tol=1e-6, maxiter=100)
        return result
    except Exception as e:
        # If Newton's method fails, try a broader search
        try:
            # Try with different initial guesses
            for g in [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.5, 1.0]:
                try:
                    result = newton(xirr_equation, g, fprime=xirr_derivative, tol=1e-6, maxiter=100)
                    if abs(xirr_equation(result)) < 1e-4:  # Verify the result
                        return result
                except:
                    continue
            # If all guesses fail, return NaN
            return float('nan')
        except:
            return float('nan')


def calculate_position_xirr(transactions: List[Transaction], current_value: float, current_date: Union[datetime, date]) -> float:
    """
    Calculate XIRR for a specific stock position based on all transactions
    
    Args:
        transactions: List of buy/sell transactions for this position
        current_value: Current market value of the position
        current_date: Current date to use as the end point
    
    Returns:
        XIRR as a decimal value
    """
    if not transactions:
        return 0.0
    
    # Create cash flows from transactions
    # Buys are negative cash flows, sells are positive
    cash_flows = []
    
    for transaction in transactions:
        if transaction.transaction_type == TransactionType.BUY:
            # For buy, it's a cash outflow (negative)
            amount = -abs(transaction.amount)  # Ensure it's negative
        else:  # SELL
            # For sell, it's a cash inflow (positive)
            amount = abs(transaction.amount)  # Ensure it's positive
        
        cash_flows.append((transaction.date, amount))
    
    # Add current value as a positive cash flow
    cash_flows.append((current_date, current_value))
    
    # Calculate XIRR
    try:
        return xirr(cash_flows)
    except:
        return 0.0  # Return 0 if calculation fails


def calculate_portfolio_xirr(transactions: List[Tuple[Union[datetime, date], float]], current_value: float, current_date: Union[datetime, date]) -> float:
    """
    Calculate XIRR for the entire portfolio
    """
    if not transactions:
        return 0.0
    
    # Add current portfolio value as the final cash flow
    all_transactions = list(transactions)
    all_transactions.append((current_date, current_value))
    
    try:
        return xirr(all_transactions)
    except:
        return 0.0


# Example usage and test function
def demo_xirr_calculation():
    """
    Demonstrate XIRR calculation with example data
    """
    # Example: Investment of ₹1,00,000 on Jan 1, 2023
    # Dividend received of ₹5,000 on June 1, 2023
    # Additional investment of ₹50,000 on Oct 1, 2023
    # Current value of ₹1,80,000 on Jan 1, 2024
    from datetime import datetime
    
    cash_flows = [
        (datetime(2023, 1, 1), -100000),  # Investment
        (datetime(2023, 6, 1), 5000),     # Dividend received
        (datetime(2023, 10, 1), -50000),  # Additional investment
        (datetime(2024, 1, 1), 180000),   # Current value
    ]
    
    xirr_result = xirr(cash_flows)
    print(f"XIRR: {xirr_result:.4f} ({xirr_result*100:.2f}%)")
    
    return xirr_result


if __name__ == "__main__":
    demo_xirr_calculation()