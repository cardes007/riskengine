from lender_cashflow_calculator import calculate_lender_cashflows
import numpy as np
from numpy_financial import irr

def test_irr_verification():
    """Test that IRR of lender cash flows equals the yearly interest rate"""
    
    # Test cases with different interest rates
    test_cases = [
        (0.12, "12% yearly interest"),
        (0.16, "16% yearly interest"), 
        (0.20, "20% yearly interest"),
        (0.25, "25% yearly interest")
    ]
    
    # Simple cash flow: -$1000 investment, then $100/month for 12 months
    original_cashflows = [-1000] + [100] * 12
    
    print("Testing IRR verification for lender cash flows")
    print("=" * 60)
    print(f"Original cash flows: {original_cashflows}")
    print()
    
    for yearly_rate, description in test_cases:
        print(f"Testing {description}")
        print("-" * 40)
        
        # Calculate lender cash flows
        lender_cf, info = calculate_lender_cashflows(original_cashflows, 
                                                   loan_percentage=0.80, 
                                                   yearly_interest_rate=yearly_rate)
        
        # Calculate IRR of lender cash flows
        try:
            calculated_irr = irr(lender_cf)
            if calculated_irr is not None and np.isfinite(calculated_irr):
                # Convert monthly IRR to yearly IRR
                yearly_irr = (1 + calculated_irr) ** 12 - 1
                
                print(f"Expected yearly rate: {yearly_rate:.4f} ({yearly_rate*100:.1f}%)")
                print(f"Calculated yearly IRR: {yearly_irr:.4f} ({yearly_irr*100:.1f}%)")
                print(f"Difference: {abs(yearly_irr - yearly_rate):.6f}")
                print(f"Match: {'✅' if abs(yearly_irr - yearly_rate) < 0.001 else '❌'}")
            else:
                print(f"❌ IRR calculation failed")
        except Exception as e:
            print(f"❌ Error calculating IRR: {e}")
        
        print(f"Lender cash flows: {[round(cf, 2) for cf in lender_cf]}")
        print(f"Net return: ${info['net_return']:.2f} ({info['net_return']/info['loan_amount']*100:.2f}%)")
        print()

if __name__ == "__main__":
    test_irr_verification() 