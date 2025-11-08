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

decorator = dataclass
@decorator
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
        Returns 0.0 if calculation fails or result is unreasonable

    Note:
        For very short time periods with losses, XIRR can approach -100% due to annualization.
        The function caps results at -0.999 (-99.9%) to avoid numerical instability.
    """
    if len(cash_flows) < 2:
        return 0.0  # Return 0 if not enough cash flows

    # Check for zero-day scenario (all cash flows on same date)
    unique_dates = set(cf[0] for cf in cash_flows)
    if len(unique_dates) == 1:
        return 0.0  # Cannot calculate XIRR for same-day transactions

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
        # Verify the result is close to zero
        if abs(xirr_equation(result)) < 1e-4:
            # Ensure result is reasonable (between -0.999 and 10)
            # Cap at -0.999 to avoid numerical instability near -100%
            if result >= -0.999 and result <= 10:
                return max(result, -0.999)  # Cap minimum at -99.9%
    except Exception as e:
        pass  # Fall through to broader search

    # If initial guess fails, try a broader search with both positive AND negative guesses
    # FIX: Include negative guesses for loss scenarios
    guess_list = [
        # Extreme negative returns (near -100%)
        -0.995, -0.99, -0.98, -0.97, -0.95, -0.93, -0.90, -0.85, -0.80, -0.75, -0.70, -0.65,
        # Moderate negative returns
        -0.60, -0.55, -0.50, -0.45, -0.40, -0.35, -0.30, -0.25, -0.20, -0.15, -0.10, -0.05, -0.01,
        # Small movements
        0.0, 0.01,
        # Positive returns (gains)
        0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 8.0
    ]

    for g in guess_list:
        try:
            result = newton(xirr_equation, g, fprime=xirr_derivative, tol=1e-6, maxiter=200)
            # Verify the result is actually a solution
            if abs(xirr_equation(result)) < 1e-3:  # Slightly relaxed tolerance
                # Ensure result is reasonable
                # Cap at -0.999 to avoid numerical instability
                if result >= -0.999 and result <= 10:
                    return max(result, -0.999)  # Cap minimum at -99.9%
        except:
            continue

    # If all guesses fail, return 0.0 as last resort
    return 0.0

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
        result = xirr(cash_flows)
        # Ensure result is reasonable
        if result < -1 or result > 10:
            return 0.0
        return result
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
        result = xirr(all_transactions)
        # Ensure result is reasonable
        if result < -1 or result > 10:
            return 0.0
        return result
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