import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

# Agregar el directorio padre al path para importar utils
sys.path.append(str(Path(__file__).parent.parent))
from utils import load_data, prepare_fact_orders, apply_filters, format_percentage, get_col


st.set_page_config(
    page_title="Satisfacción - MarketPulse Olist",
    page_icon="⭐",
    layout="wide"
)


def main():
    st.title("⭐ Satisfacción del Cliente")
    st.markdown("**Análisis de reseñas y experiencia del cliente**")
    st.markdown("Evaluación de calificaciones, mala reseña y el impacto de la entrega en la satisfacción.")
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
    
    # Filtrar órdenes con review
    if 'review_score_avg' in fact_orders_filtered.columns:
        with_review = fact_orders_filtered[fact_orders_filtered['review_score_avg'].notna()].copy()
    else:
        st.error("No se encontraron datos de reviews en el dataset.")
        st.stop()
    
    if with_review.empty:
        st.warning("No hay órdenes con reviews en el filtro seleccionado.")
        st.stop()
    
    # Calcular KPIs de satisfacción
    orders_with_review = len(with_review)
    avg_review = with_review['review_score_avg'].mean()
    bad_reviews = len(with_review[with_review['review_score_avg'] <= 2])
    bad_review_rate = bad_reviews / orders_with_review if orders_with_review > 0 else 0
    good_reviews = len(with_review[with_review['review_score_avg'] >= 4])
    good_review_rate = good_reviews / orders_with_review if orders_with_review > 0 else 0
    
    # Órdenes con comentario
    if 'has_review_comment' in with_review.columns:
        orders_with_comment = with_review['has_review_comment'].sum()
    else:
        orders_with_comment = 0
    
    # Crear grupo de retraso
    if 'delivery_delay_days' in with_review.columns:
        def categorize_delay(delay):
            if pd.isna(delay):
                return 'Sin dato'
            elif delay < 0:
                return 'Anticipada'
            elif delay == 0:
                return 'A tiempo'
            elif delay <= 3:
                return 'Retraso leve (1-3 días)'
            elif delay <= 7:
                return 'Retraso medio (4-7 días)'
            else:
                return 'Retraso alto (8+ días)'
        
        with_review['delay_group'] = with_review['delivery_delay_days'].apply(categorize_delay)
    
    # Mostrar KPIs principales
    st.subheader("🎯 Indicadores Clave de Satisfacción")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Review Promedio", f"{avg_review:.2f} ⭐")
    
    with col2:
        st.metric("Tasa Mala Reseña", format_percentage(bad_review_rate))
    
    with col3:
        st.metric("Tasa Buena Reseña", format_percentage(good_review_rate))
    
    with col4:
        st.metric("Órdenes con Reseña", f"{orders_with_review:,}")
    
    # Lectura ejecutiva
    st.subheader("💡 Lectura Ejecutiva")
    
    insights = []
    
    # Categoría con peor review (excluir Sin dato y mínimo 100 reseñas)
    if 'main_category' in with_review.columns:
        category_counts = with_review.groupby('main_category').size()
        valid_categories = category_counts[category_counts >= 100].index
        category_filtered = with_review[with_review['main_category'].isin(valid_categories)]
        category_filtered = category_filtered[category_filtered['main_category'] != 'Sin dato']
        if not category_filtered.empty:
            worst_category = category_filtered.groupby('main_category')['review_score_avg'].mean().idxmin()
            worst_category_score = category_filtered.groupby('main_category')['review_score_avg'].mean().min()
            insights.append(f"🏷️ **{worst_category} tiene peor satisfacción** con {worst_category_score:.2f} ⭐; requiere revisión de calidad del producto y servicio.")
    
    # Estado con peor review (mínimo 100 reseñas)
    if 'customer_state' in with_review.columns:
        state_counts = with_review.groupby('customer_state').size()
        valid_states = state_counts[state_counts >= 100].index
        if len(valid_states) > 0:
            state_filtered = with_review[with_review['customer_state'].isin(valid_states)]
            worst_state = state_filtered.groupby('customer_state')['review_score_avg'].mean().idxmin()
            worst_state_score = state_filtered.groupby('customer_state')['review_score_avg'].mean().min()
            insights.append(f"🗺️ **{worst_state} tiene peor satisfacción** con {worst_state_score:.2f} ⭐; indica problemas logísticos o de servicio en esa región.")
    
    # Impacto de entrega tardía
    late_col = get_col(with_review, ['is_late', 'delivery_late'])
    if late_col:
        review_on_time = with_review[with_review[late_col] == 0]['review_score_avg'].mean()
        review_late = with_review[with_review[late_col] == 1]['review_score_avg'].mean()
        if pd.notna(review_on_time) and pd.notna(review_late):
            insights.append(f"🚚 **Las entregas tardías tienen menor calificación** ({review_late:.2f}⭐) que las entregas a tiempo ({review_on_time:.2f}⭐); la puntualidad es crítica para la satisfacción.")
    
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
    st.subheader("📊 Distribución y Evolución de Satisfacción")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Redondear review_score_avg para distribución
        with_review['review_rounded'] = with_review['review_score_avg'].round()
        review_dist = with_review['review_rounded'].value_counts().sort_index().reset_index()
        review_dist.columns = ['review_score', 'count']
        
        fig_review_dist = px.bar(
            review_dist,
            x='review_score',
            y='count',
            title='Distribución de Calificaciones',
            template='plotly_white',
            color_discrete_sequence=['#1f77b4']
        )
        fig_review_dist.update_layout(
            xaxis_title='Calificación',
            yaxis_title='Órdenes',
            showlegend=False
        )
        st.plotly_chart(fig_review_dist, width='stretch')
    
    with col2:
        if 'purchase_year_month' in with_review.columns:
            # Excluir meses con menos de 100 reseñas
            month_counts = with_review.groupby('purchase_year_month').size()
            valid_months = month_counts[month_counts >= 100].index
            review_filtered = with_review[with_review['purchase_year_month'].isin(valid_months)]
            
            if not review_filtered.empty:
                review_by_month = review_filtered.groupby('purchase_year_month')['review_score_avg'].mean().reset_index()
                review_by_month = review_by_month.sort_values('purchase_year_month')
                
                fig_review_month = px.line(
                    review_by_month,
                    x='purchase_year_month',
                    y='review_score_avg',
                    title='Evolución de Review Promedio (mín. 100 reseñas)',
                    markers=True,
                    template='plotly_white',
                    color_discrete_sequence=['#1f77b4']
                )
                fig_review_month.update_layout(
                    xaxis_title='Mes',
                    yaxis_title='Review Promedio',
                    showlegend=False
                )
                st.plotly_chart(fig_review_month, width='stretch')
    
    col3, col4 = st.columns(2)
    
    with col3:
        if 'main_category' in with_review.columns:
            # Mínimo 100 reseñas por categoría, excluir Sin dato
            category_counts = with_review.groupby('main_category').size()
            valid_categories = category_counts[category_counts >= 100].index
            category_filtered = with_review[with_review['main_category'].isin(valid_categories)]
            category_filtered = category_filtered[category_filtered['main_category'] != 'Sin dato']
            
            if not category_filtered.empty:
                category_review = category_filtered.groupby('main_category')['review_score_avg'].mean().nsmallest(10).reset_index()
                
                fig_category_review = px.bar(
                    category_review,
                    x='review_score_avg',
                    y='main_category',
                    orientation='h',
                    title='Top 10 Categorías con Peor Satisfacción (mín. 100 reseñas)',
                    template='plotly_white',
                    color_discrete_sequence=['#1f77b4']
                )
                fig_category_review.update_layout(
                    xaxis_title='Review Promedio',
                    yaxis_title='Categoría',
                    showlegend=False
                )
                st.plotly_chart(fig_category_review, width='stretch')
    
    with col4:
        if 'customer_state' in with_review.columns:
            # Mínimo 100 reseñas por estado
            state_counts = with_review.groupby('customer_state').size()
            valid_states = state_counts[state_counts >= 100].index
            state_filtered = with_review[with_review['customer_state'].isin(valid_states)]
            
            if not state_filtered.empty:
                state_review = state_filtered.groupby('customer_state')['review_score_avg'].mean().nsmallest(10).reset_index()
                
                fig_state_review = px.bar(
                    state_review,
                    x='review_score_avg',
                    y='customer_state',
                    orientation='h',
                    title='Top 10 Estados con Peor Satisfacción (mín. 100 reseñas)',
                    template='plotly_white',
                    color_discrete_sequence=['#1f77b4']
                )
                fig_state_review.update_layout(
                    xaxis_title='Review Promedio',
                    yaxis_title='Estado',
                    showlegend=False
                )
                st.plotly_chart(fig_state_review, width='stretch')
    
    st.markdown("---")
    
    # Análisis exploratorio avanzado en expander
    with st.expander("🔍 Ver análisis exploratorio avanzado"):
        st.subheader("Análisis Detallado de Mala Reseña")
        
        if 'purchase_year_month' in with_review.columns:
            # Excluir meses con menos de 100 reseñas
            month_counts = with_review.groupby('purchase_year_month').size()
            valid_months = month_counts[month_counts >= 100].index
            review_filtered = with_review[with_review['purchase_year_month'].isin(valid_months)]
            
            if not review_filtered.empty:
                bad_review_by_month = review_filtered.groupby('purchase_year_month').apply(
                    lambda x: (x['review_score_avg'] <= 2).mean()
                ).reset_index(name='bad_review_rate')
                bad_review_by_month = bad_review_by_month.sort_values('purchase_year_month')
                
                fig_bad_month = px.line(
                    bad_review_by_month,
                    x='purchase_year_month',
                    y='bad_review_rate',
                    title='Tasa de Mala Reseña por Mes (mín. 100 reseñas)',
                    markers=True,
                    template='plotly_white',
                    color_discrete_sequence=['#1f77b4']
                )
                fig_bad_month.update_layout(
                    xaxis_title='Mes',
                    yaxis_title='Tasa de Mala Reseña',
                    showlegend=False
                )
                st.plotly_chart(fig_bad_month, width='stretch')
        
        # Advertencia sobre meses incompletos
        incomplete_months = ['2016-09', '2016-10', '2018-09', '2018-10']
        if any(month in month_counts.index for month in incomplete_months):
            st.warning("⚠️ Algunos meses (2016-09, 2016-10, 2018-09, 2018-10) pueden tener datos incompletos. Interpretar con precaución.")
        
        st.markdown("---")
        
        # Análisis por entrega tardía
        st.subheader("Impacto de Entrega Tardía en Reviews")
        
        col5, col6 = st.columns(2)
        
        with col5:
            late_col = get_col(with_review, ['is_late', 'delivery_late'])
            if late_col:
                review_by_late = with_review.groupby(late_col)['review_score_avg'].mean().reset_index()
                review_by_late[late_col] = review_by_late[late_col].map({1: 'Tardía', 0: 'A tiempo'})
                
                fig_review_late = px.bar(
                    review_by_late,
                    x=late_col,
                    y='review_score_avg',
                    title='Review Promedio: Entrega Tardía vs A Tiempo',
                    template='plotly_white',
                    color_discrete_sequence=['#1f77b4']
                )
                fig_review_late.update_layout(
                    xaxis_title='Tipo de Entrega',
                    yaxis_title='Review Promedio',
                    showlegend=False
                )
                st.plotly_chart(fig_review_late, width='stretch')
        
        with col6:
            if 'delay_group' in with_review.columns:
                bad_review_by_delay = with_review.groupby('delay_group').apply(
                    lambda x: (x['review_score_avg'] <= 2).mean()
                ).reset_index(name='bad_review_rate')
                
                # Ordenar por retraso
                delay_order = ['Anticipada', 'A tiempo', 'Retraso leve (1-3 días)', 'Retraso medio (4-7 días)', 'Retraso alto (8+ días)', 'Sin dato']
                bad_review_by_delay['delay_group'] = pd.Categorical(bad_review_by_delay['delay_group'], categories=delay_order, ordered=True)
                bad_review_by_delay = bad_review_by_delay.sort_values('delay_group')
                
                fig_bad_delay = px.bar(
                    bad_review_by_delay,
                    x='delay_group',
                    y='bad_review_rate',
                    title='Tasa de Mala Reseña por Grupo de Retraso',
                    template='plotly_white',
                    color_discrete_sequence=['#1f77b4']
                )
                fig_bad_delay.update_layout(
                    xaxis_title='Grupo de Retraso',
                    yaxis_title='Tasa de Mala Reseña',
                    showlegend=False
                )
                st.plotly_chart(fig_bad_delay, width='stretch')
    
    st.markdown("---")
    
    # Tabla de detalle
    st.subheader("📋 Resumen Ejecutivo por Categoría")
    
    if 'main_category' in with_review.columns:
        category_table = with_review.groupby('main_category').agg({
            'order_id': 'count'
        }).reset_index()
        category_table.columns = ['Categoría', 'Órdenes con Reseña']
        
        category_table['Review Promedio'] = with_review.groupby('main_category')['review_score_avg'].mean().values
        category_table['Tasa Mala Reseña'] = with_review.groupby('main_category').apply(
            lambda x: (x['review_score_avg'] <= 2).mean()
        ).values
        
        # Formatear columnas
        category_table['Review Promedio'] = category_table['Review Promedio'].apply(lambda x: f"{x:.2f}")
        category_table['Tasa Mala Reseña'] = category_table['Tasa Mala Reseña'].apply(format_percentage)
        
        category_table = category_table[category_table['Órdenes con Reseña'] >= 100]
        category_table = category_table.sort_values('Review Promedio', ascending=True)
        
        st.dataframe(category_table, width='stretch', hide_index=True)


if __name__ == "__main__":
    main()
