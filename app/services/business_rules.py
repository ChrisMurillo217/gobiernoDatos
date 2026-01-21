import pandas as pd
import numpy as np
from app.services.rule_engine import load_rules, apply_rule

# ==========================================
# --- Funciones de Ayuda ---
def _check_not_null(df, col):
    return df[col].notna()

def _check_value(df, col, val):
    return df[col] == val

def _check_range(df, col, min_v, max_v):
    return pd.to_numeric(df[col], errors='coerce').between(min_v, max_v)

def _check_is_in(df, col, values):
    return df[col].isin(values)

# ===================================================
# REGLAS DE PERFILAMIENTO (Reglas Simples / Formato)
# ===================================================

def rule_item_code(df):
    """
    ItemCode: Analizar si el codigo empieza por PT que no sea nulo y que 
    tenga mas de 10 caracteres alfanumericos en mayusculas.
    """
    s = df['ItemCode'].astype(str)
    cond_start = s.str.startswith('PT', na=False)
    cond_len = s.str.len() > 10
    cond_alnum = s.str.isalnum()
    cond_upper = s.str.isupper()
    return cond_start & cond_len & cond_alnum & cond_upper

def rule_item_name(df):
    """ItemName: Debe estar todo en Mayusculas y sin tildes."""
    s = df['ItemName'].astype(str)
    cond_upper = s.str.isupper()
    cond_no_tildes = ~s.str.contains('[ÁÉÍÓÚáéíóú]', regex=True, na=False)
    return cond_upper & cond_no_tildes

def rule_item_type(df):
    return _check_value(df, 'ItemType', 'I')

def rule_itms_grp_cod(df):
    return _check_not_null(df, 'ItmsGrpCod')

def rule_ugp_entry(df):
    """
    UgpEntry debe cumplir:
    - Si ItemName contiene LAMINA o MANGA -> debe ser 3
    - Si ItemName contiene ENVASE, TAPA, MANGA, BALDE, PREFORMA o FUNDA -> debe ser 1
    - Si ItemCode es PTFUND0212 o PTFUND0216 -> debe ser 11
    """
    name = df['ItemName'].astype(str)
    code = df['ItemCode'].astype(str)
    
    # Condiciones específicas
    is_lamina_manga = name.str.contains('LAMINA|MANGA', regex=True, na=False)
    is_envase_group = name.str.contains('ENVASE|TAPA|MANGA|BALDE|PREFORMA|FUNDA', regex=True, na=False)
    is_special_fund = code.isin(['PTFUND0212', 'PTFUND0216'])
    
    # Validaciones
    check_3 = df['UgpEntry'] == 3
    check_1 = df['UgpEntry'] == 1
    check_11 = df['UgpEntry'] == 11
    
    # Lógica: Por defecto True, aplicar validaciones específicas
    result = pd.Series(True, index=df.index)
    
    # Si es LAMINA o MANGA -> debe ser 3
    result = np.where(is_lamina_manga, check_3, result)
    
    # Si es ENVASE, TAPA, etc. -> debe ser 1 (pero MANGA ya fue validado arriba)
    result = np.where(is_envase_group & ~is_lamina_manga, check_1, result)
    
    # Si es PTFUND0212 o PTFUND0216 -> debe ser 11 (prioridad máxima)
    result = np.where(is_special_fund, check_11, result)
    
    return result

def rule_invnt_item(df):
    return _check_value(df, 'InvntItem', 'Y')

def rule_sell_item(df):
    return _check_value(df, 'SellItem', 'Y')

def rule_prchse_item(df):
    cond_imp = df['ItemCode'].astype(str).str.contains('IMP', na=False)
    check_compra = df['PrchseItem'] == 'Y'
    check_no = df['PrchseItem'] == 'N'
    return np.where(cond_imp, check_compra, check_no)

def rule_price_unit(df):
    """
    PriceUnit depende de UgpEntry:
    - UgpEntry=1 -> PriceUnit=8
    - UgpEntry=3 -> PriceUnit=2
    - UgpEntry=11 -> PriceUnit=13
    """
    ugp = pd.to_numeric(df['UgpEntry'], errors='coerce').fillna(0)
    pu = pd.to_numeric(df['PriceUnit'], errors='coerce').fillna(0)
    
    # Validaciones
    check_1 = pu == 8
    check_3 = pu == 2
    check_11 = pu == 13
    
    # Por defecto False seguro, o True? Mejor True y negar fallos.
    result = pd.Series(True, index=df.index)
    
    result = np.where(ugp == 1, check_1, result)
    result = np.where(ugp == 3, check_3, result)
    result = np.where(ugp == 11, check_11, result)
    
    return result

def rule_wt_liable(df):
    return _check_not_null(df, 'WTLiable')

def rule_indirct_tax(df):
    return _check_not_null(df, 'IndirctTax')

# Cambiarlo
def rule_item_class(df):
    """ItemClass: Siempre debe ser igual a 2"""
    return _check_range(df, 'ItemClass', 2, 2)

def rule_mng_method(df):
    return _check_value(df, 'MngMethod', 'A')

def rule_tax_code_ar(df):
    return _check_not_null(df, 'TaxCodeAR')

def rule_gl_method(df):
    return _check_not_null(df, 'GLMethod')

def rule_eval_system(df):
    return _check_not_null(df, 'EvalSystem')

def rule_i_weight1(df):
    return df['IWeight1'] > 0

def rule_invntry_uom(df):
    """
    UgpEntry (InvntryUom):
    - Si ItemName es LAMINA o MANGA -> KG
    - Si ItemName contiene ENVASE, TAPA, MANGA, BALDE, PREFORMA o FUNDA -> UN
    """
    name = df['ItemName'].astype(str)
    # Caso 1: Coincidencia Exacta -> KG
    # "si el ItemName contiene; LAMINA o MANGA usar KG"
    matches_kg = name.isin(['LAMINA', 'MANGA'])
    check_kg = df['InvntryUom'] == 'KG'
    # Caso 2: Contiene -> UN
    patterns_un = ['ENVASE', 'TAPA', 'MANGA', 'BALDE', 'PREFORMA', 'FUNDA']
    matches_un = name.str.contains('|'.join(patterns_un), regex=True, na=False)
    check_un = df['InvntryUom'] == 'UN'
    # Lógica: Por defecto True. Si matches_un -> check_un. Si matches_kg -> check_kg (sobrescribe).
    res = pd.Series(True, index=df.index)
    # Aplica validación UN
    res = np.where(matches_un, check_un, res)
    # Aplica validación KG (Específico sobrescribe general si hay conflicto, ej. MANGA)
    res = np.where(matches_kg, check_kg, res)
    return res

