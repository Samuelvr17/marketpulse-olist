import streamlit as st
from utils import load_data, prepare_fact_orders


st.set_page_config(
    page_title="MarketPulse Olist | Inteligencia Comercial",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


def main():
    st.title("📊 MarketPulse Olist | Inteligencia Comercial para E-commerce")
    st.markdown("---")
    
    # Descripción del proyecto
    st.markdown("""
    ## Sobre el Proyecto
    
    **MarketPulse Olist** es un dashboard ejecutivo interactivo para analizar el desempeño comercial de una plataforma de e-commerce brasileña.
    El análisis se basa en el dataset *Brazilian E-Commerce Public Dataset by Olist*, que contiene información transaccional real de miles de órdenes.
    
    ### Objetivos del Dashboard
    
    - **Análisis de Ventas**: Monitorear ingresos, ticket promedio y desempeño por categoría.
    - **Segmentación de Clientes**: Comprender el valor del cliente mediante análisis RFM.
    - **Logística**: Evaluar tiempos de entrega, retrasos y costos de flete.
    - **Satisfacción**: Analizar reviews y experiencia del cliente.
    
    ### Navegación
    
    Utilice el menú lateral para acceder a las diferentes páginas del dashboard:
    
    - **📋 Resumen Ejecutivo**: Visión general del negocio con KPIs clave.
    - **💰 Ventas y Productos**: Análisis detallado de ventas por categoría y producto.
    - **👥 Clientes RFM**: Segmentación de clientes por valor, frecuencia y recencia.
    - **🚚 Logística**: Análisis de entregas, retrasos y costos de envío.
    - **⭐ Satisfacción**: Análisis de reviews y experiencia del cliente.
    """)
    
    st.markdown("---")
    
    # Advertencia metodológica
    st.warning("""
    ⚠️ **Advertencia Metodológica**
    
    Este dashboard no calcula margen real, conversión real ni inventario real porque el dataset no contiene:
    - Costos de productos o operación
    - Datos de sesiones o tráfico web
    - Información de stock o inventario
    
    Los análisis se basan únicamente en datos transaccionales observados.
    """)
    
    st.markdown("---")
    
    # Estado de carga de datos
    st.subheader("📁 Estado de Datos")
    
    with st.spinner("Cargando datos..."):
        fact_orders, customer_rfm, logistics_enriched = load_data()
        
        if fact_orders.empty:
            st.error("❌ No se pudo cargar la tabla principal de órdenes (fact_orders.csv)")
            st.stop()
        
        fact_orders = prepare_fact_orders(fact_orders)
    
    # Mostrar resumen de archivos disponibles
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Órdenes cargadas", f"{len(fact_orders):,}")
    
    with col2:
        if not customer_rfm.empty:
            st.metric("Segmentación RFM", "✅ Disponible")
        else:
            st.metric("Segmentación RFM", "❌ No disponible")
    
    with col3:
        if not logistics_enriched.empty:
            st.metric("Logística enriquecida", "✅ Disponible")
        else:
            st.metric("Logística enriquecida", "❌ No disponible")
    
    st.markdown("---")
    
    # Información adicional
    st.info("""
    💡 **Para comenzar**, seleccione una página en el menú lateral izquierdo. 
    Cada página incluye filtros globales que permiten personalizar el análisis según sus necesidades.
    """)


if __name__ == "__main__":
    main()
