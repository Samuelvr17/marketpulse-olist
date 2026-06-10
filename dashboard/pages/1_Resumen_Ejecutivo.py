import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

# Agregar el directorio padre al path para importar utils
sys.path.append(str(Path(__file__).parent.parent))
from utils import load_data, prepare_fact_orders, apply_filters, format_currency, format_percentage, calculate_kpis, get_col


st.set_page_config(
    page_title="Resumen Ejecutivo - MarketPulse Olist",
    page_icon="📋",
    layout="wide"
)


def main():
    st.title("📋 Resumen Ejecutivo")
    st.markdown("**Visión general del desempeño comercial del marketplace**")
    st.markdown("Análisis ejecutivo de ventas, clientes, satisfacción y operación logística.")
    st.markdown("---")
    
    # Cargar datos
    with st.spinner("Cargando datos..."):
        fact_orders, customer_rfm, logistics_enriched = load_data()
        
        if fact_orders.empty:
            st.error("No se pudieron cargar los datos de órdenes.")
            st.stop()
        
        fact_orders = prepare_fact_orders(fact_orders)
    
    # Aplicar filtros
    fact_orders_filtered = apply_filters(fact_orders)
    
    # Calcular KPIs
    kpis = calculate_kpis(fact_orders_filtered)
    
    # Mostrar KPIs principales (máximo 8)
    st.subheader("🎯 Indicadores Clave de Negocio")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Valor Pagado", f"R$ {format_currency(kpis.get('total_payment_value', 0))}")
    
    with col2:
        st.metric("Órdenes", f"{kpis.get('total_orders', 0):,}")
    
    with col3:
        st.metric("Clientes Únicos", f"{kpis.get('unique_customers', 0):,}")
    
    with col4:
        st.metric("Ticket Promedio", f"R$ {format_currency(kpis.get('average_order_value', 0))}")
    
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        st.metric("Review Promedio", f"{kpis.get('average_review_score', 0):.2f} ⭐")
    
    with col6:
        st.metric("Tasa Entrega Tardía", format_percentage(kpis.get('late_delivery_rate', 0)))
    
    with col7:
        st.metric("Tasa Mala Reseña", format_percentage(kpis.get('bad_review_rate', 0)))
    
    with col8:
        st.metric("Tasa Cancelación", format_percentage(kpis.get('cancellation_rate', 0)))
    
    # Lectura ejecutiva (máximo 3 insights accionables)
    st.subheader("💡 Lectura Ejecutiva")
    
    # Calcular insights automáticos
    payment_col = get_col(fact_orders_filtered, ['payment_total', 'payment_value'])
    
    insights = []
    
    if 'main_category' in fact_orders_filtered.columns and payment_col:
        # Categoría líder por valor pagado (excluir Sin dato)
        category_filtered = fact_orders_filtered[fact_orders_filtered['main_category'] != 'Sin dato']
        if not category_filtered.empty:
            best_category = category_filtered.groupby('main_category')[payment_col].sum().idxmax()
            best_category_value = category_filtered.groupby('main_category')[payment_col].sum().max()
            if best_category:
                insights.append(f"🏷️ **{best_category} lidera el valor pagado** con R$ {format_currency(best_category_value)}; es la categoría más relevante para priorización comercial.")
    
    late_rate = kpis.get('late_delivery_rate', 0)
    if late_rate > 0.10:
        insights.append(f"🚚 **La tasa de entrega tardía es {format_percentage(late_rate)}**, lo que impacta negativamente en la satisfacción del cliente; se requiere revisión de operadores logísticos.")
    
    bad_rate = kpis.get('bad_review_rate', 0)
    if bad_rate > 0.10:
        insights.append(f"⭐ **La tasa de mala reseña es {format_percentage(bad_rate)}**, indicando oportunidades de mejora en experiencia del cliente y calidad del producto.")
    
    # Si no hay suficientes insights, agregar uno genérico
    if len(insights) < 3 and payment_col:
        total_value = kpis.get('total_payment_value', 0)
        insights.append(f"💰 **El valor pagado total es R$ {format_currency(total_value)}**, reflejando el desempeño comercial del periodo analizado.")
    
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
    
    # Gráficos principales (máximo 4)
    st.subheader("📊 Evolución y Concentración de Ventas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if payment_col:
            revenue_by_month = fact_orders_filtered.groupby('purchase_year_month')[payment_col].sum().reset_index()
            revenue_by_month = revenue_by_month.sort_values('purchase_year_month')
            
            fig_revenue_month = px.line(
                revenue_by_month,
                x='purchase_year_month',
                y=payment_col,
                title='Evolución del Valor Pagado',
                markers=True,
                template='plotly_white',
                color_discrete_sequence=['#1f77b4']
            )
            fig_revenue_month.update_layout(
                xaxis_title='Mes',
                yaxis_title='Valor Pagado (R$)',
                showlegend=False
            )
            st.plotly_chart(fig_revenue_month, width='stretch')
    
    with col2:
        if 'customer_state' in fact_orders_filtered.columns and payment_col:
            top_states = fact_orders_filtered.groupby('customer_state')[payment_col].sum().nlargest(10).reset_index()
            
            fig_top_states = px.bar(
                top_states,
                x=payment_col,
                y='customer_state',
                orientation='h',
                title='Top 10 Estados por Valor Pagado',
                template='plotly_white',
                color_discrete_sequence=['#1f77b4']
            )
            fig_top_states.update_layout(
                xaxis_title='Valor Pagado (R$)',
                yaxis_title='Estado',
                showlegend=False
            )
            st.plotly_chart(fig_top_states, width='stretch')
    
    col3, col4 = st.columns(2)
    
    with col3:
        if 'main_category' in fact_orders_filtered.columns and payment_col:
            # Excluir Sin dato de rankings ejecutivos
            category_filtered = fact_orders_filtered[fact_orders_filtered['main_category'] != 'Sin dato']
            if not category_filtered.empty:
                top_categories = category_filtered.groupby('main_category')[payment_col].sum().nlargest(10).reset_index()
                
                fig_top_categories = px.bar(
                    top_categories,
                    x=payment_col,
                    y='main_category',
                    orientation='h',
                    title='Top 10 Categorías por Valor Pagado',
                    template='plotly_white',
                    color_discrete_sequence=['#1f77b4']
                )
                fig_top_categories.update_layout(
                    xaxis_title='Valor Pagado (R$)',
                    yaxis_title='Categoría',
                    showlegend=False
                )
                st.plotly_chart(fig_top_categories, width='stretch')
    
    with col4:
        if 'order_status' in fact_orders_filtered.columns:
            status_dist = fact_orders_filtered['order_status'].value_counts().reset_index()
            status_dist.columns = ['order_status', 'count']
            
            fig_status = px.bar(
                status_dist,
                x='order_status',
                y='count',
                title='Distribución de Estados de Orden',
                template='plotly_white',
                color_discrete_sequence=['#1f77b4']
            )
            fig_status.update_layout(
                xaxis_title='Estado',
                yaxis_title='Órdenes',
                showlegend=False
            )
            st.plotly_chart(fig_status, width='stretch')
    
    st.markdown("---")
    
    # Análisis exploratorio avanzado en expander
    with st.expander("� Ver análisis exploratorio avanzado"):
        st.subheader("Análisis Detallado de Órdenes por Mes")
        
        orders_by_month = fact_orders_filtered.groupby('purchase_year_month').size().reset_index(name='orders')
        orders_by_month = orders_by_month.sort_values('purchase_year_month')
        
        fig_orders_month = px.line(
            orders_by_month,
            x='purchase_year_month',
            y='orders',
            title='Órdenes por Mes',
            markers=True,
            template='plotly_white'
        )
        fig_orders_month.update_layout(
            xaxis_title='Mes',
            yaxis_title='Órdenes',
            showlegend=False
        )
        st.plotly_chart(fig_orders_month, width='stretch')
    
    st.markdown("---")
    
    # Tabla de detalle
    st.subheader("📋 Resumen por Estado")
    
    if 'customer_state' in fact_orders_filtered.columns:
        state_table = fact_orders_filtered.groupby('customer_state').agg({
            'order_id': 'count'
        }).reset_index()
        state_table.columns = ['Estado', 'Órdenes']
        
        if payment_col:
            state_table['Valor Pagado'] = fact_orders_filtered.groupby('customer_state')[payment_col].sum().values
        
        if 'review_score_avg' in fact_orders_filtered.columns:
            state_table['Review Promedio'] = fact_orders_filtered.groupby('customer_state')['review_score_avg'].mean().values
        
        if 'is_late' in fact_orders_filtered.columns:
            state_table['Tasa Tardía'] = fact_orders_filtered.groupby('customer_state')['is_late'].mean().values
        
        # Formatear columnas
        if 'Valor Pagado' in state_table.columns:
            state_table['Valor Pagado'] = state_table['Valor Pagado'].apply(lambda x: f"R$ {x:,.0f}")
        if 'Review Promedio' in state_table.columns:
            state_table['Review Promedio'] = state_table['Review Promedio'].apply(lambda x: f"{x:.2f}")
        if 'Tasa Tardía' in state_table.columns:
            state_table['Tasa Tardía'] = state_table['Tasa Tardía'].apply(format_percentage)
        
        state_table = state_table.sort_values('Órdenes', ascending=False)
        st.dataframe(state_table, width='stretch', hide_index=True)


if __name__ == "__main__":
    main()