def rule_dflt_wh(df):
    return df['DfltWH'].astype(str).str.contains('_PROD', na=False)
    
def rule_planing_sys(df):
    return _check_value(df, 'PlaningSys', 'M')

def rule_pricing_prc(df):
    """PricingPrc debe ser 0"""
    return _check_value(df, 'PricingPrc', 0)

def rule_lead_time(df):
    """LeadTime: Debe ser un numero entre 1 y 20"""
    return _check_range(df, 'LeadTime', 1, 20)
    
def rule_toleran_day(df):
    """ToleranDay: Numero entero entre 0 y 24"""
    return _check_range(df, 'ToleranDay', 0, 24)

def rule_pricing_prc(df):
    """PricingPrc debe ser 0"""
    return df['PricingPrc'] == 0

def rule_lead_time(df):
    """LeadTime: Debe ser un numero entre 1 y 20"""
    return df['LeadTime'].between(1, 20)

def rule_toleran_day(df):
    """ToleranDay: Numero entero entre 0 y 24"""
    return df['ToleranDay'].between(0, 24)

def rule_u_beas_gruppe(df):
    """U_beas_gruppe siempre valido (True proforma)"""
    return pd.Series(True, index=df.index)

def rule_u_beas_prccode(df):
    """U_beas_gruppe debe ser igual a U_beas_prccode"""
    return df['U_beas_gruppe'].fillna('') == df['U_beas_prccode'].fillna('')

def rule_u_beas_prodrelease(df):
    """U_beas_prodrelease debe ser 'Y'"""
    return df['U_beas_prodrelease'] == 'Y'

def rule_u_beas_batchroh(df):
    """U_beas_batchroh siempre valido"""
    return pd.Series(True, index=df.index)

def rule_pictur_name(df):
    """PicturName siempre valido"""
    return pd.Series(True, index=df.index)

def rule_u_beas_dispo(df):
    """U_beas_dispo debe ser 'A' o 'B'"""
    return df['U_beas_dispo'].isin(['A', 'B'])

def rule_u_empa_espesor(df):
    # LLENAR CUANDO SEA PTLAMI Y PTMANG
    cond_target = df['ItemCode'].astype(str).str.contains('PTLAMI|PTMANG', na=False, regex=True)
    val_gt_0 = df['U_EMPA_ESPESOR'] > 0
    val_is_nan = df['U_EMPA_ESPESOR'].isna()
    return np.where(cond_target, val_gt_0, val_is_nan)

def rule_u_empa_desidad(df):
    cond_target = df['ItemCode'].astype(str).str.contains('PTLAMI|PTMANG', na=False, regex=True)
    val_gt_0 = df['U_EMPA_DESIDAD'] > 0
    val_is_nan = df['U_EMPA_DESIDAD'].isna()
    return np.where(cond_target, val_gt_0, val_is_nan)

def rule_u_empa_ancho(df):
    cond_target = df['ItemCode'].astype(str).str.contains('PTLAMI|PTMANG', na=False, regex=True)
    val_gt_0 = df['U_EMPA_ANCHO'] > 0
    val_is_nan = df['U_EMPA_ANCHO'].isna()
    return np.where(cond_target, val_gt_0, val_is_nan)

def rule_u_plg_cicle(df):
    cond_target = df['ItemCode'].astype(str).str.contains('PTLAMI|PTMANG|PTFUN', na=False, regex=True)
    # Si es (Lami/Mang/Fun) -> Debe estar vacio (NaN)
    val_is_nan = df['U_PLG_CICLE'].isna()
    # Si es (PT) -> Debe estar entre 1.00 y 160.00
    val = df['U_PLG_CICLE']
    valid_range = (val >= 1.00) & (val <= 160.00)
    return np.where(cond_target, val_is_nan, valid_range)

# ==============================================
# REGLAS DE CALIDAD (Reglas Complejas / Negocio)
# ==============================================

def get_valid_from_profiling(df_profiling, col_name, item_codes):
    if col_name in df_profiling.columns:
        return df_profiling[col_name]
    return pd.Series(False, index=item_codes) 

def check_u_codigo_secundario(df):
    not_na = df['U_Codigo_Secundario'].notna()
    duplicates = df[not_na].duplicated(subset=['U_Codigo_Secundario'], keep=False)
    is_valid = ~duplicates
    mask = pd.Series(True, index=df.index)
    mask.loc[not_na] = is_valid
    return mask

def check_frgn_name(df):
    return df['ItemName'] != df['FrgnName']

def check_itms_grp_cod(df):
    return _check_not_null(df, 'ItmsGrpCod')

def check_wt_liable(df):
    return _check_not_null(df, 'WTLiable')

def check_indirct_tax(df):
    # Si IndirctTax == 'Y', TaxCodeAR debe tener valor.
    # Si NO es 'Y', la regla no aplica (es válido por defecto).
    cond_target = df['IndirctTax'] == 'Y'
    check_exists = df['TaxCodeAR'].notna()
    # Retorna True si: NO es target, O (SI es target Y existe)
    return np.where(cond_target, check_exists, True)

def check_tax_code_ar(df):
    return _check_not_null(df, 'TaxCodeAR')

def check_gl_method(df):
    return _check_value(df, 'GLMethod', 'C')

def check_eval_system(df):
    return _check_not_null(df, 'EvalSystem')

def check_planing_sys(df):
    starts_pt = df['ItemCode'].astype(str).str.startswith('PT', na=False)
    is_pnm = df['PlaningSys'] == 'M'
    valid_pt = starts_pt & is_pnm
    valid_other = (~starts_pt) & (df['PlaningSys'] != 'M')
    return valid_pt | valid_other

def check_pricing_prc(df):
    return _check_not_null(df, 'PricingPrc')

def check_lead_time(df):
    rules = load_rules()
    for rule in rules:
        if rule['field'] == 'LeadTime':
            return apply_rule(df, rule)
    return _check_range(df, 'LeadTime', 0, 20)

def check_toleran_day(df):
    return (df['ToleranDay'] + df['LeadTime']) == 20

def check_u_beas_prodrelease(df):
    starts_pt = df['ItemCode'].astype(str).str.startswith('PT', na=False)
    is_y = df['U_beas_prodrelease'] == 'Y'
    valid_pt = starts_pt & is_y
    valid_other = (~starts_pt) & (~is_y)
    return valid_pt | valid_other

