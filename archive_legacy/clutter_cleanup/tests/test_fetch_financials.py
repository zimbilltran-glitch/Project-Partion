import pytest
import pandas as pd
import sys
import os

# Setup sys.path so we can import fetch_financials from tools/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools.fetch_financials import transform_kbs

def test_transform_kbs_cyclic_hierarchy():
    """
    Test CTO Debt 1: Ensure that a cyclic mapping in the KBSV API response
    does not cause an infinite recursion loop (RecursionError).
    """
    head = [{"YearPeriod": 2024, "TermCode": 1}]
    # Simulate a corrupted API response where item 3 loops back to item 1
    items = [
        {"ReportNormID": 1, "ParentReportNormID": 2, "Name": "Item 1", "Value1": 10},
        {"ReportNormID": 2, "ParentReportNormID": 3, "Name": "Item 2", "Value1": 20},
        {"ReportNormID": 3, "ParentReportNormID": 1, "Name": "Item 3 (Cycle)", "Value1": 30} 
    ]
    
    # If the recursive function 'get_real_level' doesn't use a visited set, it would crash here.
    df = transform_kbs(head, items, "TEST", "KQKD", "quarter", coa_data=None)
    
    # Test passed if it reaches this point without a RecursionError.
    assert not df.empty
    assert len(df) == 3

def test_transform_kbs_normal_hierarchy():
    """
    Test that a normal nested tree correctly calculates depth levels.
    """
    head = [{"YearPeriod": 2024, "TermCode": 1}]
    items = [
        {"ReportNormID": 1, "ParentReportNormID": 0, "Name": "Root", "Value1": 100},
        {"ReportNormID": 2, "ParentReportNormID": 1, "Name": "Child", "Value1": 50},
        {"ReportNormID": 3, "ParentReportNormID": 2, "Name": "Grandchild", "Value1": 25}
    ]
    
    df = transform_kbs(head, items, "TEST", "KQKD", "quarter", coa_data=None)
    
    assert len(df) == 3
    
    # Check levels are computed properly
    root_level = df[df['item'] == 'Root']['levels'].values[0]
    child_level = df[df['item'] == 'Child']['levels'].values[0]
    grandchild_level = df[df['item'] == 'Grandchild']['levels'].values[0]
    
    assert root_level == 0
    assert child_level == 1
    assert grandchild_level == 2
