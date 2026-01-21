def get_field_common_name(db_field_name):
    """
    Retorna el Nombre Común del campo basado en el mapeo del Diccionario de Datos.
    Si existe, retorna "DBField - CommonName".
    Si no existe, retorna solo "DBField".
    """
    mappings = {
        "ItemCode": "Codigo del Articulo",
        "ItemName": "Nombre del Articulo",
        "U_Codigo_Secundario": "Codigo Secundario",
        "FrgnName": "Nombre Extranjero",
        "ItemType": "Clase del Articulo",
        "ItmsGrpCod": "Grupo de Articulos",
        "UgpEntry": "Grupo unid. de medida",
        "InvntItem": "Artículo de inventario",
        "SellItem": "Artículo venta",
        "PrchseItem": "Artículo de compra",
        "PriceUnit": "Unidad de determinación de precios",
        "WTLiable": "Sujeto a retención de impuesto",
        "IndirctTax": "Impuesto indirecto",
        "ItemClass": "Artículo gestionado por",
        "MngMethod": "Método de gestión",
        "TaxCodeAR": "Indicador de IVA",
        "GLMethod": "Fijar ctas de mayor según",
        "EvalSystem": "Método de valoración",
        "IWeight1": "Peso",
        "InvntryUom": "Código de UM de recuento de inventario",
        "DfltWH": "Almacen Estandar",
        "PlaningSys": "Método de planificación",
        "PricingPrc": "Método aprovisionamiento",
        "LeadTime": "Tiempo lead",
        "ToleranDay": "Días de tolerancia",
        "QryGroup1": "DANEC",
        "QryGroup2": "TERRAFERTIL",
        "U_beas_gruppe": "Grupo de materiales",
        "U_beas_prccode": "Centro de coste",
        "U_beas_prodrelease": "Liberado Producción",
        "U_beas_batchroh": "Localización del Lote",
        "PicturName": "Imagen del Articulo",
        "U_beas_dispo": "Exploción lista de materiales",
        "U_EMPA_ESPESOR": "Espesor",
        "U_EMPA_DESIDAD": "Densidad",
        "U_EMPA_ANCHO": "Ancho",
        "U_PLG_CICLE": "Ciclo",
        "U_EMPA_CARACTERISTICA_TIPO": "Caracteristica Tipo",
        "U_EMPA_CARACTERISTICA_MP": "Caracteristica Tipo MP"
    }
    
    common_name = mappings.get(db_field_name)
    if common_name:
        return f"{db_field_name} - {common_name}"
    return db_field_name
