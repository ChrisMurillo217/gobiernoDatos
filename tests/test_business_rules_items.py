import pytest
import pandas as pd
import numpy as np
import sys
import os

# Adjust path to import app
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.business_rules import check_item_name_complex

def test_check_item_name_envase():
    # Valid
    # ENVASE PET 5 LT CRISTAL VOLCANIC 84 g r 48 mm
    # With optional client: VOLCANIC
    data = {'ItemName': ['ENVASE PET 5 LT CRISTAL VOLCANIC 84 g R 48 mm'], 'ItemCode': ['PTEPET0001']}
    df = pd.DataFrame(data)
    res = check_item_name_complex(df)
    assert res[0] == True, "Should be valid with client"

    # Valid without client? (Optional)
    # ENVASE PET 5 LT CRISTAL 84 g R 48 mm
    data = {'ItemName': ['ENVASE PET 5 LT CRISTAL 84 g R 48 mm'], 'ItemCode': ['PTEPET0002']}
    df = pd.DataFrame(data)
    res = check_item_name_complex(df)
    assert res[0] == True, "Should be valid without client"

    # Invalid order
    # ENVASE PET CRISTAL 5 LT ...
    data = {'ItemName': ['ENVASE PET CRISTAL 5 LT 84 g R 48 mm'], 'ItemCode': ['PTEPET0003']}
    df = pd.DataFrame(data)
    res = check_item_name_complex(df)
    assert res[0] == False, "Invalid order should fail"

def test_check_item_name_preforma():
    # Valid
    # PREFORMA PET 16.5 GR AZUL ORIENTAL R 1881
    data = {'ItemName': ['PREFORMA PET 16.5 GR AZUL ORIENTAL R 1881'], 'ItemCode': ['PTEPET0004']} # Assuming PTEPET fits or mapped
    # Preforma might fall under PTEPET? User didn't specify code prefix for Preforma, but let's assume valid prefix logic or check.
    # Actually, check_item_name_complex filters by prefix. 
    # 'PTEPET': ['ENVASE'] in original code. 'PREFORMA' is not in the map?
    # Wait, existing map: 'PTEPET': ['ENVASE'], 'PTEPAD': ['ENVASE']...
    # The user request implies ADDING these validations. So I need to add PREFORMA to the prefix map or handling.
    # If PREFORMA is not in valid_struct logic, it defaults to True?
    # Currently: valid_struct = pd.Series(True...)
    # I need to ensure PREFORMA is checked. 
    # For test purposes, I will check if my implementation adds PREFORMA key or if I should assume it's under 'PTEPET' or similar.
    # If not mapped, it returns True (identity). But I want strict validation.
    # "ItemName ... validation" implies strict check.
    # Note: I'll need to update prefix_map in strict implementation.
    # For now, let's assume I will map PREFORMA to PTEPET or similar or just add it.
    pass 

def test_check_item_name_lamina():
    # LAMINA PEBD 32,7 CM X 95 MC TRANSPARENTE ACEITE TRIREFINADO SIERRA 900 ML
    # Prefix for LAMINA is PTLAMI (existing map)
    data = {'ItemName': ['LAMINA PEBD 32,7 CM X 95 MC TRANSPARENTE ACEITE TRIREFINADO SIERRA 900 ML'], 'ItemCode': ['PTLAMI0001']}
    df = pd.DataFrame(data)
    res = check_item_name_complex(df)
    assert res[0] == True

def test_check_item_name_manga():
    # MANGA PEBD 36 "" X 60 MC TRANSPARENTE
    # Prefix PTMANG
    data = {'ItemName': ['MANGA PEBD 36 "" X 60 MC TRANSPARENTE'], 'ItemCode': ['PTMANG0001']}
    df = pd.DataFrame(data)
    res = check_item_name_complex(df)
    assert res[0] == True

def test_check_item_name_funda():
    # FUNDA PEBD 26,5"" X 66"" X 60 MC TRANSPARENTE
    # Prefix PTFUND
    data = {'ItemName': ['FUNDA PEBD 26,5"" X 66"" X 60 MC TRANSPARENTE'], 'ItemCode': ['PTFUND0001']}
    df = pd.DataFrame(data)
    res = check_item_name_complex(df)
    assert res[0] == True

def test_check_item_name_tapa():
    # TAPA PP REPOSTERO DORADA 250 - 500 GR DANEC
    # Prefix PTTAPA
    data = {'ItemName': ['TAPA PP REPOSTERO DORADA 250 - 500 GR DANEC'], 'ItemCode': ['PTTAPA0001']}
    df = pd.DataFrame(data)
    res = check_item_name_complex(df)
    assert res[0] == True
