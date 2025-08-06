def calculate_lender_cashflows(original_cashflows, loan_percentage=0.80, yearly_interest_rate=0.16):
    """
    Calculate lender cash flows from a series of monthly cash flows.
    
    Args:
        original_cashflows (list): List of monthly cash flows where first is negative (investment)
        loan_percentage (float): Percentage of original cash flow to lend (default 80%)
        yearly_interest_rate (float): Yearly interest rate as decimal (default 16%)
    
    Returns:
        list: Lender cash flows
        dict: Additional information about the loan
    """
    if not original_cashflows or len(original_cashflows) < 2:
        raise ValueError("Cash flows must have at least 2 elements")
    
    if original_cashflows[0] >= 0:
        raise ValueError("First cash flow must be negative (investment)")
    
    # Calculate monthly interest rate
    monthly_interest_rate = (1 + yearly_interest_rate) ** (1/12) - 1
    
    # Initialize lender cash flows
    lender_cashflows = []
    
    # First cash flow: loan amount (negative)
    loan_amount = original_cashflows[0] * loan_percentage
    lender_cashflows.append(loan_amount)
    
    # Track outstanding principal
    outstanding_principal = abs(loan_amount)
    
    # Process remaining cash flows
    for i, original_flow in enumerate(original_cashflows[1:], 1):
        if original_flow <= 0:
            # No positive cash flow = no payment to lender (lender loses money)
            lender_cashflows.append(0)
        else:
            # Calculate maximum payment (x% of original cash flow)
            max_payment = original_flow * loan_percentage
            
            # Calculate interest on outstanding principal
            interest_payment = outstanding_principal * monthly_interest_rate
            
            # Calculate available principal payment
            available_principal_payment = max_payment - interest_payment
            
            # Principal payment cannot exceed outstanding principal
            actual_principal_payment = min(available_principal_payment, outstanding_principal)
            
            # Total payment to lender
            total_payment = interest_payment + actual_principal_payment
            
            # Update outstanding principal
            outstanding_principal -= actual_principal_payment
            
            lender_cashflows.append(total_payment)
    
    # Calculate loan metrics
    total_loan_amount = abs(loan_amount)
    total_payments = sum(lender_cashflows[1:])  # Exclude initial loan
    final_principal = outstanding_principal
    
    loan_info = {
        'loan_amount': total_loan_amount,
        'total_payments_received': total_payments,
        'final_outstanding_principal': final_principal,
        'net_return': total_payments - total_loan_amount,
        'monthly_interest_rate': monthly_interest_rate,
        'loan_percentage': loan_percentage,
        'yearly_interest_rate': yearly_interest_rate
    }
    
    return lender_cashflows, loan_info


def print_lender_analysis(original_cashflows, lender_cashflows, loan_info):
    """
    Print a detailed analysis of the lender cash flows.
    """
    print("=" * 60)
    print("LENDER CASH FLOW ANALYSIS")
    print("=" * 60)
    print(f"Loan Percentage: {loan_info['loan_percentage']*100:.1f}%")
    print(f"Yearly Interest Rate: {loan_info['yearly_interest_rate']*100:.1f}%")
    print(f"Monthly Interest Rate: {loan_info['monthly_interest_rate']*100:.4f}%")
    print(f"Initial Loan Amount: ${loan_info['loan_amount']:,.2f}")
    print(f"Total Payments Received: ${loan_info['total_payments_received']:,.2f}")
    print(f"Final Outstanding Principal: ${loan_info['final_outstanding_principal']:,.2f}")
    print(f"Net Return: ${loan_info['net_return']:,.2f}")
    print(f"Return on Investment: {(loan_info['net_return']/loan_info['loan_amount'])*100:.2f}%")
    
    print("\n" + "=" * 60)
    print("MONTHLY BREAKDOWN")
    print("=" * 60)
    print(f"{'Month':<6} {'Original':<12} {'Lender':<12} {'Outstanding':<12}")
    print("-" * 60)
    
    outstanding = abs(lender_cashflows[0])
    for i, (orig, lender) in enumerate(zip(original_cashflows, lender_cashflows)):
        if i == 0:
            print(f"{i:<6} ${orig:<11,.2f} ${lender:<11,.2f} ${outstanding:<11,.2f}")
        else:
            if lender > 0:
                outstanding -= (lender - outstanding * loan_info['monthly_interest_rate'])
            print(f"{i:<6} ${orig:<11,.2f} ${lender:<11,.2f} ${max(0, outstanding):<11,.2f}")


# Example usage and testing
if __name__ == "__main__":
    # Example cash flows: -$1000 investment, then monthly returns
    example_cashflows = [-1000, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150]
    
    print("Example: $1000 investment with monthly returns")
    print("Original cash flows:", example_cashflows)
    
    # Calculate lender cash flows with default parameters (80% loan, 16% yearly interest)
    lender_cf, info = calculate_lender_cashflows(example_cashflows)
    
    print("\nLender cash flows:", [round(cf, 2) for cf in lender_cf])
    
    # Print detailed analysis
    print_lender_analysis(example_cashflows, lender_cf, info)
    
    # Test with different parameters
    print("\n" + "=" * 60)
    print("TESTING WITH DIFFERENT PARAMETERS")
    print("=" * 60)
    
    # 70% loan, 12% yearly interest
    lender_cf2, info2 = calculate_lender_cashflows(example_cashflows, loan_percentage=0.70, yearly_interest_rate=0.12)
    print(f"\n70% loan, 12% yearly interest:")
    print(f"Net Return: ${info2['net_return']:,.2f} ({info2['net_return']/info2['loan_amount']*100:.2f}%)")
    
    # 90% loan, 20% yearly interest
    lender_cf3, info3 = calculate_lender_cashflows(example_cashflows, loan_percentage=0.90, yearly_interest_rate=0.20)
    print(f"\n90% loan, 20% yearly interest:")
    print(f"Net Return: ${info3['net_return']:,.2f} ({info3['net_return']/info3['loan_amount']*100:.2f}%)") 