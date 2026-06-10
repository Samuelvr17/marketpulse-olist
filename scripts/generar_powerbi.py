import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configurar rutas
PROCESSED_DIR = Path('data/processed')
POWERBI_DIR = Path('data/powerbi')

# Crear directorio si no existe
POWERBI_DIR.mkdir(parents=True, exist_ok=True)

print('Librerías importadas correctamente.')

# Cargar archivos principales
print('\nCargando archivos procesados...')

fact_orders = pd.read_csv(PROCESSED_DIR / 'fact_orders.csv')
dim_customers = pd.read_csv(PROCESSED_DIR / 'dim_customers.csv')
dim_products = pd.read_csv(PROCESSED_DIR / 'dim_products.csv')
dim_sellers = pd.read_csv(PROCESSED_DIR / 'dim_sellers.csv')

# Cargar archivos opcionales si existen
try:
    logistics_enriched = pd.read_csv(PROCESSED_DIR / 'logistics_enriched.csv')
    print('✓ logistics_enriched.csv cargado')
except FileNotFoundError:
    logistics_enriched = None
    print('✗ logistics_enriched.csv no encontrado')

try:
    customer_rfm = pd.read_csv(PROCESSED_DIR / 'customer_rfm.csv')
    print('✓ customer_rfm.csv cargado')
except FileNotFoundError:
    customer_rfm = None
    print('✗ customer_rfm.csv no encontrado')

print(f'\nFact orders: {fact_orders.shape}')
print(f'Dim customers: {dim_customers.shape}')
print(f'Dim products: {dim_products.shape}')
print(f'Dim sellers: {dim_sellers.shape}')

# Usar logistics_enriched como base si existe, si no usar fact_orders
if logistics_enriched is not None:
    print('\nUsando logistics_enriched.csv como base principal')
    orders_base = logistics_enriched.copy()
else:
    print('\nUsando fact_orders.csv como base principal')
    orders_base = fact_orders.copy()

# Convertir columnas de fecha
date_columns = ['order_purchase_timestamp', 'order_approved_at', 
                'order_delivered_carrier_date', 'order_delivered_customer_date', 
                'order_estimated_delivery_date']

for col in date_columns:
    if col in orders_base.columns:
        orders_base[col] = pd.to_datetime(orders_base[col])

# Extraer componentes de fecha de purchase_timestamp
orders_base['purchase_year'] = orders_base['order_purchase_timestamp'].dt.year
orders_base['purchase_month'] = orders_base['order_purchase_timestamp'].dt.month
orders_base['purchase_year_month'] = orders_base['order_purchase_timestamp'].dt.to_period('M').astype(str)
orders_base['purchase_dayofweek'] = orders_base['order_purchase_timestamp'].dt.dayofweek
orders_base['purchase_hour'] = orders_base['order_purchase_timestamp'].dt.hour

print('Componentes de fecha extraídos correctamente.')

# Unir con dimensión de clientes
customer_cols = ['customer_id', 'customer_unique_id', 'customer_city', 'customer_state']
customers_subset = dim_customers[customer_cols]

# Eliminar columnas de cliente si ya existen para evitar duplicados
for col in ['customer_unique_id', 'customer_city', 'customer_state']:
    if col in orders_base.columns:
        orders_base = orders_base.drop(columns=[col])
    
orders_base = orders_base.merge(customers_subset, on='customer_id', how='left')

print('Información de clientes agregada.')
print(f'Columnas después del merge: {list(orders_base.columns)[:10]}...')

# Definir columnas requeridas
required_columns = [
    # Identificación
    'order_id', 'customer_id', 'customer_unique_id',
    # Estado
    'order_status',
    # Fechas
    'order_purchase_timestamp', 'order_approved_at', 'order_delivered_carrier_date',
    'order_delivered_customer_date', 'order_estimated_delivery_date',
    'purchase_year', 'purchase_month', 'purchase_year_month', 
    'purchase_dayofweek', 'purchase_hour',
    # Cliente
    'customer_city', 'customer_state',
    # Ventas
    'items_count', 'products_count', 'sellers_count',
    'total_price', 'total_freight', 'payment_total',
    'avg_item_price', 'main_category', 'main_payment_type',
    'payment_count', 'max_installments', 'freight_ratio', 'average_ticket',
    # Logística
    'is_delivered', 'is_canceled', 'is_unavailable',
    'approval_time_days', 'carrier_handling_time_days', 'delivery_time_days',
    'estimated_delivery_time_days', 'delivery_delay_days', 'is_late'
]

