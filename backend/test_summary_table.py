#!/usr/bin/env python3

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from transform_to_lender_cashflows import create_summary_table

print("Testing create_summary_table function...")
print(f"Current working directory: {os.getcwd()}")
print(f"Files in current directory: {os.listdir('.')}")

result = create_summary_table()
print(f"Result: {result}")

if result:
    print(f"Summary table created: {result}")
    print(f"File exists: {os.path.exists(result)}")
else:
    print("Summary table creation failed") 