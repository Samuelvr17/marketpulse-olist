import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

# Agregar el directorio padre al path para importar utils
sys.path.append(str(Path(__file__).parent.parent))
from utils import load_data, format_currency, get_col, format_percentage


st.set_page_config(
    page_title="Clientes RFM - MarketPulse Olist",
    page_icon="👥",
    layout="wide"
)


def main():
    st.title("👥 Segmentación de Clientes RFM")
    st.markdown("**Análisis de valor, frecuencia y recencia de clientes**")
    st.markdown("Clasificación de clientes según su comportamiento de compra para estrategias comerciales.")
    st.markdown("---")
    
    # Cargar datos
    with st.spinner("Cargando datos..."):
        fact_orders, customer_rfm, logistics_enriched = load_data()
    
    # Verificar si existe datos RFM
    if customer_rfm.empty:
        st.error("No se encontraron datos de segmentación RFM (customer_rfm.csv).")
        st.info("Para generar la segmentación RFM, ejecute el notebook de análisis correspondiente.")
        st.stop()
    
    # Usar customer_unique_id para contar clientes
    customer_col = get_col(customer_rfm, ['customer_unique_id', 'customer_id'])
    total_customers = len(customer_rfm) if customer_col else 0
    
    # KPIs de segmentación
    total_monetary = customer_rfm['monetary'].sum() if 'monetary' in customer_rfm.columns else 0
    avg_frequency = customer_rfm['frequency'].mean() if 'frequency' in customer_rfm.columns else 0
    avg_recency = customer_rfm['recency_days'].mean() if 'recency_days' in customer_rfm.columns else 0
    
    # Segmento con más clientes
    if 'customer_segment' in customer_rfm.columns:
        largest_segment = customer_rfm['customer_segment'].value_counts().idxmax()
        largest_segment_count = customer_rfm['customer_segment'].value_counts().max()
    else:
        largest_segment = "N/A"
        largest_segment_count = 0
    
    # Mostrar KPIs principales
    st.subheader("🎯 Indicadores Clave de Segmentación")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Clientes Segmentados", f"{total_customers:,}")
    
    with col2:
        st.metric("Valor Histórico Total", f"R$ {format_currency(total_monetary)}")
    
    with col3:
        st.metric("Frecuencia Promedio", f"{avg_frequency:.2f}")
    
    with col4:
        st.metric("Recencia Promedio", f"{avg_recency:.1f} días")
    
    # Lectura ejecutiva (máximo 3 insights accionables)
    st.subheader("💡 Lectura Ejecutiva")
    
    insights = []
    
    if 'customer_segment' in customer_rfm.columns:
        # Segmento con más clientes
        largest_segment = customer_rfm['customer_segment'].value_counts().idxmax()
        largest_segment_count = customer_rfm['customer_segment'].value_counts().max()
        insights.append(f"👥 **{largest_segment} es el segmento mayoritario** con {largest_segment_count:,} clientes; representa la base principal del negocio.")
    
    if 'customer_segment' in customer_rfm.columns and 'monetary' in customer_rfm.columns:
        # Segmento con mayor valor total
        segment_highest_value = customer_rfm.groupby('customer_segment')['monetary'].sum().idxmax()
        segment_highest_value_amount = customer_rfm.groupby('customer_segment')['monetary'].sum().max()
        insights.append(f"💰 **{segment_highest_value} genera mayor valor histórico** con R$ {format_currency(segment_highest_value_amount)}; es crítico para la sostenibilidad del negocio.")
    
    # Recomendación comercial sobre riesgo de churn
    if 'customer_segment' in customer_rfm.columns:
        churn_risk = customer_rfm[customer_rfm['customer_segment'].isin(['At Risk', 'Lost Customers'])]
        if not churn_risk.empty:
            churn_count = len(churn_risk)
            churn_pct = churn_count / total_customers * 100
            insights.append(f"⚠️ **{churn_count:,} clientes ({churn_pct:.1f}%) están en riesgo de churn**; requieren campañas de reactivación urgentes para recuperar valor.")
    
    # Mostrar máximo 3 insights
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if len(insights) > 0:
            st.info(insights[0])
    
    with col2:
        if len(insights) > 1:
            st.info(insights[1])
    
    with col3:
        if len(insights) > 2:
            st.info(insights[2])
    
    st.markdown("---")
    
    # Explicación de segmentos
    st.subheader("📖 Guía de Segmentos")
    
    segment_explanations = {
        'Champions': 'Clientes valiosos y recientes. Compran frecuentemente y con alto valor. Prioridad máxima para retención.',
        'Loyal Customers': 'Clientes con comportamiento recurrente. Compran regularmente con buen valor. Fidelizados.',
        'Big Spenders': 'Clientes de alto valor monetario. Compran grandes cantidades aunque menos frecuentemente.',
        'At Risk': 'Clientes valiosos o frecuentes que llevan tiempo sin comprar. Requieren reactivación urgente.',
        'Lost Customers': 'Clientes antiguos con baja actividad. Probablemente ya no compran. Requieren campañas de reconquista.',
        'One-time Buyers': 'Clientes con una sola compra. Potencial para convertirse en recurrentes.',
        'New Customers': 'Clientes recientes. Oportunidad de convertir en leales.',
        'Potential Loyalists': 'Clientes recientes con potencial de recurrencia. Compraron bien pero hace poco tiempo.'
    }
    
    if 'customer_segment' in customer_rfm.columns:
        active_segments = customer_rfm['customer_segment'].unique()
        for segment in active_segments:
            if segment in segment_explanations:
                st.info(f"**{segment}:** {segment_explanations[segment]}")
    
    st.markdown("---")
    
    # Acciones sugeridas por segmento
    st.subheader("🎯 Acciones Sugeridas por Segmento")
    
    segment_actions = {
        'Champions': 'Programa de fidelización exclusivo, acceso anticipado a productos, beneficios VIP.',
        'Loyal Customers': 'Ofertas personalizadas, programa de puntos, comunicación regular sobre nuevos productos.',
        'Big Spenders': 'Beneficios premium, atención personalizada, ofertas de alto valor.',
        'At Risk': 'Campañas de reactivación con descuentos agresivos, encuestas de satisfacción, contacto directo.',
        'Lost Customers': 'Campañas de reconquista con ofertas especiales, investigación de causas de abandono.',
        'One-time Buyers': 'Campañas de segunda compra, descuentos por compra recurrente, recomendaciones personalizadas.',
        'New Customers': 'Onboarding optimizado, guía de productos, incentivos para segunda compra.',
        'Potential Loyalists': 'Programa de bienvenida, comunicación de valor, incentivos para aumentar frecuencia.'
    }
    
    if 'customer_segment' in customer_rfm.columns:
        for segment in active_segments:
            if segment in segment_actions:
                st.success(f"**{segment}:** {segment_actions[segment]}")
    
    st.markdown("---")
    
    # Gráficos principales (máximo 4)
    st.subheader("📊 Distribución y Valor por Segmento")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'customer_segment' in customer_rfm.columns:
            segment_counts = customer_rfm['customer_segment'].value_counts().reset_index()
            segment_counts.columns = ['customer_segment', 'count']
            
            fig_segment_counts = px.bar(
                segment_counts,
                x='customer_segment',
                y='count',
                title='Clientes por Segmento',
                template='plotly_white',
                color_discrete_sequence=['#1f77b4']
            )
            fig_segment_counts.update_layout(
                xaxis_title='Segmento',
                yaxis_title='Clientes',
                showlegend=False
            )
            st.plotly_chart(fig_segment_counts, width='stretch')
    
    with col2:
        if 'customer_segment' in customer_rfm.columns and 'monetary' in customer_rfm.columns:
            segment_monetary = customer_rfm.groupby('customer_segment')['monetary'].sum().reset_index()
            
            fig_segment_monetary = px.bar(
                segment_monetary,
                x='customer_segment',
                y='monetary',
                title='Valor Histórico Total por Segmento',
                template='plotly_white',
                color_discrete_sequence=['#1f77b4']
            )
            fig_segment_monetary.update_layout(
                xaxis_title='Segmento',
                yaxis_title='Valor (R$)',
                showlegend=False
            )
            st.plotly_chart(fig_segment_monetary, width='stretch')
    
    col3, col4 = st.columns(2)
    
    with col3:
        if 'customer_segment' in customer_rfm.columns and 'monetary' in customer_rfm.columns:
            segment_avg_monetary = customer_rfm.groupby('customer_segment')['monetary'].mean().reset_index()
            
            fig_avg_monetary = px.bar(
                segment_avg_monetary,
                x='customer_segment',
                y='monetary',
                title='Valor Promedio por Segmento',
                template='plotly_white',
                color_discrete_sequence=['#1f77b4']
            )
            fig_avg_monetary.update_layout(
                xaxis_title='Segmento',
                yaxis_title='Valor Promedio (R$)',
                showlegend=False
            )
            st.plotly_chart(fig_avg_monetary, width='stretch')
    
    with col4:
        if 'customer_segment' in customer_rfm.columns and 'recency_days' in customer_rfm.columns:
            segment_recency = customer_rfm.groupby('customer_segment')['recency_days'].mean().reset_index()
            
            fig_recency = px.bar(
                segment_recency,
                x='customer_segment',
                y='recency_days',
                title='Recencia Promedio por Segmento',
                template='plotly_white',
                color_discrete_sequence=['#1f77b4']
            )
            fig_recency.update_layout(
                xaxis_title='Segmento',
                yaxis_title='Recencia (días)',
                showlegend=False
            )
            st.plotly_chart(fig_recency, width='stretch')
    
    st.markdown("---")
    
    # Análisis exploratorio avanzado en expander
    with st.expander("🔍 Ver análisis exploratorio avanzado"):
        st.subheader("Análisis de Frecuencia vs Valor")
        
        if 'frequency' in customer_rfm.columns and 'monetary' in customer_rfm.columns:
            fig_scatter_fm = px.scatter(
                customer_rfm,
                x='frequency',
                y='monetary',
                color='customer_segment' if 'customer_segment' in customer_rfm.columns else None,
                title='Frecuencia vs Valor por Segmento',
                template='plotly_white'
            )
            fig_scatter_fm.update_layout(
                xaxis_title='Frecuencia',
                yaxis_title='Valor (R$)',
                showlegend=True
            )
            st.plotly_chart(fig_scatter_fm, width='stretch')
    
    st.markdown("---")
    
    # Tabla resumen por segmento
    st.subheader("📋 Resumen Ejecutivo por Segmento")
    
    if 'customer_segment' in customer_rfm.columns:
        segment_table = customer_rfm.groupby('customer_segment').agg({
            customer_col: 'count' if customer_col else 'size',
            'monetary': ['sum', 'mean'],
            'frequency': 'mean',
            'recency_days': 'mean'
        }).reset_index()
        
        segment_table.columns = ['Segmento', 'Clientes', 'Valor Total', 'Valor Promedio', 'Frecuencia Promedio', 'Recencia Promedio (días)']
        
        # Formatear columnas numéricas
        segment_table['Valor Total'] = segment_table['Valor Total'].apply(lambda x: f"R$ {x:,.0f}")
        segment_table['Valor Promedio'] = segment_table['Valor Promedio'].apply(lambda x: f"R$ {x:.2f}")
        segment_table['Frecuencia Promedio'] = segment_table['Frecuencia Promedio'].apply(lambda x: f"{x:.2f}")
        segment_table['Recencia Promedio (días)'] = segment_table['Recencia Promedio (días)'].apply(lambda x: f"{x:.1f}")
        
        segment_table = segment_table.sort_values('Clientes', ascending=False)
        
        st.dataframe(segment_table, width='stretch', hide_index=True)


if __name__ == "__main__":
    main()