# Agregar columnas opcionales si existen
optional_columns = ['avg_distance_km', 'max_distance_km', 'main_seller_state']
for col in optional_columns:
    if col in orders_base.columns:
        required_columns.append(col)

# Agregar columnas de satisfacción si existen
satisfaction_columns = ['review_score_avg', 'review_score_min', 'review_score_max', 
                        'reviews_count', 'has_review_comment', 'bad_review']
for col in satisfaction_columns:
    if col in orders_base.columns:
        required_columns.append(col)

# Seleccionar columnas que existen
final_columns = [col for col in required_columns if col in orders_base.columns]
fact_orders_powerbi = orders_base[final_columns].copy()

print(f'\nTabla fact_orders_powerbi creada con {fact_orders_powerbi.shape[0]} filas y {fact_orders_powerbi.shape[1]} columnas.')
print(f'Columnas: {list(fact_orders_powerbi.columns)}')

# Guardar fact_orders_powerbi.csv
fact_orders_powerbi.to_csv(POWERBI_DIR / 'fact_orders_powerbi.csv', index=False)
print('✓ fact_orders_powerbi.csv guardado en data/powerbi/')

# Crear tabla de fechas
min_date = fact_orders_powerbi['order_purchase_timestamp'].min()
max_date = fact_orders_powerbi['order_purchase_timestamp'].max()

print(f'\nRango de fechas: {min_date} a {max_date}')

# Crear rango completo de fechas
date_range = pd.date_range(start=min_date, end=max_date, freq='D')
dim_date = pd.DataFrame({'date': date_range})

# Extraer componentes de fecha
dim_date['year'] = dim_date['date'].dt.year
dim_date['month'] = dim_date['date'].dt.month
dim_date['month_name'] = dim_date['date'].dt.month_name()
dim_date['year_month'] = dim_date['date'].dt.to_period('M').astype(str)
dim_date['quarter'] = dim_date['date'].dt.quarter
dim_date['day'] = dim_date['date'].dt.day
dim_date['day_of_week'] = dim_date['date'].dt.dayofweek
dim_date['day_name'] = dim_date['date'].dt.day_name()
dim_date['is_weekend'] = dim_date['date'].dt.dayofweek.isin([5, 6]).astype(int)

print(f'Tabla dim_date_powerbi creada con {dim_date.shape[0]} días.')

dim_date.to_csv(POWERBI_DIR / 'dim_date_powerbi.csv', index=False)
print('✓ dim_date_powerbi.csv guardado en data/powerbi/')

# Crear tabla de métricas mensuales
monthly_metrics = fact_orders_powerbi.groupby('purchase_year_month').agg({
    'order_id': 'count',
    'is_delivered': 'sum',
    'is_canceled': 'sum',
    'customer_unique_id': 'nunique',
    'total_price': 'sum',
    'payment_total': 'sum',
    'total_freight': 'sum',
    'average_ticket': 'mean',
    'review_score_avg': 'mean',
    'is_late': 'sum',
    'bad_review': 'sum'
}).reset_index()

# Renombrar columnas
monthly_metrics.columns = [
    'purchase_year_month', 'orders', 'delivered_orders', 'canceled_orders',
    'unique_customers', 'revenue_items', 'payment_value', 'freight_value',
    'average_order_value', 'average_review_score', 'late_deliveries', 'bad_reviews'
]

# Calcular tasas
monthly_metrics['late_delivery_rate'] = (monthly_metrics['late_deliveries'] / monthly_metrics['delivered_orders'] * 100).round(2)
monthly_metrics['bad_review_rate'] = (monthly_metrics['bad_reviews'] / monthly_metrics['delivered_orders'] * 100).round(2)

# Eliminar columnas intermedias
monthly_metrics = monthly_metrics.drop(['late_deliveries', 'bad_reviews'], axis=1)

# Reemplazar NaN con 0
monthly_metrics = monthly_metrics.fillna(0)