def check_u_beas_dispo(df):
    grp = df['ItmsGrpCod']
    val = df['U_beas_dispo']
    is_pt = grp == 'PRODUCTO TERMINADO'
    valid_a = np.where(is_pt, val=='A', val!='A')
    is_semi = grp == 'PRODUCTO SEMIELABORADO'
    valid_b = np.where(is_semi, val=='B', val!='B')
    return pd.Series(valid_a | valid_b, index=df.index)

def check_u_empa_espesor_range(df):
    # Calidad: PTLAMI/PTMANG -> 25 a 125 (¿Enteros?)
    # Diccionario dice "enteros desde 25 UM hasta 125 UM"
    code = df['ItemCode'].astype(str)
    is_ptlami = code.str.contains('PTLAMI', na=False)
    is_ptmang = code.str.contains('PTMANG', na=False)
    target = is_ptlami | is_ptmang
    
    val = df['U_EMPA_ESPESOR']
    is_valid_range = (val >= 25) & (val <= 125)
    return np.where(target, is_valid_range, True)

def check_u_empa_ancho_range(df):
    # Calidad: PTLAMI -> 8.4-120, PTMANG -> 5-58
    code = df['ItemCode'].astype(str)
    val = pd.to_numeric(df['U_EMPA_ANCHO'], errors='coerce')
    
    is_ptlami = code.str.contains('PTLAMI', na=False)
    is_ptmang = code.str.contains('PTMANG', na=False)
    
    valid_lami = val.between(8.4, 120)
    valid_mang = val.between(5, 58)
    
    # Lógica: Si Lami -> valida Lami, Sino Si Mang -> valida Mang, Sino -> True
    # Usamos np.where anidado para evitar asignacion parcial que causa warnings
    return np.where(is_ptlami, valid_lami, np.where(is_ptmang, valid_mang, True))

def check_u_empa_caracteristica_tipo(df):
    # Calidad: ESPECIFICO vs GENERICO basado en Cliente en Nombre
    # Asumiendo primero que los valores válidos son SOLO 'ESPECIFICO', 'GENERICO'.
    return df['U_EMPA_CARACTERISTICA_TIPO'].isin(['ESPECIFICO', 'GENERICO'])

def check_u_empa_caracteristica_mp(df):
    return _check_not_null(df, 'U_EMPA_CARACTERISTICA_MP')

def check_item_code_complex(df):
    """
    ItemCode: Unico, No nulo.
    Estructura por Grupo (102, 103, 114).
    """
    s = df['ItemCode'].astype(str)
    grp = pd.to_numeric(df['ItmsGrpCod'], errors='coerce')
    is_unique = ~s.duplicated(keep=False)
    not_null = s.notna() & (s != 'nan') & (s != '')
    starts_pt = s.str.startswith('PT', na=False)
    valid_struct = pd.Series(False, index=df.index)    
    # 102: PT + (Lista) + 4 digitos
    # "Despues de esos 6 caracteres si ItmsGrpCod es 102 deben tener 4 digitos" -> PT(2)+XXXX(4) 
    # PT EPET (6) + 4 digitos. Total 10.
    list_102 = ['EPET', 'EPAD', 'TAPA', 'BALD', 'FUND', 'LAMI', 'MANG']
    pat_102 = r'^PT(' + '|'.join(list_102) + r')\d{4}$'
    check_102 = s.str.match(pat_102, na=False)
    # 103: PTPR + 6 digitos
    # "si ItmsGrpCod es 103 despues de PT debe ir PR, Despues de esos 4 caracteres deben tener 6 digitos"
    # PT PR = 4 carac. + 6 digitos.
    pat_103 = r'^PTPR\d{6}$'
    check_103 = s.str.match(pat_103, na=False)
    # 114: PT + 4 + IMP + 4? 
    # El usuario indico: "si ItmsGrpCod es 114 despues de PT y los 4 caracteres siguientes debe tener IMP."
    # Y tambien: "Despues de esos 9 caracteres si ItmsGrpCod es 114 deben tener 4 digitos"
    # Esto implica la estructura: PT (2) + XXXX (4) + IMP (3) = 9 caracteres?
    # Asi que 114 items empiezan con PT....IMP y luego 4 digitos.    
    pat_114_imp = r'^PT.{4}IMP'
    check_114 = s.str.match(pat_114_imp, na=False)
    pat_114 = r'^PT.{4}IMP\d{4}$'
    check_114 = s.str.match(pat_114, na=False)
    valid_struct = np.where(grp == 102, check_102, valid_struct)
    valid_struct = np.where(grp == 103, check_103, valid_struct)
    valid_struct = np.where(grp == 114, check_114, valid_struct)
    return is_unique & not_null & starts_pt & valid_struct

def check_item_name_complex(df):
    """
    ItemName: Unico, No nulo.
    Estructura: [ProductoMapped] [Material] [Specs]
    """
    name = df['ItemName'].astype(str).str.strip()
    code = df['ItemCode'].astype(str)
    is_unique = ~name.duplicated(keep=False)
    not_null = name.notna() & (name != 'nan') & (name != '')
    prefix_map = {
        'PTEPET': ['ENVASE'],
        'PTEPAD': ['ENVASE'],
        'PTTAPA': ['TAPA', 'ANILLO', 'SOBRETAPA', 'TAZON', 'TAPON'],
        'PTBALD': ['BALDE'],
        'PTFUND': ['FUNDA', 'FUNDAS'],
        'PTLAMI': ['LAMINA', 'BILAMINA'],
        'PTMANG': ['MANGA'],
        'PTMANI': ['MANIJA'],
        'PTREPO': ['REPOSTERO']
    }
    materials = ['MIX', 'PEAD', 'PET', 'PC', 'PEBD', 'POLIOLEFINA', 'BOPP', 'CAST', 'PP']
    mat_pat = '|'.join(materials)
    valid_struct = pd.Series(True, index=df.index) # Por defecto true para los que no coinciden con prefijos conocidos
    # Asumiremos estricto para los prefijos conocidos
    # La regla dice "ItemName ... debe seguir la estructura siguiente". Implica para todos.
    # Pero primero validemos cuales aplican. Iteramos el mapa.
    # Estrategia: Inicializar en False solo para los que tienen prefijo PT?
    # O validar positivo si cumple alguna regla.
    # Vamos a iterar. Si code empieza con key, 'name' DEBE coincidir con value + material.
    for prefix, allowed_names in prefix_map.items():
        mask_prefix = code.str.startswith(prefix, na=False)
        if not mask_prefix.any():
            continue
        names_pat = '|'.join(allowed_names)
        full_pat = r'^(' + names_pat + r') (' + mat_pat + r').*'
        check_row = name.str.match(full_pat, na=False)
        valid_struct = np.where(mask_prefix, check_row, valid_struct)
    return is_unique & not_null & valid_struct

