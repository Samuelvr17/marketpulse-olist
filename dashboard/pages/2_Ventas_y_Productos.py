import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

# Agregar el directorio padre al path para importar utils
sys.path.append(str(Path(__file__).parent.parent))
from utils import load_data, prepare_fact_orders, apply_filters, format_currency, format_percentage, get_col, format_category_name


st.set_page_config(
    page_title="Ventas y Productos - MarketPulse Olist",
    page_icon="💰",
    layout="wide"
)


def main():
    st.title("💰 Ventas y Productos")
    st.markdown("**Análisis de desempeño comercial por categoría de producto**")
    st.markdown("Evaluación de valor pagado, volumen de órdenes y ticket promedio por categoría.")
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
    
    # Calcular KPIs específicos de ventas
    price_col = get_col(fact_orders_filtered, ['total_price', 'price'])
    payment_col = get_col(fact_orders_filtered, ['payment_total', 'payment_value'])
    
    total_revenue_items = fact_orders_filtered[price_col].sum() if price_col else 0
    total_payment_value = fact_orders_filtered[payment_col].sum() if payment_col else 0
    total_orders = len(fact_orders_filtered)
    average_order_value = fact_orders_filtered[payment_col].mean() if payment_col else 0
    
    # Categorías activas
    active_categories = fact_orders_filtered['main_category'].nunique() if 'main_category' in fact_orders_filtered.columns else 0
    
    # Mostrar KPIs principales
    st.subheader("🎯 Indicadores Clave de Ventas")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Valor Pagado", f"R$ {format_currency(total_payment_value)}")
    
    with col2:
        st.metric("Órdenes", f"{total_orders:,}")
    
    with col3:
        st.metric("Ticket Promedio", f"R$ {format_currency(average_order_value)}")
    
    with col4:
        st.metric("Categorías Activas", f"{active_categories}")
    
    # Lectura ejecutiva (máximo 3 insights accionables)
    st.subheader("💡 Lectura Ejecutiva")
    
    insights = []
    
    if payment_col and 'main_category' in fact_orders_filtered.columns:
        # Categoría con mayor valor pagado (excluir Sin dato)
        category_filtered = fact_orders_filtered[fact_orders_filtered['main_category'] != 'Sin dato']
        if not category_filtered.empty:
            best_category = category_filtered.groupby('main_category')[payment_col].sum().idxmax()
            best_category_value = category_filtered.groupby('main_category')[payment_col].sum().max()
            if best_category:
                insights.append(f"🏆 **{best_category} lidera el valor pagado** con R$ {format_currency(best_category_value)}; es la categoría más relevante para priorización comercial.")
    
    if 'main_category' in fact_orders_filtered.columns:
        # Categoría con más órdenes (excluir Sin dato)
        category_filtered = fact_orders_filtered[fact_orders_filtered['main_category'] != 'Sin dato']
        if not category_filtered.empty:
            most_orders_category = category_filtered.groupby('main_category').size().idxmax()
            most_orders_count = category_filtered.groupby('main_category').size().max()
            if most_orders_category:
                insights.append(f"📦 **{most_orders_category} tiene mayor volumen** con {most_orders_count:,} órdenes; indica alta demanda y necesidad de inventario.")
    
    if payment_col and 'main_category' in fact_orders_filtered.columns:
        # Categoría con mejor ticket (excluir Sin dato)
        category_filtered = fact_orders_filtered[fact_orders_filtered['main_category'] != 'Sin dato']
        if not category_filtered.empty:
            best_ticket_category = category_filtered.groupby('main_category')[payment_col].mean().idxmax()
            best_ticket_value = category_filtered.groupby('main_category')[payment_col].mean().max()
            if best_ticket_category:
                insights.append(f"💎 **{best_ticket_category} tiene el mejor ticket** con R$ {format_currency(best_ticket_value)}; representa oportunidad para estrategias de up-selling.")
    
    # Mostrar insights
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
    st.subheader("📊 Evolución y Desempeño por Categoría")
    
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
        if 'main_category' in fact_orders_filtered.columns and payment_col:
            # Excluir Sin dato de rankings ejecutivos
            category_filtered = fact_orders_filtered[fact_orders_filtered['main_category'] != 'Sin dato']
            if not category_filtered.empty:
                top_categories_revenue = category_filtered.groupby('main_category')[payment_col].sum().nlargest(10).reset_index()
                
                fig_top_revenue = px.bar(
                    top_categories_revenue,
                    x=payment_col,
                    y='main_category',
                    orientation='h',
                    title='Top 10 Categorías por Valor Pagado',
                    template='plotly_white',
                    color_discrete_sequence=['#1f77b4']
                )
                fig_top_revenue.update_layout(
                    xaxis_title='Valor Pagado (R$)',
                    yaxis_title='Categoría',
                    showlegend=False
                )
                st.plotly_chart(fig_top_revenue, width='stretch')
    
    col3, col4 = st.columns(2)
    
    with col3:
        if 'main_category' in fact_orders_filtered.columns:
            # Excluir Sin dato de rankings ejecutivos
            category_filtered = fact_orders_filtered[fact_orders_filtered['main_category'] != 'Sin dato']
            if not category_filtered.empty:
                top_categories_orders = category_filtered.groupby('main_category').size().nlargest(10).reset_index(name='orders')
                
                fig_top_orders = px.bar(
                    top_categories_orders,
                    x='orders',
                    y='main_category',
                    orientation='h',
                    title='Top 10 Categorías por Órdenes',
                    template='plotly_white',
                    color_discrete_sequence=['#1f77b4']
                )
                fig_top_orders.update_layout(
                    xaxis_title='Órdenes',
                    yaxis_title='Categoría',
                    showlegend=False
                )
                st.plotly_chart(fig_top_orders, width='stretch')
    
    with col4:
        if 'main_category' in fact_orders_filtered.columns and payment_col:
            # Excluir Sin dato de rankings ejecutivos
            category_filtered = fact_orders_filtered[fact_orders_filtered['main_category'] != 'Sin dato']
            if not category_filtered.empty:
                ticket_by_category = category_filtered.groupby('main_category')[payment_col].mean().nlargest(10).reset_index()
                ticket_by_category.columns = ['main_category', 'avg_ticket']
                
                fig_ticket = px.bar(
                    ticket_by_category,
                    x='avg_ticket',
                    y='main_category',
                    orientation='h',
                    title='Top 10 Ticket Promedio por Categoría',
                    template='plotly_white',
                    color_discrete_sequence=['#1f77b4']
                )
                fig_ticket.update_layout(
                    xaxis_title='Ticket Promedio (R$)',
                    yaxis_title='Categoría',
                    showlegend=False
                )
                st.plotly_chart(fig_ticket, width='stretch')
    
    st.markdown("---")
    
    # Análisis exploratorio avanzado en expander
    with st.expander("🔍 Ver análisis exploratorio avanzado"):
        st.subheader("Análisis Detallado por Categoría")
        
        if 'main_category' in fact_orders_filtered.columns and price_col:
            gmv_by_category = fact_orders_filtered.groupby('main_category')[price_col].sum().nlargest(15).reset_index()
            
            fig_gmv = px.bar(
                gmv_by_category,
                x=price_col,
                y='main_category',
                orientation='h',
                title='Top 15 GMV Productos por Categoría',
                template='plotly_white',
                color_discrete_sequence=['#1f77b4']
            )
            fig_gmv.update_layout(
                xaxis_title='GMV Productos (R$)',
                yaxis_title='Categoría',
                showlegend=False
            )
            st.plotly_chart(fig_gmv, width='stretch')
    
    st.markdown("---")
    
    # Tabla ejecutiva por categoría
    st.subheader("📋 Resumen Ejecutivo por Categoría")
    
    if 'main_category' in fact_orders_filtered.columns:
        category_table = fact_orders_filtered.groupby('main_category').agg({
            'order_id': 'count'
        }).reset_index()
        category_table.columns = ['Categoría', 'Órdenes']
        
        if payment_col:
            category_table['Valor Pagado'] = fact_orders_filtered.groupby('main_category')[payment_col].sum().values
        
        if price_col:
            category_table['GMV Productos'] = fact_orders_filtered.groupby('main_category')[price_col].sum().values
        
        if payment_col:
            category_table['Ticket Promedio'] = category_table['Valor Pagado'] / category_table['Órdenes']
        
        if 'review_score_avg' in fact_orders_filtered.columns:
            category_table['Review Promedio'] = fact_orders_filtered.groupby('main_category')['review_score_avg'].mean().values
        
        if 'is_late' in fact_orders_filtered.columns:
            category_table['Tasa Tardía'] = fact_orders_filtered.groupby('main_category')['is_late'].mean().values
        
        if 'bad_review' in fact_orders_filtered.columns:
            category_table['Tasa Mala Reseña'] = fact_orders_filtered.groupby('main_category')['bad_review'].mean().values
        elif 'review_score_avg' in fact_orders_filtered.columns:
            bad_review_by_category = fact_orders_filtered[fact_orders_filtered['review_score_avg'] <= 2].groupby('main_category').size() / fact_orders_filtered.groupby('main_category').size()
            category_table['Tasa Mala Reseña'] = category_table['Categoría'].map(bad_review_by_category).fillna(0)
        
        # Formatear columnas numéricas
        if 'Valor Pagado' in category_table.columns:
            category_table['Valor Pagado'] = category_table['Valor Pagado'].apply(lambda x: f"R$ {x:,.0f}")
        if 'GMV Productos' in category_table.columns:
            category_table['GMV Productos'] = category_table['GMV Productos'].apply(lambda x: f"R$ {x:,.0f}")
        if 'Ticket Promedio' in category_table.columns:
            category_table['Ticket Promedio'] = category_table['Ticket Promedio'].apply(lambda x: f"R$ {x:.2f}")
        if 'Review Promedio' in category_table.columns:
            category_table['Review Promedio'] = category_table['Review Promedio'].apply(lambda x: f"{x:.2f}")
        if 'Tasa Tardía' in category_table.columns:
            category_table['Tasa Tardía'] = category_table['Tasa Tardía'].apply(format_percentage)
        if 'Tasa Mala Reseña' in category_table.columns:
            category_table['Tasa Mala Reseña'] = category_table['Tasa Mala Reseña'].apply(format_percentage)
        
        # Ordenar por valor pagado
        category_table = category_table.sort_values('Órdenes', ascending=False)
        
        st.dataframe(category_table, width='stretch', hide_index=True)


if __name__ == "__main__":
    main()