print(f'Tabla monthly_metrics_powerbi creada con {monthly_metrics.shape[0]} meses.')

monthly_metrics.to_csv(POWERBI_DIR / 'monthly_metrics_powerbi.csv', index=False)
print('✓ monthly_metrics_powerbi.csv guardado en data/powerbi/')

# Crear tabla de métricas por categoría
category_metrics = fact_orders_powerbi.groupby('main_category').agg({
    'order_id': 'count',
    'is_delivered': 'sum',
    'customer_unique_id': 'nunique',
    'total_price': 'sum',
    'payment_total': 'sum',
    'average_ticket': 'mean',
    'review_score_avg': 'mean',
    'is_late': 'sum',
    'bad_review': 'sum',
    'delivery_time_days': 'mean',
    'total_freight': 'mean'
}).reset_index()

# Renombrar columnas
category_metrics.columns = [
    'main_category', 'orders', 'delivered_orders', 'unique_customers',
    'revenue_items', 'payment_value', 'average_order_value', 'average_review_score',
    'late_deliveries', 'bad_reviews', 'avg_delivery_time_days', 'avg_freight_value'
]

# Calcular tasas
category_metrics['late_delivery_rate'] = (category_metrics['late_deliveries'] / category_metrics['delivered_orders'] * 100).round(2)
category_metrics['bad_review_rate'] = (category_metrics['bad_reviews'] / category_metrics['delivered_orders'] * 100).round(2)

# Eliminar columnas intermedias
category_metrics = category_metrics.drop(['late_deliveries', 'bad_reviews'], axis=1)

# Reemplazar NaN con 0
category_metrics = category_metrics.fillna(0)

print(f'Tabla category_metrics_powerbi creada con {category_metrics.shape[0]} categorías.')

category_metrics.to_csv(POWERBI_DIR / 'category_metrics_powerbi.csv', index=False)
print('✓ category_metrics_powerbi.csv guardado en data/powerbi/')

# Crear tabla de métricas por estado
state_metrics = fact_orders_powerbi.groupby('customer_state').agg({
    'order_id': 'count',
    'is_delivered': 'sum',
    'customer_unique_id': 'nunique',
    'total_price': 'sum',
    'payment_total': 'sum',
    'average_ticket': 'mean',
    'review_score_avg': 'mean',
    'is_late': 'sum',
    'bad_review': 'sum',
    'delivery_time_days': 'mean',
    'total_freight': 'mean'
}).reset_index()

# Renombrar columnas
state_metrics.columns = [
    'customer_state', 'orders', 'delivered_orders', 'unique_customers',
    'revenue_items', 'payment_value', 'average_order_value', 'average_review_score',
    'late_deliveries', 'bad_reviews', 'avg_delivery_time_days', 'avg_freight_value'
]

# Calcular tasas
state_metrics['late_delivery_rate'] = (state_metrics['late_deliveries'] / state_metrics['delivered_orders'] * 100).round(2)
state_metrics['bad_review_rate'] = (state_metrics['bad_reviews'] / state_metrics['delivered_orders'] * 100).round(2)

# Eliminar columnas intermedias
state_metrics = state_metrics.drop(['late_deliveries', 'bad_reviews'], axis=1)

# Reemplazar NaN con 0
state_metrics = state_metrics.fillna(0)

print(f'Tabla state_metrics_powerbi creada con {state_metrics.shape[0]} estados.')

state_metrics.to_csv(POWERBI_DIR / 'state_metrics_powerbi.csv', index=False)
print('✓ state_metrics_powerbi.csv guardado en data/powerbi/')