def check_item_type(df):
    s = df['ItemType']
    not_null = s.notna() & (s != '')
    check_pt = np.where(df['ItemCode'].astype(str).str.startswith('PT', na=False), s == 'I', True)
    return not_null & check_pt

def check_invnt_item(df):
    return _check_value(df, 'InvntItem', 'Y')

def check_sell_item(df):
    return _check_value(df, 'SellItem', 'Y')

def check_prchse_item(df):
    has_imp = df['ItemName'].astype(str).str.contains('IMP', na=False)
    return np.where(has_imp, df['PrchseItem'] == 'Y', True)

def check_price_unit(df):
    """
    PriceUnit depende de UgpEntry:
    - UgpEntry=1 -> PriceUnit=8
    - UgpEntry=3 -> PriceUnit=2
    - UgpEntry=11 -> PriceUnit=13
    """
    ugp = pd.to_numeric(df['UgpEntry'], errors='coerce').fillna(0)
    pu = pd.to_numeric(df['PriceUnit'], errors='coerce').fillna(0)
    
    check_1 = pu == 8
    check_3 = pu == 2
    check_11 = pu == 13
    
    result = pd.Series(True, index=df.index)
    result = np.where(ugp == 1, check_1, result)
    result = np.where(ugp == 3, check_3, result)
    result = np.where(ugp == 11, check_11, result)
    
    return result

def check_item_class(df):
    rules = load_rules()
    for rule in rules:
        if rule['field'] == 'ItemClass':
            return apply_rule(df, rule)
    return _check_range(df, 'ItemClass', 2, 2)

def check_mng_method(df):
    rules = load_rules()
    for rule in rules:
        if rule['field'] == 'MngMethod':
            return apply_rule(df, rule)
    return _check_value(df, 'MngMethod', 'A')

def check_i_weight1(df):
    rules = load_rules()
    for rule in rules:
        if rule['field'] == 'IWeight1':
            return apply_rule(df, rule)
    return _check_range(df, 'IWeight1', 0, 1000)

def check_invntry_uom(df):
    """
    InvntryUom depende de UgpEntry:
    - UgpEntry=1 -> 'UN'
    - UgpEntry=3 -> 'KG'
    - UgpEntry=11 -> 'PKG'
    """
    ugp = pd.to_numeric(df['UgpEntry'], errors='coerce').fillna(0)
    uom = df['InvntryUom'].astype(str)
    
    check_1 = uom == 'UN'
    check_3 = uom == 'KG'
    check_11 = uom == 'PKG'
    
    # Por defecto asumimos válido si no cae en estas reglas? 
    # O inválido? Si UgpEntry es otro, ¿qué debería ser InvntryUom?
    # Asumiremos True por defecto para no romper otros casos.
    result = pd.Series(True, index=df.index)
    
    result = np.where(ugp == 1, check_1, result)
    result = np.where(ugp == 3, check_3, result)
    result = np.where(ugp == 11, check_11, result)
    
    return result

def check_dflt_wh(df):
    s = df['DfltWH'].astype(str)
    return s.str.contains('_PROD', na=False)

def check_u_beas_gruppe(df):
    return _check_not_null(df, 'U_beas_gruppe') & (df['U_beas_gruppe'] != '')

def check_u_beas_prccode(df):
    return _check_not_null(df, 'U_beas_prccode') & (df['U_beas_prccode'] != '')

def check_u_beas_batchroh(df):
    return _check_value(df, 'U_beas_batchroh', 'Y')

def check_u_beas_desidad(df):
    code = df['ItemCode'].astype(str)
    is_ptlami = code.str.contains('PTLAMI', na=False)
    is_ptmang = code.str.contains('PTMANG', na=False)
    target = is_ptlami | is_ptmang
    # Debe estar lleno = No Nulo. Asumir columna U_BEAS_DESIDAD existe.
    if 'U_BEAS_DESIDAD' not in df.columns:
        return pd.Series(False, index=df.index) # Fallar si falta columna
    val = df['U_BEAS_DESIDAD']
    not_null = val.notna() & (val != '')
    return np.where(target, not_null, True)

def check_u_plg_cicle(df):
    code = df['ItemCode'].astype(str)
    is_ptlami = code.str.contains('PTLAMI', na=False)
    is_ptmang = code.str.contains('PTMANG', na=False)
    target = is_ptlami | is_ptmang
    val = pd.to_numeric(df['U_PLG_CICLE'], errors='coerce')
    valid_null = df['U_PLG_CICLE'].isna() | (df['U_PLG_CICLE'] == '')
    valid_range = val.between(1, 160)
    return np.where(target, valid_null, valid_range)

# ==========================================
# REGLAS DE LIMPIEZA (Reglas de Limpieza / Transformación)
# Cada función recibe df y devuelve df modificado (in-place o copy)
# ==========================================

def clean_item_code(df):
    df['ItemCode_Obsolete'] = False
    return df

def clean_item_name(df):
    # Validacion vectorizada de estructura nombre
    # >= 2 palabras y contiene materiales
    s = df['ItemName'].astype(str)
    has_spaces = s.str.split().str.len() >= 2
    materials = ['PEBD', 'PEAD', 'PET', 'MIX', 'PP']
    # ¿Sensible a mayúsculas por 'PeBd' vs 'PEBD'? Código de usuario 'in' es sensible a mayúsculas
    has_material = s.str.contains('|'.join(materials), regex=True, case=True)
    
    df['ItemName_Valid'] = has_spaces & has_material
    df['Needs_I_D_Review'] = ~df['ItemName_Valid']
    return df

def clean_item_type(df):
    df['ItemType'] = df['ItemType'].replace('', 'I').fillna('I')
    return df

