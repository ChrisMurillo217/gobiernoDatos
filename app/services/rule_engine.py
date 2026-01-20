import yaml
import pandas as pd
import numpy as np
import os

# Ruta relativa a este archivo: ../config/rules.yaml
RULES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'rules.yaml')

from functools import lru_cache

@lru_cache(maxsize=1)
def load_rules():
    """Carga las reglas desde el archivo YAML. (Cacheada)"""
    if not os.path.exists(RULES_PATH):
        print(f"[RuleEngine] Advertencia: No se encontró {RULES_PATH}.")
        return []
    try:
        with open(RULES_PATH, 'r') as f:
            config = yaml.safe_load(f)
        rules = config.get('rules', [])
        # print(f"[RuleEngine] Cargadas {len(rules)} reglas dinámicas.") # Verbose off
        return rules
    except Exception as e:
        print(f"[RuleEngine] Error cargando reglas: {e}")
        return []

def apply_rule(df, rule):
    """Aplica una regla individual a un DataFrame y retorna una Series booleana."""
    field = rule['field']
    rule_type = rule['type']
    
    if field not in df.columns:
        # Si el campo no existe en el DF, decidimos si retorna True o False.
        # Por seguridad asumimos True (no falla la regla), pero se podría loguear.
        return pd.Series(True, index=df.index)

    # Preparar datos
    col_data = df[field]
    
    if rule_type == 'range':
        # Conversión a numérico forzada para rangos
        val = pd.to_numeric(col_data, errors='coerce')
        min_v = rule.get('min', -float('inf'))
        max_v = rule.get('max', float('inf'))
        
        # Validar (NaN falla en rangos usualmente, o se maneja aparte?)
        # between devuelve False para NaN.
        return val.between(min_v, max_v)
    
    elif rule_type == 'value':
        target = rule['equal_to']
        # Comparación directa
        if isinstance(target, (int, float)):
            # Intentar comparar numéricamente
            val_num = pd.to_numeric(col_data, errors='coerce')
            return val_num == target
        else:
            # Comparar como string
            return col_data.astype(str) == str(target)
            
    # Otros tipos de reglas se pueden agregar aquí
    
    return pd.Series(True, index=df.index)

def evaluate_dynamic_rules(df):
    """
    Evalúa todas las reglas dinámicas sobre el DataFrame.
    Retorna un DataFrame con booleans (True=Pass, False=Fail) por columna evaluada.
    """
    rules = load_rules()
    results = {}
    
    for rule in rules:
        col_name = rule['field']
        res = apply_rule(df, rule)
        
        # Si ya hay resultados para esta columna (múltiples reglas), hacemos AND
        if col_name in results:
            results[col_name] = results[col_name] & res
        else:
            results[col_name] = res
            
    return pd.DataFrame(results, index=df.index)
