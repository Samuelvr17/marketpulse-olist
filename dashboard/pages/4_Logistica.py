import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

# Agregar el directorio padre al path para importar utils
sys.path.append(str(Path(__file__).parent.parent))
from utils import load_data, prepare_fact_orders, apply_filters, format_currency, format_percentage, get_col


st.set_page_config(
    page_title="Logística - MarketPulse Olist",
    page_icon="🚚",
    layout="wide"
)


def main():
    st.title("🚚 Logística y Entregas")
    st.markdown("**Análisis de tiempos de entrega y desempeño operativo**")
    st.markdown("Evaluación de eficiencia logística, retrasos y costos de envío por geografía y categoría.")
    st.markdown("---")
    
    # Cargar datos
    with st.spinner("Cargando datos..."):
        fact_orders, customer_rfm, logistics_enriched = load_data()
        
        if fact_orders.empty:
            st.error("No se pudieron cargar los datos de órdenes.")
            st.stop()
        
        fact_orders = prepare_fact_orders(fact_orders)
    
    # Verificar si existe logistics_enriched
    use_logistics = not logistics_enriched.empty
    
    if use_logistics:
        df = logistics_enriched.copy()
    else:
        df = fact_orders.copy()
    
    # Aplicar filtros
    df_filtered = apply_filters(df)
    
    # Filtrar solo órdenes entregadas para análisis logístico
    delivered = df_filtered[df_filtered['order_status'] == 'delivered'].copy()
    
    if delivered.empty:
        st.warning("No hay órdenes entregadas en el filtro seleccionado.")
        st.stop()
    
    # Calcular KPIs logísticos
    delivered_orders = len(delivered)
    
    if 'delivery_time_days' in delivered.columns:
        avg_delivery_time = delivered['delivery_time_days'].mean()
        median_delivery_time = delivered['delivery_time_days'].median()
    else:
        avg_delivery_time = 0
        median_delivery_time = 0
    
    late_col = get_col(delivered, ['is_late', 'delivery_late'])
    if late_col:
        late_delivery_rate = delivered[late_col].mean()
    else:
        late_delivery_rate = 0
    
    if 'delivery_delay_days' in delivered.columns:
        avg_delay = delivered[delivered['delivery_delay_days'] > 0]['delivery_delay_days'].mean() if len(delivered[delivered['delivery_delay_days'] > 0]) > 0 else 0
    else:
        avg_delay = 0
    
    freight_col = get_col(delivered, ['total_freight', 'freight_value'])
    if freight_col:
        avg_freight = delivered[freight_col].mean()
    else:
        avg_freight = 0
    
    if 'avg_distance_km' in delivered.columns:
        avg_distance = delivered['avg_distance_km'].mean()
    else:
        avg_distance = None
    
    # Mostrar KPIs principales (5 KPIs)
    st.subheader("🎯 Indicadores Clave de Logística")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Órdenes Entregadas", f"{delivered_orders:,}")
    
    with col2:
        st.metric("Tiempo Promedio", f"{avg_delivery_time:.1f} días")
    
    with col3:
        st.metric("Tasa Tardía", format_percentage(late_delivery_rate))
    
    with col4:
        st.metric("Retraso Promedio", f"{avg_delay:.1f} días")
    
    with col5:
        st.metric("Flete Promedio", f"R$ {format_currency(avg_freight)}")
    
    # Lectura ejecutiva (máximo 3 insights accionables)
    st.subheader("💡 Lectura Ejecutiva")
    
    insights = []
    
    # Estado con peor tiempo de entrega
    if 'customer_state' in delivered.columns and 'delivery_time_days' in delivered.columns:
        worst_state = delivered.groupby('customer_state')['delivery_time_days'].mean().idxmax()
        worst_state_time = delivered.groupby('customer_state')['delivery_time_days'].mean().max()
        insights.append(f"🗺️ **{worst_state} tiene mayor tiempo de entrega** con {worst_state_time:.1f} días promedio; debe priorizarse para revisión logística.")
    
    # Categoría con mayor tiempo de entrega (excluir Sin dato)
    if 'main_category' in delivered.columns and 'delivery_time_days' in delivered.columns:
        category_filtered = delivered[delivered['main_category'] != 'Sin dato']
        if not category_filtered.empty:
            slowest_category = category_filtered.groupby('main_category')['delivery_time_days'].mean().idxmax()
            slowest_category_time = category_filtered.groupby('main_category')['delivery_time_days'].mean().max()
            insights.append(f"📦 **{slowest_category} tiene mayor tiempo de entrega** con {slowest_category_time:.1f} días promedio; requiere revisión de procesos logísticos específicos.")
    
    # Tasa tardía
    if late_delivery_rate > 0.10:
        insights.append(f"⚠️ **La tasa de entrega tardía es {format_percentage(late_delivery_rate)}**, lo que impacta negativamente en la satisfacción del cliente; se requiere optimización de operadores.")
    
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
    st.subheader("📊 Evolución y Desempeño Logístico")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'purchase_year_month' in delivered.columns and late_col:
            # Excluir meses con menos de 100 órdenes entregadas
            month_counts = delivered.groupby('purchase_year_month').size()
            valid_months = month_counts[month_counts >= 100].index
            delivered_filtered = delivered[delivered['purchase_year_month'].isin(valid_months)]
            
            if not delivered_filtered.empty:
                late_by_month = delivered_filtered.groupby('purchase_year_month')[late_col].mean().reset_index()
                late_by_month = late_by_month.sort_values('purchase_year_month')
                
                fig_late_month = px.line(
                    late_by_month,
                    x='purchase_year_month',
                    y=late_col,
                    title='Evolución de Entregas Tardías (mín. 100 entregas/mes)',
                    markers=True,
                    template='plotly_white',
                    color_discrete_sequence=['#1f77b4']
                )
                fig_late_month.update_layout(
                    xaxis_title='Mes',
                    yaxis_title='Tasa de Entrega Tardía',
                    showlegend=False
                )
                st.plotly_chart(fig_late_month, width='stretch')
            else:
                st.warning("No hay suficientes datos mensuales (mín. 100 entregas/mes) para mostrar la evolución.")
    
    with col2:
        if 'customer_state' in delivered.columns and 'delivery_time_days' in delivered.columns:
            state_delivery = delivered.groupby('customer_state')['delivery_time_days'].mean().nlargest(10).reset_index()
            
            fig_state_delivery = px.bar(
                state_delivery,
                x='delivery_time_days',
                y='customer_state',
                orientation='h',
                title='Top 10 Estados con Mayor Tiempo de Entrega',
                template='plotly_white',
                color_discrete_sequence=['#1f77b4']
            )
            fig_state_delivery.update_layout(
                xaxis_title='Tiempo Promedio (días)',
                yaxis_title='Estado',
                showlegend=False
            )
            st.plotly_chart(fig_state_delivery, width='stretch')
    
    col3, col4 = st.columns(2)
    
    with col3:
        if 'main_category' in delivered.columns and 'delivery_time_days' in delivered.columns:
            # Excluir Sin dato de rankings ejecutivos
            category_filtered = delivered[delivered['main_category'] != 'Sin dato']
            if not category_filtered.empty:
                category_delivery = category_filtered.groupby('main_category')['delivery_time_days'].mean().nlargest(10).reset_index()
                
                fig_category_delivery = px.bar(
                    category_delivery,
                    x='delivery_time_days',
                    y='main_category',
                    orientation='h',
                    title='Top 10 Categorías con Mayor Tiempo de Entrega',
                    template='plotly_white',
                    color_discrete_sequence=['#1f77b4']
                )
                fig_category_delivery.update_layout(
                    xaxis_title='Tiempo Promedio (días)',
                    yaxis_title='Categoría',
                    showlegend=False
                )
                st.plotly_chart(fig_category_delivery, width='stretch')
    
    with col4:
        if 'customer_state' in delivered.columns and late_col:
            state_late = delivered.groupby('customer_state')[late_col].mean().nlargest(10).reset_index()
            
            fig_state_late = px.bar(
                state_late,
                x=late_col,
                y='customer_state',
                orientation='h',
                title='Top 10 Estados con Mayor Tasa Tardía',
                template='plotly_white',
                color_discrete_sequence=['#1f77b4']
            )
            fig_state_late.update_layout(
                xaxis_title='Tasa de Entrega Tardía',
                yaxis_title='Estado',
                showlegend=False
            )
            st.plotly_chart(fig_state_late, width='stretch')
    
    st.markdown("---")
    
    # Análisis exploratorio avanzado en expander
    with st.expander("🔍 Ver análisis exploratorio avanzado"):
        st.subheader("Distribución de Tiempos de Entrega")
        
        if 'delivery_time_days' in delivered.columns:
            # Limitar al percentil 99 visualmente
            p99 = delivered['delivery_time_days'].quantile(0.99)
            delivery_limited = delivered[delivered['delivery_time_days'] <= p99]
            
            fig_delivery_time = px.histogram(
                delivery_limited,
                x='delivery_time_days',
                title='Distribución de Tiempo de Entrega',
                template='plotly_white',
                nbins=50
            )
            fig_delivery_time.update_layout(
                xaxis_title='Días',
                yaxis_title='Órdenes',
                showlegend=False
            )
            st.plotly_chart(fig_delivery_time, width='stretch')
        
        st.markdown("---")
        
        # Análisis de distancia si está disponible
        if avg_distance is not None:
            st.subheader("Análisis de Distancia vs Flete")
            
            if 'avg_distance_km' in delivered.columns and freight_col:
                fig_dist_freight = px.scatter(
                    delivered,
                    x='avg_distance_km',
                    y=freight_col,
                    title='Relación Distancia vs Flete',
                    template='plotly_white',
                    opacity=0.5
                )
                fig_dist_freight.update_layout(
                    xaxis_title='Distancia (km)',
                    yaxis_title='Flete (R$)',
                    showlegend=False
                )
                st.plotly_chart(fig_dist_freight, width='stretch')
    
    st.markdown("---")
    
    # Tabla por estado
    st.subheader("📋 Resumen Ejecutivo por Estado")
    
    if 'customer_state' in delivered.columns:
        state_table = delivered.groupby('customer_state').agg({
            'order_id': 'count',
            'delivery_time_days': 'mean',
        }).reset_index()
        state_table.columns = ['Estado', 'Órdenes Entregadas', 'Tiempo Promedio']
        
        if late_col:
            state_table['Tasa Tardía'] = delivered.groupby('customer_state')[late_col].mean().values
        
        if freight_col:
            state_table['Flete Promedio'] = delivered.groupby('customer_state')[freight_col].mean().values
        
        if 'review_score_avg' in delivered.columns:
            state_table['Review Promedio'] = delivered.groupby('customer_state')['review_score_avg'].mean().values
        
        # Formatear columnas
        state_table['Tiempo Promedio'] = state_table['Tiempo Promedio'].apply(lambda x: f"{x:.1f} días")
        if 'Tasa Tardía' in state_table.columns:
            state_table['Tasa Tardía'] = state_table['Tasa Tardía'].apply(format_percentage)
        if 'Flete Promedio' in state_table.columns:
            state_table['Flete Promedio'] = state_table['Flete Promedio'].apply(lambda x: f"R$ {x:.2f}")
        if 'Review Promedio' in state_table.columns:
            state_table['Review Promedio'] = state_table['Review Promedio'].apply(lambda x: f"{x:.2f}")
        
        state_table = state_table.sort_values('Órdenes Entregadas', ascending=False)
        
        st.dataframe(state_table, width='stretch', hide_index=True)


if __name__ == "__main__":
    main()