def clean_invntry_uom(df):
    # Vectorizacion: Si PTLAMI -> KG, else -> UN (si ItemCode no es na, sino original)
    cond_ptlami = df['ItemCode'].astype(str).str.contains('PTLAMI', na=False)
    new_val = np.where(cond_ptlami, 'KG', 'UN')
    # ¿Preservar NaN si ItemCode es NaN? Código usuario: if pd.isna(itemcode): return row['InvntryUom']
    # Pero si ItemCode es NaN, cond_ptlami es False ('UN').
    # Si ItemCode es NaN, el usuario quieria devolver valor original.
    mask_na = df['ItemCode'].isna()
    final_val = np.where(mask_na, df['InvntryUom'], new_val)
    df['InvntryUom'] = final_val
    return df

def clean_u_beas_prodrelease_fill(df):
    df['U_beas_prodrelease'] = df['U_beas_prodrelease'].replace('', 'Y').fillna('Y')
    return df

def clean_u_beas_dispo_fill(df):
    df['U_beas_dispo'] = df['U_beas_dispo'].replace('', 'Y').fillna('Y')
    return df

def clean_invnt_item_sell_item(df):
    # InvntItem siempre debe ser 'Y'
    df['InvntItem'] = 'Y'
    
    pt_mask = df['ItemCode'].astype(str).str.startswith('PT', na=False)
    imp_mask = df['ItemCode'].astype(str).str.contains('IMP', na=False)
    
    df.loc[pt_mask, 'SellItem'] = 'Y'
    df.loc[pt_mask & imp_mask, 'PrchseItem'] = 'Y'
    return df

def clean_price_unit(df):
    """
    Asigna PriceUnit basado en UgpEntry:
    - 1 -> 8
    - 3 -> 2
    - 11 -> 13
    """
    ugp = pd.to_numeric(df['UgpEntry'], errors='coerce').fillna(0)
    
    # Inicializar con 0 o mantener previo si no aplica? User implies strict mapping.
    # Pero si UgpEntry no es 1,3,11? Asignar 0 o dejar como estaba?
    # Asumiremos que UgpEntry ya fue limpiado y tiene 1,3,11 principalmente.
    # Pero si hay otros valores, PriceUnit debería ser consistente?
    # El usuario solo especificó reglas para 1, 3, 11.
    
    vals = df['PriceUnit'].copy()
    
    vals[ugp == 1] = 8
    vals[ugp == 3] = 2
    vals[ugp == 11] = 13
    
    df['PriceUnit'] = vals
    return df

def clean_lot_number(df):
    df['LotNumber'] = 'Lotes'
    return df

def clean_manage_by(df):
    df['ManageBy'] = 'EN TODAS LAS TRANSACCIONES'
    return df

def clean_iweight1(df):
    pt_mask = df['ItemCode'].astype(str).str.startswith('PT', na=False)
    df.loc[pt_mask, 'IWeight1'] = 500.0
    return df

def clean_dflt_wh(df):
    # Vectorización: Si ItemCode contiene '_PROD', preservar el valor actual de DfltWH
    # De lo contrario, asignar 'UIO_PROD' por defecto
    code_upper = df['ItemCode'].astype(str).str.upper()
    
    # Crear copia de valores actuales
    vals = df['DfltWH'].copy()
    
    # Máscara: ItemCode contiene '_PROD'
    mask_has_prod = code_upper.str.contains('_PROD', na=False)
    
    # Si NO contiene '_PROD', revisar el valor actual de DfltWH
    # Si contiene 'GYE' -> 'GYE_PROD', si contiene 'UIO' -> 'UIO_PROD', sino -> 'UIO_PROD'
    mask_needs_update = ~mask_has_prod
    
    # Para los que necesitan actualización, revisar el valor actual
    dflt_wh_upper = df['DfltWH'].astype(str).str.upper()
    mask_has_gye = dflt_wh_upper.str.contains('GYE', na=False)
    mask_has_uio = dflt_wh_upper.str.contains('UIO', na=False)
    
    # Aplicar lógica: GYE -> GYE_PROD, UIO -> UIO_PROD, otros -> UIO_PROD
    vals[mask_needs_update & mask_has_gye] = 'GYE_PROD'
    vals[mask_needs_update & mask_has_uio & ~mask_has_gye] = 'UIO_PROD'  # UIO pero no GYE
    vals[mask_needs_update & ~mask_has_gye & ~mask_has_uio] = 'UIO_PROD'  # Ni GYE ni UIO
    
    # Restaurar si ItemCode era NA
    mask_na = df['ItemCode'].isna()
    vals[mask_na] = df.loc[mask_na, 'DfltWH']
    
    df['DfltWH'] = vals
    return df

def clean_planning_sys(df):
    df['PlaningSys'] = 'M'
    return df

def clean_prchse_item_pt(df):
    pt_mask = df['ItemCode'].astype(str).str.startswith('PT', na=False)
    df.loc[pt_mask, 'PrchseItem'] = 'EFECTUAR'
    return df

def clean_lead_time_pt(df):
    pt_mask = df['ItemCode'].astype(str).str.startswith('PT', na=False)
    df.loc[pt_mask, 'LeadTime'] = 20
    return df

def clean_toleran_day(df):
    df['ToleranDay'] = pd.to_numeric(df['ToleranDay'], errors='coerce').fillna(0).clip(0, 24)
    return df

def clean_u_beas_gruppe_material(df):
    # Extraer material del Nombre
    s = df['ItemName'].astype(str)
    materials = ['PEBD', 'PEAD', 'PET', 'MIX', 'PP']
    # Extracción vectorizada es complicada con prioridad, pero bucle es aceptable o regex
    pattern = '|'.join(materials)
    # str.extract retorna primer solapamiento
    extracted = s.str.extract(f'({pattern})', expand=False).fillna('')
    df['U_beas_gruppe'] = extracted
    return df

def clean_u_beas_prodrelease_check(df):
    pt_mask = df['ItemCode'].astype(str).str.startswith('PT', na=False)
    df.loc[pt_mask, 'U_beas_prodrelease'] = 'Y'
    df.loc[~pt_mask, 'U_beas_prodrelease'] = np.nan
    return df

def clean_u_beas_batchroh(df):
    df['U_beas_batchroh'] = 'DETERMINACION DE LOTE'
    return df

def clean_pictur_name(df):
    s = df['PicturName'].astype(str)
    valid_ext = s.str.lower().str.endswith(('.jpg', '.png', '.pdf'))
    df['PicturName_Valid'] = valid_ext
    df['Needs_Design_Graphics_Review'] = ~valid_ext
    return df

