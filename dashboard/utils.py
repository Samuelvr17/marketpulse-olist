import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path


def get_col(df, preferred_columns):
    """
    Selecciona la primera columna disponible de una lista de preferencias.
    
    Args:
        df: DataFrame
        preferred_columns: Lista de nombres de columnas en orden de preferencia
        
    Returns:
        Nombre de la columna disponible o None
    """
    for col in preferred_columns:
        if col in df.columns:
            return col
    return None


def clean_text_column(df, column, default="Sin dato"):
    """
    Limpia una columna de texto rellenando nulos y convirtiendo a string.
    
    Args:
        df: DataFrame
        column: Nombre de la columna a limpiar
        default: Valor por defecto para nulos/valores inválidos
        
    Returns:
        DataFrame con la columna limpia
    """
    if column not in df.columns:
        return df
    
    df = df.copy()
    
    # Rellenar nulos
    df[column] = df[column].fillna(default)
    
    # Convertir a string
    df[column] = df[column].astype(str)
    
    # Reemplazar valores inválidos
    invalid_values = ['nan', 'None', '']
    df[column] = df[column].replace(invalid_values, default)
    
    return df


def get_filter_options(df, column):
    """
    Obtiene opciones de filtro de forma segura para una columna.
    
    Args:
        df: DataFrame
        column: Nombre de la columna
        
    Returns:
        Lista de opciones limpias y ordenadas
    """
    if column not in df.columns:
        return []
    
    # Obtener valores únicos
    values = df[column].dropna().unique()
    
    # Convertir a string
    values = [str(v) for v in values]
    
    # Excluir valores inválidos
    invalid_values = ['nan', 'None', '']
    values = [v for v in values if v not in invalid_values]
    
    # Ordenar de forma segura
    try:
        values = sorted(values)
    except TypeError:
        # Si hay tipos mixtos, ordenar como strings
        values = sorted(values, key=str)
    
    return values


def format_category_name(category):
    """
    Formatea el nombre de una categoría para visualización.
    Reemplaza guiones bajos por espacios y convierte a formato título.
    
    Args:
        category: Nombre de la categoría (string)
        
    Returns:
        Nombre formateado para visualización
    """
    if pd.isna(category) or category == 'Sin dato':
        return category
    
    # Reemplazar guiones bajos por espacios
    formatted = str(category).replace('_', ' ')
    
    # Convertir a formato título (primera letra de cada palabra en mayúscula)
    formatted = formatted.title()
    
    return formatted


@st.cache_data
def load_data():
    """
    Carga los datos procesados del proyecto.
    
    Returns:
        tuple: (fact_orders, customer_rfm, logistics_enriched)
    """
    base_path = Path(__file__).parent.parent / "data" / "processed"
    
    # Cargar tabla principal
    fact_orders_path = base_path / "fact_orders.csv"
    if fact_orders_path.exists():
        fact_orders = pd.read_csv(fact_orders_path)
    else:
        st.error(f"No se encontró el archivo {fact_orders_path}")
        fact_orders = pd.DataFrame()
    
    # Cargar segmentación RFM (opcional)
    customer_rfm_path = base_path / "customer_rfm.csv"
    if customer_rfm_path.exists():
        customer_rfm = pd.read_csv(customer_rfm_path)
    else:
        customer_rfm = pd.DataFrame()
    
    # Cargar logística enriquecida (opcional)
    logistics_enriched_path = base_path / "logistics_enriched.csv"
    if logistics_enriched_path.exists():
        logistics_enriched = pd.read_csv(logistics_enriched_path)
    else:
        logistics_enriched = pd.DataFrame()
    
    return fact_orders, customer_rfm, logistics_enriched


