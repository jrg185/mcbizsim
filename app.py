import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class BusinessParams:
    units_base: float
    units_std: float
    price_per_unit: float
    subscription_rate: float
    addon_rate: float
    fixed_costs: float
    variable_cost_per_unit: float
    non_recurring_costs: float
    num_employees: int
    employee_salary: float

def calculate_total_revenue(units: float, params: BusinessParams) -> dict:
    base_revenue = units * params.price_per_unit
    subscription_revenue = units * params.subscription_rate
    addon_revenue = units * params.addon_rate
    total = base_revenue + subscription_revenue + addon_revenue
    
    return {
        'base': base_revenue,
        'subscription': subscription_revenue,
        'addons': addon_revenue,
        'total': total
    }

def calculate_total_costs(units: float, params: BusinessParams) -> dict:
    employee_costs = params.num_employees * params.employee_salary
    fixed_costs = params.fixed_costs + employee_costs
    variable_costs = units * params.variable_cost_per_unit
    total = fixed_costs + variable_costs + params.non_recurring_costs
    
    return {
        'fixed': fixed_costs,
        'variable': variable_costs,
        'non_recurring': params.non_recurring_costs,
        'total': total
    }

def run_simulation(params: BusinessParams, num_simulations: int = 1000) -> Tuple[pd.DataFrame, dict]:
    results = []
    
    for _ in range(num_simulations):
        # Simulate units sold with normal distribution
        units = max(0, np.random.normal(params.units_base, params.units_std))
        
        # Calculate revenues and costs
        revenue = calculate_total_revenue(units, params)
        costs = calculate_total_costs(units, params)
        
        # Calculate profit and ROI
        profit = revenue['total'] - costs['total']
        roi = (profit / costs['total']) * 100 if costs['total'] > 0 else 0
        
        results.append({
            'Units': units,
            'Revenue': revenue['total'],
            'Costs': costs['total'],
            'Profit': profit,
            'ROI': roi
        })
    
    df = pd.DataFrame(results)
    
    # Calculate breakeven units
    unit_contribution = params.price_per_unit + params.subscription_rate + params.addon_rate - params.variable_cost_per_unit
    fixed_and_nonrecurring = params.fixed_costs + params.non_recurring_costs + (params.num_employees * params.employee_salary)
    breakeven_units = fixed_and_nonrecurring / unit_contribution if unit_contribution > 0 else float('inf')
    
    metrics = {
        'breakeven_units': breakeven_units,
        'poor_case': df['Profit'].quantile(0.1),
        'average_case': df['Profit'].mean(),
        'good_case': df['Profit'].quantile(0.9)
    }
    
    return df, metrics

def format_currency(value: float) -> str:
    return f"${value:,.2f}"

def main():
    st.set_page_config(layout="wide")
    st.title('Business Monte Carlo Simulation')
    st.markdown("""
    This simulation helps estimate potential business outcomes based on your inputs.
    Adjust the parameters in the sidebar to see how they affect your business metrics.
    """)
    
    with st.sidebar:
        st.header('Input Parameters')
        
        # Base unit parameters
        st.subheader('🛍️ Sales Parameters')
        col1, col2 = st.columns(2)
        with col1:
            units_base = st.number_input('Expected Units', min_value=1, max_value=10000, value=100)
        with col2:
            units_std = st.number_input('Units Variation (±)', min_value=0.0, max_value=100.0, value=10.0,
                                      help="Standard deviation in units sold")
        
        price_per_unit = st.number_input('Base Price per Unit ($)', min_value=0.01, value=100.00, step=0.01,
                                        help="One-time purchase price per unit")
        
        # Revenue streams
        st.subheader('💰 Additional Revenue')
        subscription_rate = st.number_input('Annual Subscription ($)', min_value=0.0, value=50.0, step=0.01,
                                          help="Annual recurring revenue per unit")
        addon_rate = st.number_input('Annual Add-ons ($)', min_value=0.0, value=25.0, step=0.01,
                                    help="Expected annual add-on revenue per unit")
        
        # Costs
        st.subheader('💼 Business Costs')
        fixed_costs = st.number_input('Fixed Costs / Year ($)', min_value=0.0, value=50000.0, step=100.0,
                                     help="Annual fixed costs excluding salaries")
        variable_cost_per_unit = st.number_input('Cost per Unit ($)', min_value=0.0, value=40.0, step=0.01,
                                                help="Variable cost per unit sold")
        non_recurring_costs = st.number_input('One-time Costs ($)', min_value=0.0, value=10000.0, step=100.0,
                                            help="Non-recurring setup or initial costs")
        
        # Employee costs
        st.subheader('👥 Employee Costs')
        col3, col4 = st.columns(2)
        with col3:
            num_employees = st.number_input('Employees', min_value=0, value=2, step=1)
        with col4:
            employee_salary = st.number_input('Salary / Year ($)', min_value=0.0, value=50000.0, step=1000.0)
        
        # Simulation parameters
        st.subheader('🎲 Simulation Settings')
        num_simulations = st.slider('Number of Simulations', 100, 10000, 1000)

    # Create parameters object
    params = BusinessParams(
        units_base=units_base,
        units_std=units_std,
        price_per_unit=price_per_unit,
        subscription_rate=subscription_rate,
        addon_rate=addon_rate,
        fixed_costs=fixed_costs,
        variable_cost_per_unit=variable_cost_per_unit,
        non_recurring_costs=non_recurring_costs,
        num_employees=num_employees,
        employee_salary=employee_salary
    )
    
    # Run simulation
    df, metrics = run_simulation(params, num_simulations)
    
    # Display results in three columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader('📊 Revenue Breakdown (Per Unit)')
        base_rev = format_currency(params.price_per_unit)
        sub_rev = format_currency(params.subscription_rate)
        addon_rev = format_currency(params.addon_rate)
        total_rev = format_currency(params.price_per_unit + params.subscription_rate + params.addon_rate)
        
        st.info(f"""
        Base Price: {base_rev}
        + Annual Subscription: {sub_rev}
        + Annual Add-ons: {addon_rev}
        = Total Revenue/Unit: {total_rev}
        """)
    
    with col2:
        st.subheader('💰 Profit Scenarios')
        st.success(f"Good Case (90th): {format_currency(metrics['good_case'])}")
        st.info(f"Average Case: {format_currency(metrics['average_case'])}")
        st.error(f"Poor Case (10th): {format_currency(metrics['poor_case'])}")
    
    with col3:
        st.subheader('📈 Key Metrics')
        st.write(f"Breakeven Units: {metrics['breakeven_units']:.1f}")
        annual_fixed = params.fixed_costs + (params.num_employees * params.employee_salary)
        st.write(f"Annual Fixed Costs: {format_currency(annual_fixed)}")
        st.write(f"Cost per Unit: {format_currency(params.variable_cost_per_unit)}")
    
    # Create visualization
    st.subheader('📊 Profit Distribution')
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=df['Profit'],
        nbinsx=50,
        marker_color='#2E86C1'
    ))
    fig.update_layout(
        title='Distribution of Potential Annual Profits',
        xaxis_title='Profit ($)',
        yaxis_title='Frequency',
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Show detailed statistics in an expandable section
    with st.expander("Show Detailed Statistics"):
        st.dataframe(df.describe().round(2))

if __name__ == "__main__":
    main()