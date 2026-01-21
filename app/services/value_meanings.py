def get_value_meaning(col_name, value):
    """
    Retorna el significado del valor para campos específicos.
    Formato: "Valor - Significado"
    """
    if str(value) == 'nan' or value is None or str(value).strip() == '':
        return value

    val_str = str(value).strip()
    
    mappings = {
        "UgpEntry": {
            "1": "UN",
            "3": "KG",
            "11": "UNDPKG",
            "-1": "Manual"
        },
        "ItemType": {
            "I": "Artículos",
            "L": "Trabajo", 
            "T": "Viaje"
        },
        "InvntItem": {"Y": "Articulo de inventario", "N": "No"},
        "SellItem": {"Y": "Articulo de venta", "N": "No"},
        "PrchseItem": {"Y": "Articulo de compra", "N": "No"},
        "WTLiable": {"Y": "Sujeto a retencion de impuesto", "N": "No"},
        "IndirctTax": {"Y": "Impuesto indirecto", "N": "No"},
        "QryGroup1": {"Y": "Si", "N": "No"},
        "QryGroup2": {"Y": "Si", "N": "No"},
        "U_beas_prodrelease": {"Y": "Sí - Liberación de Producción Permitida", "N": "No"},
        "U_beas_batchroh": {
            "N": "Determinación automática de lote",
            "J": "Lote como material", 
            "M": "Introducir lotes manualmente"
        },
        "MngMethod": {
            "A": "En todas las transacciones",
            "R": "Solo en release"
        },
        "GLMethod": {
            "C": "Por Grupo de Artículos",
            "L": "Por Nivel de Artículo",
            "W": "Por Almacén" 
        },
        "EvalSystem": {
            "A": "Promedio Ponderado",
            "S": "Estándar",
            "F": "FIFO"
        },
        "PlaningSys": {
            "M": "PNM",
            "N": "Ninguno"
        },
        "ItemClass": {
            "0": "Ninguno",
            "1": "Numeros de serie",
            "2": "Lotes"
        },
        "U_beas_dispo": {
            "B": "Orientado a Stock",
            "A": "Por Orden",
            "S": "Artículo Fantasma",
            "K": "No hay resolución"
        }
    }

    if col_name in mappings:
        meaning = mappings[col_name].get(val_str)
        if meaning:
            return f"{val_str} - {meaning}"
    
    return value