def prepare_fact_orders(df):
    """
    Prepara el dataframe de órdenes convirtiendo fechas y creando columnas auxiliares.
    
    Args:
        df: DataFrame con las órdenes
        
    Returns:
        DataFrame preparado
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # Convertir columnas de fecha
    date_columns = [
        'order_purchase_timestamp',
        'order_approved_at',
        'order_delivered_carrier_date',
        'order_delivered_customer_date',
        'order_estimated_delivery_date'
    ]
    
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Crear purchase_date si no existe
    if 'purchase_date' not in df.columns and 'order_purchase_timestamp' in df.columns:
        df['purchase_date'] = df['order_purchase_timestamp'].dt.date
    
    # Crear purchase_year_month si no existe
    if 'purchase_year_month' not in df.columns and 'order_purchase_timestamp' in df.columns:
        df['purchase_year_month'] = df['order_purchase_timestamp'].dt.to_period('M').astype(str)
    
    # Asegurar columnas numéricas
    numeric_columns = {
        'total_price': ['total_price', 'price'],
        'total_freight': ['total_freight', 'freight_value'],
        'payment_total': ['payment_total', 'payment_value'],
        'review_score_avg': ['review_score_avg'],
        'delivery_time_days': ['delivery_time_days'],
        'delivery_delay_days': ['delivery_delay_days']
    }
    
    for target_col, preferred_cols in numeric_columns.items():
        if target_col not in df.columns:
            source_col = get_col(df, preferred_cols)
            if source_col:
                df[target_col] = df[source_col]
    
    # Asegurar columnas binarias
    binary_columns = ['is_delivered', 'is_canceled', 'is_late', 'bad_review', 'has_review_comment']
    for col in binary_columns:
        if col in df.columns:
            # Convertir valores 10 a 1
            df[col] = df[col].replace(10, 1)
            # Asegurar que sea 0 o 1
            df[col] = df[col].fillna(0).astype(int)
    
    # Crear bad_review si no existe
    if 'bad_review' not in df.columns and 'review_score_avg' in df.columns:
        def create_bad_review(score):
            if pd.isna(score):
                return np.nan
            elif score <= 2:
                return 1
            elif score >= 4:
                return 0
            else:  # score == 3
                return np.nan
        df['bad_review'] = df['review_score_avg'].apply(create_bad_review)
    
    # Crear is_late si no existe
    if 'is_late' not in df.columns and 'delivery_delay_days' in df.columns:
        def create_is_late(delay):
            if pd.isna(delay):
                return np.nan
            elif delay > 0:
                return 1
            else:
                return 0
        df['is_late'] = df['delivery_delay_days'].apply(create_is_late)
    
    # Crear payment_total desde payment_value si no existe
    if 'payment_total' not in df.columns and 'payment_value' in df.columns:
        df['payment_total'] = df['payment_value']
    
    # Crear total_freight desde freight_value si no existe
    if 'total_freight' not in df.columns and 'freight_value' in df.columns:
        df['total_freight'] = df['freight_value']
    
    # Limpiar columnas de texto para filtros
    text_columns = ['main_category', 'customer_state', 'order_status', 'main_payment_type', 'customer_city']
    for col in text_columns:
        if col in df.columns:
            df = clean_text_column(df, col)
    
    return df


def apply_filters(df):
    """
    Aplica filtros globales desde el sidebar.
    
    Args:
        df: DataFrame a filtrar
        
    Returns:
        DataFrame filtrado
    """
    if df.empty:
        return df
    
    df_filtered = df.copy()
    
    with st.sidebar.expander("🔍 Filtros del análisis", expanded=True):
        # Filtro de rango de fechas
        if 'purchase_date' in df_filtered.columns:
            min_date = df_filtered['purchase_date'].min()
            max_date = df_filtered['purchase_date'].max()
            
            date_range = st.date_input(
                "Rango de fechas",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
            if len(date_range) == 2:
                start_date, end_date = date_range
                df_filtered = df_filtered[
                    (df_filtered['purchase_date'] >= start_date) & 
                    (df_filtered['purchase_date'] <= end_date)
                ]
        
        # Filtro de estado del cliente
        if 'customer_state' in df_filtered.columns:
            states = get_filter_options(df_filtered, 'customer_state')
            selected_states = st.multiselect(
                "Estado del cliente",
                options=states,
                default=[],  # Vacío por defecto = todos
                key="filter_state"
            )
            if selected_states:  # Solo filtrar si hay selección
                df_filtered = df_filtered[df_filtered['customer_state'].isin(selected_states)]
        
        # Filtro de estado de orden
        if 'order_status' in df_filtered.columns:
            statuses = get_filter_options(df_filtered, 'order_status')
            selected_statuses = st.multiselect(
                "Estado de orden",
                options=statuses,
                default=[],  # Vacío por defecto = todos
                key="filter_status"
            )
            if selected_statuses:  # Solo filtrar si hay selección
                df_filtered = df_filtered[df_filtered['order_status'].isin(selected_statuses)]
        
        # Filtro de categoría
        if 'main_category' in df_filtered.columns:
            categories = get_filter_options(df_filtered, 'main_category')
            # Excluir "Sin dato" de las opciones por defecto
            categories_filtered = [c for c in categories if c != 'Sin dato']
            selected_categories = st.multiselect(
                "Categoría",
                options=categories_filtered,
                default=[],  # Vacío por defecto = todos
                key="filter_category"
            )
            if selected_categories:  # Solo filtrar si hay selección
                df_filtered = df_filtered[df_filtered['main_category'].isin(selected_categories)]
    
    return df_filtered


def format_currency(value):
    """
    Formatea un valor monetario en formato compacto.
    
    Args:
        value: Valor numérico
        
    Returns:
        String formateado (ej: 15.4M, 159.8, 13.2M)
    """
    if pd.isna(value):
        return "0"
    
    if value >= 1_000_000:
        return f"{value/1_000_000:.1f}M"
    elif value >= 1_000:
        return f"{value/1_000:.1f}K"
    else:
        return f"{value:.0f}"


def format_percentage(value):
    """
    Formatea un valor como porcentaje.
    
    Args:
        value: Valor numérico (0-1 o 0-100)
        
    Returns:
        String formateado (ej: 8.11%)
    """
    if pd.isna(value):
        return "0.00%"
    
    if value > 1:
        return f"{value:.2f}%"
    else:
        return f"{value*100:.2f}%"


def calculate_kpis(df):
    """
    Calcula KPIs principales del dataframe de órdenes.
    
    Args:
        df: DataFrame con las órdenes
        
    Returns:
        dict con los KPIs calculados
    """
    if df.empty:
        return {}
    
    kpis = {}
    
    # Órdenes
    kpis['total_orders'] = len(df)
    kpis['delivered_orders'] = len(df[df['order_status'] == 'delivered']) if 'order_status' in df.columns else 0
    kpis['canceled_orders'] = len(df[df['order_status'] == 'canceled']) if 'order_status' in df.columns else 0
    
    # Clientes - usar customer_unique_id si existe, sino customer_id
    customer_col = get_col(df, ['customer_unique_id', 'customer_id'])
    kpis['unique_customers'] = df[customer_col].nunique() if customer_col else 0
    
    # Valores monetarios - usar columnas correctas
    kpis['total_payment_value'] = df['payment_total'].sum() if 'payment_total' in df.columns else 0
    kpis['total_revenue_items'] = df['total_price'].sum() if 'total_price' in df.columns else 0
    kpis['total_freight'] = df['total_freight'].sum() if 'total_freight' in df.columns else 0
    
    # Promedios
    kpis['average_order_value'] = df['payment_total'].mean() if 'payment_total' in df.columns else 0
    kpis['average_review_score'] = df['review_score_avg'].mean() if 'review_score_avg' in df.columns else 0
    
    # Tasas
    delivered = df[df['order_status'] == 'delivered'] if 'order_status' in df.columns else pd.DataFrame()
    if not delivered.empty:
        if 'is_late' in delivered.columns:
            kpis['late_delivery_rate'] = delivered['is_late'].mean()
        else:
            kpis['late_delivery_rate'] = 0
        
        if 'delivery_time_days' in delivered.columns:
            kpis['avg_delivery_time_days'] = delivered['delivery_time_days'].mean()
        else:
            kpis['avg_delivery_time_days'] = 0
    
    if 'bad_review' in df.columns:
        kpis['bad_review_rate'] = df['bad_review'].mean()
    elif 'review_score_avg' in df.columns:
        kpis['bad_review_rate'] = (df['review_score_avg'] <= 2).mean()
    else:
        kpis['bad_review_rate'] = 0
    
    kpis['cancellation_rate'] = (df['order_status'] == 'canceled').mean() if 'order_status' in df.columns else 0
    
    return kpis