def clean_u_beas_dispo_letter(df):
    # Si PROD TERM -> A, SEMI -> B, sino -> A
    # Código de usuario maneja grupo nulo con cadena vacía
    grp = df.get('GrupoArticulo', pd.Series(['']*len(df))).fillna('') # Manejar si falta col
    
    cond_semi = grp.str.contains('SEMIELABORADO')
    # cond_term = grp.str.contains('PRODUCTO TERMINADO') -> A
    # sino -> A.
    # Entonces: Si SEMI -> B, sino -> A.
    
    df['U_beas_dispo'] = np.where(cond_semi, 'B', 'A')
    return df

def clean_u_empa_espesor(df):
    pt_mask = df['ItemCode'].astype(str).str.startswith('PT', na=False)
    code = df['ItemCode'].astype(str)
    is_ptlami = code.str.contains('PTLAMI', na=False)
    is_ptmang = code.str.contains('PTMANG', na=False)
    lam_mang = is_ptlami | is_ptmang
    mask = pt_mask & lam_mang
    df.loc[mask, 'U_EMPA_ESPESOR'] = df.loc[mask, 'U_EMPA_ESPESOR'].fillna(50)
    return df

def clean_u_empa_desidad(df):
    pt_mask = df['ItemCode'].astype(str).str.startswith('PT', na=False)
    code = df['ItemCode'].astype(str)
    is_ptlami = code.str.contains('PTLAMI', na=False)
    is_ptmang = code.str.contains('PTMANG', na=False)
    lam_mang = is_ptlami | is_ptmang
    mask = pt_mask & lam_mang
    df.loc[mask, 'U_EMPA_DESIDAD'] = df.loc[mask, 'U_EMPA_DESIDAD'].fillna(0.92)
    df.loc[~mask, 'U_EMPA_DESIDAD'] = np.nan
    return df

def clean_u_empa_ancho(df):
    pt_mask = df['ItemCode'].astype(str).str.startswith('PT', na=False)
    code = df['ItemCode'].astype(str)
    is_ptlami = code.str.contains('PTLAMI', na=False)
    is_ptmang = code.str.contains('PTMANG', na=False)
    lam_mang = is_ptlami | is_ptmang
    mask = pt_mask & lam_mang
    df.loc[mask, 'U_EMPA_ANCHO'] = df.loc[mask, 'U_EMPA_ANCHO'].fillna(10.0)
    return df

def clean_u_plg_cicle(df):
    pt_mask = df['ItemCode'].astype(str).str.startswith('PT', na=False)
    code = df['ItemCode'].astype(str)
    is_ptlami = code.str.contains('PTLAMI', na=False)
    is_ptmang = code.str.contains('PTMANG', na=False)
    is_ptfun = code.str.contains('PTFUN', na=False)
    target = is_ptlami | is_ptmang | is_ptfun
    
    # 1. PT y Objetivo -> NaN
    df.loc[pt_mask & target, 'U_PLG_CICLE'] = np.nan
    
    # 2. PT y No Objetivo -> Rellenar 30
    mask2 = pt_mask & ~target
    df.loc[mask2, 'U_PLG_CICLE'] = df.loc[mask2, 'U_PLG_CICLE'].fillna(30.0)
    return df

def clean_u_beas_gruppe_client_type(df):
    # clientes_especificos = ['DANEC', 'TERRAFERTIL'] -> ESPECIFICO, sino GENERIC
    s = df['ItemName'].astype(str)
    clients_pattern = 'DANEC|TERRAFERTIL'
    is_specific = s.str.contains(clients_pattern, regex=True)
    df['U_beas_gruppe'] = np.where(is_specific, 'ESPECIFICO', 'GENERIC')
    return df

def clean_item_code_format(df):
    """Corrige formato de ItemCode: convierte a mayúsculas"""
    df['ItemCode'] = df['ItemCode'].astype(str).str.upper()
    return df

def clean_item_name_format(df):
    """Corrige formato de ItemName: mayúsculas y sin tildes"""
    s = df['ItemName'].astype(str)
    # Convertir a mayúsculas
    s = s.str.upper()
    # Remover tildes
    replacements = {'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
                'á': 'A', 'é': 'E', 'í': 'I', 'ó': 'O', 'ú': 'U'}
    for old, new in replacements.items():
        s = s.str.replace(old, new, regex=False)
    df['ItemName'] = s
    return df

def clean_mng_method(df):
    """Asigna MngMethod = 'A' por defecto"""
    df['MngMethod'] = df['MngMethod'].fillna('A')
    df.loc[df['MngMethod'] == '', 'MngMethod'] = 'A'
    return df

def clean_item_class(df):
    """Asigna ItemClass = 2"""
    df['ItemClass'] = 2
    return df

def clean_wt_liable(df):
    """Asigna WTLiable por defecto si está vacío"""
    df['WTLiable'] = df['WTLiable'].fillna('Y')
    df.loc[df['WTLiable'] == '', 'WTLiable'] = 'Y'
    return df

def clean_indirct_tax(df):
    """
    Asigna sugerencia para IndirctTax.
    Usuario solicita explícitamente: 'Asignar valor a TaxCodeAR'
    """
    message = "Asignar valor a TaxCodeAR"
    
    # Si esta vacío o nulo -> mensaje
    df['IndirctTax'] = df['IndirctTax'].fillna(message)
    df.loc[df['IndirctTax'] == '', 'IndirctTax'] = message
    
    # Si la validación falla para valores que NO son 'Y' (p.ej 'N'), 
    # tal vez deberíamos sugerir el mensaje también?
    # La regla check_indirct_tax valida si 'IndirctTax' está presente (si es dependiente de TaxCodeAR).
    # Si asumimos que cualquier fallo debe mostrar este mensaje:
    # Podemos forzar que la versión 'limpia' siempre tenga este mensaje si no es válida.
    # Pero por seguridad, reemplacemos todo lo que no sea 'Y' con el mensaje?
    # O simplemente llenamos nulos. El usuario dijo "si no cumple".
    # Si el valor actual es vacio, no cumple -> sugerencia mensaje.
    
    return df

def clean_tax_code_ar(df):
    """Asigna TaxCodeAR por defecto si está vacío"""
    df['TaxCodeAR'] = df['TaxCodeAR'].fillna('IVAV15')
    df.loc[df['TaxCodeAR'] == '', 'TaxCodeAR'] = 'IVAV15'
    return df

def clean_gl_method(df):
    """Asigna GLMethod = 'C' (Por Grupo de Artículos)"""
    df['GLMethod'] = 'C'
    return df

