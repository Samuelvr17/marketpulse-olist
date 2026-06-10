# MarketPulse - Olist Inteligencia Comercial

## Descripción breve
Proyecto de analítica de datos para portafolio enfocado en el dataset de e-commerce brasileño Olist. El proyecto busca generar insights de negocio a través de análisis exploratorio, segmentación de clientes, análisis logístico, forecasting de ventas y detección de anomalías.

## Objetivo general
Desarrollar un pipeline completo de analítica de datos que incluya desde la carga y limpieza de datos hasta la creación de un dashboard interactivo para la toma de decisiones comerciales.

## Estructura del proyecto
```
marketpulse-olist-inteligencia-comercial/
├── data/               # Almacenamiento de datos
│   ├── raw/           # Datos originales (CSVs de Olist)
│   ├── processed/     # Datos procesados y transformados
│   └── external/      # Datos externos complementarios
├── notebooks/         # Notebooks de análisis y desarrollo
├── src/              # Módulos de Python reutilizables
├── dashboard/        # Aplicación Streamlit
├── reports/          # Reportes y visualizaciones
├── models/           # Modelos entrenados guardados
├── docs/             # Documentación del proyecto
└── main.py          # Punto de entrada principal
```

## Dataset esperado
El proyecto utiliza el dataset público de Olist, que contiene 9 tablas principales:
- olist_orders_dataset.csv
- olist_order_items_dataset.csv
- olist_order_payments_dataset.csv
- olist_order_reviews_dataset.csv
- olist_customers_dataset.csv
- olist_products_dataset.csv
- olist_sellers_dataset.csv
- olist_geolocation_dataset.csv
- product_category_name_translation.csv

**Nota importante:** Los archivos CSV originales deben colocarse en la carpeta `data/raw/`.

## Stack tecnológico previsto
- Python 3.x
- Pandas y NumPy para manipulación de datos
- Matplotlib, Seaborn y Plotly para visualización
- Streamlit para el dashboard interactivo
- Scikit-learn para modelado de machine learning
- Statsmodels para análisis estadístico
- XGBoost y LightGBM para modelos avanzados
- Jupyter Notebooks para análisis exploratorio

## Estado del proyecto
Este es un proyecto en desarrollo inicial. La estructura se ha creado para facilitar el desarrollo incremental de cada componente.