# Crear tabla RFM para Power BI
if customer_rfm is not None:
    print('\nProcesando customer_rfm.csv...')
    
    # Seleccionar columnas principales
    rfm_columns = [
        'customer_unique_id', 'customer_segment', 'recency_days', 
        'frequency', 'monetary', 'avg_order_value',
        'R_score', 'F_score', 'M_score', 'RFM_score_total',
        'customer_value_proxy'
    ]
    
    # Filtrar columnas que existen
    rfm_columns = [col for col in rfm_columns if col in customer_rfm.columns]
    
    customer_rfm_powerbi = customer_rfm[rfm_columns].copy()
    
    # Agregar información de estado y categoría principal si es posible
    if 'customer_state' in fact_orders_powerbi.columns:
        customer_state_info = fact_orders_powerbi.groupby('customer_unique_id')['customer_state'].first().reset_index()
        customer_rfm_powerbi = customer_rfm_powerbi.merge(customer_state_info, on='customer_unique_id', how='left')
    
    if 'main_category' in fact_orders_powerbi.columns:
        customer_category_info = fact_orders_powerbi.groupby('customer_unique_id')['main_category'].agg(lambda x: x.mode()[0] if len(x.mode()) > 0 else x.iloc[0]).reset_index()
        customer_category_info.columns = ['customer_unique_id', 'main_category']
        customer_rfm_powerbi = customer_rfm_powerbi.merge(customer_category_info, on='customer_unique_id', how='left')
    
    # Reemplazar NaN con 0
    customer_rfm_powerbi = customer_rfm_powerbi.fillna(0)
    
    customer_rfm_powerbi.to_csv(POWERBI_DIR / 'customer_rfm_powerbi.csv', index=False)
    print(f'✓ customer_rfm_powerbi.csv guardado con {customer_rfm_powerbi.shape[0]} clientes.')
else:
    print('\n✗ customer_rfm.csv no existe, saltando creación de customer_rfm_powerbi.csv')

# Calcular KPIs globales
total_orders = len(fact_orders_powerbi)
delivered_orders = fact_orders_powerbi['is_delivered'].sum()
canceled_orders = fact_orders_powerbi['is_canceled'].sum()
unique_customers = fact_orders_powerbi['customer_unique_id'].nunique()
total_revenue_items = fact_orders_powerbi['total_price'].sum()
total_payment_value = fact_orders_powerbi['payment_total'].sum()
total_freight = fact_orders_powerbi['total_freight'].sum()
average_order_value = fact_orders_powerbi['average_ticket'].mean()
average_review_score = fact_orders_powerbi['review_score_avg'].mean()
late_delivery_rate = (fact_orders_powerbi['is_late'].sum() / delivered_orders * 100) if delivered_orders > 0 else 0
bad_review_rate = (fact_orders_powerbi['bad_review'].sum() / delivered_orders * 100) if delivered_orders > 0 else 0
cancellation_rate = (canceled_orders / total_orders * 100) if total_orders > 0 else 0

# Calcular tasa de clientes recurrentes
customer_order_counts = fact_orders_powerbi['customer_unique_id'].value_counts()
repeat_customers = (customer_order_counts > 1).sum()
repeat_customer_rate = (repeat_customers / unique_customers * 100) if unique_customers > 0 else 0

# Crear DataFrame de KPIs
kpis = pd.DataFrame({
    'metric': [
        'total_orders', 'delivered_orders', 'canceled_orders',
        'unique_customers', 'total_revenue_items', 'total_payment_value',
        'total_freight', 'average_order_value', 'average_review_score',
        'late_delivery_rate', 'bad_review_rate', 'cancellation_rate',
        'repeat_customer_rate'
    ],
    'value': [
        total_orders, delivered_orders, canceled_orders,
        unique_customers, total_revenue_items, total_payment_value,
        total_freight, average_order_value, average_review_score,
        late_delivery_rate, bad_review_rate, cancellation_rate,
        repeat_customer_rate
    ]
})

# Redondear valores decimales
kpis['value'] = kpis['value'].round(2)

print(f'\nTabla executive_kpis_powerbi creada con {kpis.shape[0]} KPIs.')

kpis.to_csv(POWERBI_DIR / 'executive_kpis_powerbi.csv', index=False)
print('✓ executive_kpis_powerbi.csv guardado en data/powerbi/')

# Resumen de archivos generados
print('\n' + '='*60)
print('ARCHIVOS GENERADOS PARA POWER BI')
print('='*60)

powerbi_files = list(POWERBI_DIR.glob('*.csv'))
for file in sorted(powerbi_files):
    size_mb = file.stat().st_size / (1024 * 1024)
    print(f'✓ {file.name} ({size_mb:.2f} MB)')

print('\n' + '='*60)
print('Todos los archivos están listos para cargar en Power BI Desktop.')
print('='*60)