def clean_eval_system(df):
    """Asigna EvalSystem por defecto"""
    df['EvalSystem'] = df['EvalSystem'].fillna('A')
    df.loc[df['EvalSystem'] == '', 'EvalSystem'] = 'A'
    return df

def clean_pricing_prc(df):
    """Asigna PricingPrc = 0"""
    df['PricingPrc'] = 0
    return df

def clean_ugp_entry(df):
    """
    Asigna UgpEntry según reglas:
    - Si ItemCode es PTFUND0212 o PTFUND0216 -> 11
    - Si ItemName contiene LAMINA o MANGA -> 3
    - Si ItemName contiene ENVASE, TAPA, BALDE, PREFORMA o FUNDA -> 1
    - Por defecto -> 1
    """
    name = df['ItemName'].astype(str)
    code = df['ItemCode'].astype(str)
    
    # Inicializar con valor por defecto
    df['UgpEntry'] = 1
    
    # Aplicar reglas en orden de prioridad (de menos a más específico)
    # 1. Si contiene ENVASE, TAPA, BALDE, PREFORMA, FUNDA -> 1
    mask_envase = name.str.contains('ENVASE|TAPA|BALDE|PREFORMA|FUNDA', regex=True, na=False)
    df.loc[mask_envase, 'UgpEntry'] = 1
    
    # 2. Si contiene LAMINA o MANGA -> 3 (sobrescribe anterior si aplica)
    mask_lamina_manga = name.str.contains('LAMINA|MANGA', regex=True, na=False)
    df.loc[mask_lamina_manga, 'UgpEntry'] = 3
    
    # 3. Casos especiales PTFUND0212 o PTFUND0216 -> 11 (máxima prioridad)
    mask_special = code.isin(['PTFUND0212', 'PTFUND0216'])
    df.loc[mask_special, 'UgpEntry'] = 11
    
    return df

def clean_itms_grp_cod(df):
    """Asigna ItmsGrpCod por defecto basado en ItemCode"""
    code = df['ItemCode'].astype(str)
    # Por defecto 102 (Producto Terminado)
    df.loc[df['ItmsGrpCod'].isna(), 'ItmsGrpCod'] = 102
    # Si contiene PTPR -> 103 (Preforma)
    df.loc[code.str.contains('PTPR', na=False), 'ItmsGrpCod'] = 103
    # Si contiene IMP -> 114 (Importado)
    df.loc[code.str.contains('IMP', na=False), 'ItmsGrpCod'] = 114
    return df

def clean_frgn_name(df):
    """Asigna FrgnName diferente a ItemName si son iguales"""
    mask_equal = df['FrgnName'] == df['ItemName']
    df.loc[mask_equal, 'FrgnName'] = df.loc[mask_equal, 'ItemName'] + ' (ENG)'
    return df

def clean_u_empa_caracteristica_tipo(df):
    """Asigna tipo ESPECIFICO o GENERICO basado en cliente"""
    s = df['ItemName'].astype(str)
    clients_pattern = 'DANEC|TERRAFERTIL'
    is_specific = s.str.contains(clients_pattern, regex=True, na=False)
    df['U_EMPA_CARACTERISTICA_TIPO'] = np.where(is_specific, 'ESPECIFICO', 'GENERICO')
    return df

def clean_u_empa_caracteristica_mp(df):
    """Asigna material predominante basado en ItemName"""
    s = df['ItemName'].astype(str)
    materials = ['PEBD', 'PEAD', 'PET', 'MIX', 'PP', 'PC', 'POLIOLEFINA', 'BOPP', 'CAST']
    pattern = '|'.join(materials)
    extracted = s.str.extract(f'({pattern})', expand=False).fillna('MIX')
    df['U_EMPA_CARACTERISTICA_MP'] = extracted
    return df


# ==========================================
# REGISTROS EXPORTADOS
# ==========================================

PROFILING_RULES = {
    "ItemCode": rule_item_code,
    "ItemName": rule_item_name,
    "PricingPrc": rule_pricing_prc,
    "LeadTime": rule_lead_time,
    "ToleranDay": rule_toleran_day,
    "U_beas_gruppe": rule_u_beas_gruppe,
    "U_beas_prccode": rule_u_beas_prccode,
    "U_beas_prodrelease": rule_u_beas_prodrelease,
    "U_beas_batchroh": rule_u_beas_batchroh,
    "PicturName": rule_pictur_name,
    "U_beas_dispo": rule_u_beas_dispo,
    "U_EMPA_ESPESOR": rule_u_empa_espesor,
    "U_EMPA_DESIDAD": rule_u_empa_desidad,
    "U_EMPA_ANCHO": rule_u_empa_ancho,
    "U_PLG_CICLE": rule_u_plg_cicle,
    "ItemType": rule_item_type,
    "UgpEntry": rule_ugp_entry,
    "InvntItem": rule_invnt_item,
    "SellItem": rule_sell_item,
    "PrchseItem": rule_prchse_item,
    "PriceUnit": rule_price_unit,
    "ItemClass": rule_item_class,
    "MngMethod": rule_mng_method,
    "IWeight1": rule_i_weight1,
    "InvntryUom": rule_invntry_uom,
    "DfltWH": rule_dflt_wh,
    "PlaningSys": rule_planing_sys
}

QUALITY_RULES = {
    "U_Codigo_Secundario": check_u_codigo_secundario,
    "FrgnName": check_frgn_name,
    "ItmsGrpCod": check_itms_grp_cod,
    "WTLiable": check_wt_liable,
    "IndirctTax": check_indirct_tax,
    "GLMethod": check_gl_method,
    "EvalSystem": check_eval_system,
    "TaxCodeAR": check_tax_code_ar,
    "PlaningSys": check_planing_sys,
    "PricingPrc": check_pricing_prc,
    "LeadTime": check_lead_time,
    "ToleranDay": check_toleran_day,
    "U_beas_prodrelease": check_u_beas_prodrelease,
    "U_beas_dispo": check_u_beas_dispo,
    "U_EMPA_CARACTERISTICA_TIPO": check_u_empa_caracteristica_tipo,
    "U_EMPA_CARACTERISTICA_MP": check_u_empa_caracteristica_mp,
    "U_EMPA_ESPESOR": check_u_empa_espesor_range,
    "U_EMPA_ANCHO": check_u_empa_ancho_range,
    
    # Nuevas Reglas
    "ItemCode": check_item_code_complex,
    "ItemName": check_item_name_complex,
    "ItemType": check_item_type,
    "InvntItem": check_invnt_item,
    "SellItem": check_sell_item,
    "PrchseItem": check_prchse_item,
    "PriceUnit": check_price_unit,
    "ItemClass": check_item_class,
    "MngMethod": check_mng_method,
    "IWeight1": check_i_weight1,
    "InvntryUom": check_invntry_uom,
    "DfltWH": check_dflt_wh,
    "U_beas_gruppe": check_u_beas_gruppe,
    "U_beas_prccode": check_u_beas_prccode,
    "U_beas_batchroh": check_u_beas_batchroh,
    "U_BEAS_DESIDAD": check_u_beas_desidad,
    "U_PLG_CICLE": check_u_plg_cicle,
}

