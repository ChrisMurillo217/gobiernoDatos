import pytest
import pandas as pd
import numpy as np
import sys
import os

# Agregar root al path para importar app
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.rule_engine import apply_rule

def test_apply_rule_range():
    df = pd.DataFrame({'val': [1, 5, 20, 0, 21, np.nan]})
    rule = {'field': 'val', 'type': 'range', 'min': 1, 'max': 20}
    
    res = apply_rule(df, rule)
    
    # 1 (True), 5 (True), 20 (True), 0 (False), 21 (False), NaN (False)
    assert res[0] == True
    assert res[1] == True
    assert res[2] == True
    assert res[3] == False
    assert res[4] == False
    assert res[5] == False

def test_apply_rule_value():
    df = pd.DataFrame({'cat': ['A', 'B', 'A', 'C']})
    rule = {'field': 'cat', 'type': 'value', 'equal_to': 'A'}
    
    res = apply_rule(df, rule)
    
    assert res[0] == True
    assert res[1] == False
    assert res[2] == True
    assert res[3] == False
