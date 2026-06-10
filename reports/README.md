# MarketPulse Olist

Proyecto de analítica de datos y visualización ejecutiva basado en el dataset público de Olist, un marketplace de e-commerce en Brasil.

El objetivo del proyecto fue analizar el comportamiento comercial del marketplace a partir de más de 99 mil órdenes, evaluando ventas, clientes, productos, logística y satisfacción del cliente.

## Qué se hizo

* Se realizó limpieza, transformación y preparación de datos con Python y Pandas.
* Se construyó una tabla maestra de órdenes para centralizar la información comercial, logística y de satisfacción.
* Se analizaron indicadores clave como órdenes totales, valor pagado, ticket promedio, clientes únicos, entregas tardías, cancelaciones y calificación promedio.
* Se aplicó segmentación de clientes RFM para identificar perfiles de compra y comportamiento de clientes.
* Se desarrollaron dashboards interactivos en Streamlit y Power BI para presentar los principales hallazgos de negocio.

## Herramientas utilizadas

* Python
* Pandas
* Jupyter Notebook
* Plotly
* Streamlit
* Power BI
* Power Query
* DAX

## Estructura del proyecto

```text
dashboard/      Dashboard interactivo en Streamlit
notebooks/      Análisis, limpieza, ETL y preparación de datos
scripts/        Script para preparar archivos usados en Power BI
data/           Carpeta local para datos originales y procesados
reports/        Carpeta local para reportes y archivos generados
```

## Datos

Los archivos CSV no se incluyen en el repositorio porque son datos originales o generados. Para reproducir el proyecto, se debe descargar el dataset de Olist, ubicar los CSV originales en `data/raw/` y ejecutar los notebooks correspondientes.

Dataset utilizado: Brazilian E-Commerce Public Dataset by Olist. 
https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

## Cómo ejecutar el dashboard Streamlit

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Ejecutar la aplicación:

```bash
streamlit run dashboard/app.py
```