PROFILING_DEPENDENCY_MAP = {
    "ItemType": "ItemType",
    "UgpEntry": "UgpEntry",
    "InvntItem": "InvntItem",
    "SellItem": "SellItem",
    "PrchseItem": "PrchseItem",
    "PriceUnit": "PriceUnit",
    "ItemClass": "ItemClass", 
    "MngMethod": "MngMethod",
    "IWeight1": "IWeight1",
    "InvntryUom": "InvntryUom",
    "DfltWH": "DfltWH",
    "QryGroup1": "QryGroup1",
    "QryGroup2": "QryGroup2",
    "U_beas_gruppe": "U_beas_gruppe",
    "U_beas_prccode": "U_beas_prccode",
    "U_beas_batchroh": "U_beas_batchroh",
    "PicturName": "PicturName",
    "U_EMPA_ESPESOR": "U_EMPA_ESPESOR",
    "U_EMPA_DESIDAD": "U_EMPA_DESIDAD",
    "U_EMPA_ANCHO": "U_EMPA_ANCHO",
    "U_PLG_CICLE": "U_PLG_CICLE"
}

# Lista ordenada de transformaciones
CLEANING_RULES = [
    clean_item_code_format,        # NUEVO: Formato ItemCode
    clean_item_name_format,        # NUEVO: Formato ItemName
    clean_item_code,
    clean_item_name,
    clean_item_type,
    clean_invntry_uom,
    clean_u_beas_prodrelease_fill,
    clean_u_beas_dispo_fill,
    clean_invnt_item_sell_item,

    clean_lot_number,
    clean_manage_by,
    clean_iweight1,
    clean_dflt_wh,
    clean_planning_sys,
    clean_prchse_item_pt,
    clean_lead_time_pt,
    clean_toleran_day,
    clean_u_beas_gruppe_material,
    clean_u_beas_prodrelease_check,
    clean_u_beas_batchroh,
    clean_pictur_name,
    clean_u_beas_dispo_letter,
    clean_u_empa_espesor,
    clean_u_empa_desidad,
    clean_u_empa_ancho,
    clean_u_plg_cicle,
    clean_u_beas_gruppe_client_type,
    # NUEVAS FUNCIONES DE LIMPIEZA
    clean_mng_method,
    clean_item_class,
    clean_wt_liable,
    clean_indirct_tax,
    clean_tax_code_ar,
    clean_gl_method,
    clean_eval_system,
    clean_pricing_prc,
    clean_ugp_entry,
    clean_price_unit,
    clean_itms_grp_cod,
    clean_frgn_name,
    clean_u_empa_caracteristica_tipo,
    clean_u_empa_caracteristica_mp
]

RULE_DESCRIPTIONS = {
    "PricingPrc": "Debe ser 0.",
    "LeadTime": "Debe ser mayor a 0 y menor o igual a 20.",
    "ToleranDay": "La suma de ToleranDay + LeadTime debe ser 20.",
    "QryGroup1": "Debe ser válido.",
    "QryGroup2": "Debe ser válido.",
    "U_beas_gruppe": "Debe ser no nulo.",
    "U_beas_prccode": "Debe ser no nulo.",
    "U_beas_prodrelease": "Debe ser 'Y' para PT (o nulo para otros).",
    "U_beas_batchroh": "Debe ser 'Y'.",
    "PicturName": "PTLAMI requiere .jpg/.png, otros .pdf.",
    "U_beas_dispo": "PT=A, Semi=B.",
    "U_EMPA_ESPESOR": "Debe estar definido para PTLAMI/PTMANG (25-125).",
    "U_EMPA_DESIDAD": "Debe estar definido para PTLAMI/PTMANG.",
    "U_BEAS_DESIDAD": "Si ItemCode PTLAMI/PTMANG debe estar lleno.",
    "U_EMPA_ANCHO": "PTLAMI (8.4-120), PTMANG (5-58).",
    "U_PLG_CICLE": "PTLAMI/PTMANG -> Null, otros -> 1-160.",
    "ItemType": "No nulo y en PT debe ser 'I'.",
    "UgpEntry": "LAMINA/MANGA=3, ENVASE/TAPA/BALDE/PREFORMA/FUNDA=1, PTFUND0212/PTFUND0216=11.",
    "InvntItem": "Debe ser 'Y'.",
    "SellItem": "Debe ser 'Y'.",
    "PrchseItem": "Debe ser 'Y' solo si nombre contiene IMP.",
    "PriceUnit": "UgpEntry=1 -> 8, UgpEntry=3 -> 2, UgpEntry=11 -> 13.",
    "ItemClass": "Debe ser 2.",
    "MngMethod": "Debe ser 'A'.",
    "IWeight1": "Entre 0 y 1000 (inclusive).",
    "InvntryUom": "LAMINA/MANGA -> KG, otros -> UN.",
    "DfltWH": "Debe contener UIO_ o GYE_.",
    "PlaningSys": "Debe ser 'M'.",
    "U_Codigo_Secundario": "No debe estar duplicado.",
    "FrgnName": "No debe ser igual a ItemName.",
    "ItmsGrpCod": "102, 103 o 114.",
    "WTLiable": "No debe estar vacío.",
    "IndirctTax": "Si es 'Impuesto indirecto', TaxCodeAR debe existir.",
    "GLMethod": "Debe ser 'Por Grupo de Artículos'.",
    "EvalSystem": "A o S.",
    "TaxCodeAR": "No debe estar vacío.",
    "U_EMPA_CARACTERISTICA_TIPO": "Debe ser ESPECIFICO o GENERICO.",
    "U_EMPA_CARACTERISTICA_MP": "No debe estar vacío.",
    "ItemCode": "Estructura PT especí­fica por grupo (102, 103, 114).",
    "ItemName": "Estructura [Producto] [Material] [Specs] y prefijos válidos."
}
