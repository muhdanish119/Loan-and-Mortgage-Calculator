import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
from dateutil.relativedelta import relativedelta

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Ultimate Mortgage Analyzer Pro", 
    page_icon="🏦", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .st-emotion-cache-1y4p8pa {
        padding: 2rem 1rem;
    }
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-left: 4px solid #4e79a7;
    }
    .feature-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .stButton>button {
        background-color: #4e79a7;
        color: white;
        border-radius: 8px;
        padding: 8px 16px;
    }
    h1 {
        color: #2c3e50;
    }
    h2 {
        color: #34495e;
        border-bottom: 2px solid #4e79a7;
        padding-bottom: 8px;
    }
    .result-box {
        background-color: #e8f4fc;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'mortgage_calculated' not in st.session_state:
    st.session_state.mortgage_calculated = False
if 'affordability_calculated' not in st.session_state:
    st.session_state.affordability_calculated = False
if 'scenario_comparison' not in st.session_state:
    st.session_state.scenario_comparison = False
if 'dti_calculated' not in st.session_state:
    st.session_state.dti_calculated = False

# --- CALCULATION FUNCTIONS ---
def calculate_amortization(principal, rate, years, start_date, extra_payment=0, payment_freq=12):
    monthly_rate = rate / 100 / payment_freq
    periods = years * payment_freq
    payment = (principal * monthly_rate) / (1 - (1 + monthly_rate) ** -periods)
    
    schedule = []
    balance = principal
    total_interest = 0
    current_date = start_date
    
    for i in range(1, periods + 1):
        interest = balance * monthly_rate
        principal_payment = payment - interest + extra_payment
        balance -= principal_payment
        total_interest += interest
        
        schedule.append({
            "Date": current_date.strftime("%Y-%m-%d"),
            "Period": i,
            "Payment ($)": round(payment + extra_payment, 2),
            "Principal ($)": round(principal_payment, 2),
            "Interest ($)": round(interest, 2),
            "Remaining Balance ($)": round(max(balance, 0), 2),
            "Cumulative Interest ($)": round(total_interest, 2)
        })
        
        current_date += relativedelta(months=1)
        if balance <= 0:
            break
            
    return pd.DataFrame(schedule), total_interest

def calculate_dti(monthly_income, debts, new_payment):
    return ((debts + new_payment) / monthly_income) * 100

def calculate_affordability(income, debts, rate, years, dti_limit=36):
    max_payment = (income * (dti_limit/100)) - debts
    monthly_rate = rate / 100 / 12
    periods = years * 12
    max_loan = max_payment * ((1 - (1 + monthly_rate) ** -periods) / monthly_rate)
    return max_loan

# --- MAIN PAGE LAYOUT ---
st.title("🏦 Ultimate Mortgage Analyzer Pro")
st.markdown("""
<div class="result-box">
    <h3 style="color:#2c3e50; margin-top:0;">Get a complete understanding of your mortgage options</h3>
    <p style="color:#7f8c8d;">Visualize payments, analyze affordability, and compare scenarios with our comprehensive tool</p>
</div>
""", unsafe_allow_html=True)

# --- INPUT SECTION ---
with st.container():
    st.header("📝 Loan Parameters")
    col1, col2, col3 = st.columns(3)
    with col1:
        principal = st.number_input("Loan Amount ($)", min_value=1000, value=300000, step=1000)
        rate = st.number_input("Annual Interest Rate (%)", min_value=0.01, value=5.5, step=0.01, format="%.2f")
    with col2:
        years = st.slider("Loan Term (Years)", 1, 40, 30, help="Standard terms are 15, 20, or 30 years")
        start_date = st.date_input("Start Date", value=date.today())
    with col3:
        payment_freq = st.selectbox("Payment Frequency", ["Monthly (12/yr)", "Bi-Weekly (26/yr)", "Weekly (52/yr)"], index=0)
        freq_map = {"Monthly (12/yr)": 12, "Bi-Weekly (26/yr)": 26, "Weekly (52/yr)": 52}
        extra_payment = st.number_input("Extra Payment ($/period)", min_value=0, value=0, step=50)

# --- MAIN CALCULATION BUTTON ---
if st.button("💰 Calculate Mortgage", type="primary", use_container_width=True):
    st.session_state.mortgage_calculated = True
    st.session_state.amortization_df, st.session_state.total_interest = calculate_amortization(
        principal, rate, years, start_date, extra_payment, freq_map[payment_freq]
    )

# --- RESULTS DISPLAY ---
if st.session_state.mortgage_calculated:
    with st.container():
        st.header("📊 Loan Overview")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            with st.container(border=True):
                st.metric("Monthly Payment", f"${st.session_state.amortization_df.iloc[0]['Payment ($)']:,.2f}")
        with col2:
            with st.container(border=True):
                st.metric("Total Interest", f"${st.session_state.total_interest:,.2f}")
        with col3:
            with st.container(border=True):
                st.metric("Total Cost", f"${principal + st.session_state.total_interest:,.2f}")
        with col4:
            with st.container(border=True):
                payoff_months = len(st.session_state.amortization_df)
                st.metric("Payoff Period", f"{payoff_months//12} yrs {payoff_months%12} mos")
        
        # --- AMORTIZATION SCHEDULE ---
        with st.expander("📜 View Full Amortization Schedule", expanded=True):
            st.dataframe(st.session_state.amortization_df.style.format({
                "Payment ($)": "${:,.2f}",
                "Principal ($)": "${:,.2f}",
                "Interest ($)": "${:,.2f}",
                "Remaining Balance ($)": "${:,.2f}",
                "Cumulative Interest ($)": "${:,.2f}"
            }), height=400, use_container_width=True)
        
        # --- VISUALIZATIONS ---
        st.header("📈 Payment Analysis")
        tab1, tab2 = st.tabs(["Payment Breakdown", "Equity Growth"])
        
        with tab1:
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(
                x=st.session_state.amortization_df["Period"], 
                y=st.session_state.amortization_df["Principal ($)"],
                name="Principal",
                stackgroup="one",
                line=dict(color="#2ecc71")
            ))
            fig1.add_trace(go.Scatter(
                x=st.session_state.amortization_df["Period"], 
                y=st.session_state.amortization_df["Interest ($)"],
                name="Interest",
                stackgroup="one",
                line=dict(color="#e74c3c")
            ))
            fig1.update_layout(
                title="Payment Composition Over Time",
                xaxis_title="Payment Period",
                yaxis_title="Amount ($)",
                hovermode="x unified",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with tab2:
            fig2 = px.area(
                st.session_state.amortization_df,
                x="Period",
                y=principal - st.session_state.amortization_df["Remaining Balance ($)"],
                title="Equity Growth Over Time",
                labels={"y": "Equity ($)"},
                color_discrete_sequence=["#3498db"]
            )
            fig2.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        # --- ADVANCED FEATURES SECTION ---
        st.header("🔍 Advanced Analysis")
        
        # Debt-to-Income Analysis
        with st.container(border=True):
            st.subheader("💳 Debt-to-Income (DTI) Analysis")
            col1, col2 = st.columns(2)
            with col1:
                monthly_income = st.number_input("Your Gross Monthly Income ($)", min_value=500, value=6000, step=100)
                existing_debts = st.number_input("Existing Monthly Debt Payments ($)", min_value=0, value=500, step=50)
            
            if st.button("Calculate DTI Ratio", key="dti_button", type="secondary"):
                st.session_state.dti_calculated = True
                st.session_state.dti = calculate_dti(
                    monthly_income, 
                    existing_debts, 
                    st.session_state.amortization_df.iloc[0]['Payment ($)']
                )
            
            if st.session_state.dti_calculated:
                with col2:
                    fig3 = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=st.session_state.dti,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': "Your DTI Ratio"},
                        gauge={
                            'axis': {'range': [0, 50]},
                            'steps': [
                                {'range': [0, 36], 'color': "#2ecc71"},
                                {'range': [36, 43], 'color': "#f39c12"},
                                {'range': [43, 50], 'color': "#e74c3c"}
                            ],
                            'bar': {'color': "#2c3e50"}
                        }
                    ))
                    st.plotly_chart(fig3, use_container_width=True)
                
                if st.session_state.dti > 43:
                    st.error("Most lenders will reject applications over 43% DTI")
                elif st.session_state.dti > 36:
                    st.warning("Approval may be difficult (36-43% DTI)")
                else:
                    st.success("Good DTI (under 36%)")
        
        # Home Affordability Calculator
        with st.container(border=True):
            st.subheader("🏠 Home Affordability Calculator")
            col1, col2 = st.columns(2)
            with col1:
                affordability_income = st.number_input("Your Annual Income ($)", min_value=10000, value=80000, step=1000)
                affordability_debts = st.number_input("Your Current Monthly Debts ($)", min_value=0, value=500, step=50)
            with col2:
                affordability_rate = st.number_input("Current Market Rate (%)", min_value=0.01, value=5.5, step=0.01)
                dti_limit = st.slider("Lender's DTI Limit (%)", 20, 50, 36)
            
            if st.button("Calculate My Buying Power", key="affordability_button", type="secondary"):
                st.session_state.affordability_calculated = True
                st.session_state.max_loan = calculate_affordability(
                    affordability_income/12, 
                    affordability_debts, 
                    affordability_rate, 
                    30,  # Standard 30-year term
                    dti_limit/100
                )
            
            if st.session_state.affordability_calculated:
                st.markdown(f"""
                <div class="result-box">
                    <h3 style="margin-top:0; color:#2c3e50;">Based on your income and a {dti_limit}% DTI limit:</h3>
                    <h1 style="color:#27ae60; margin-bottom:0;">${st.session_state.max_loan:,.0f}</h1>
                    <p style="color:#7f8c8d;">Maximum home price you can afford</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Scenario Comparison
        with st.container(border=True):
            st.subheader("🔄 Scenario Comparison")
            col1, col2 = st.columns(2)
            with col1:
                compare_rate = st.number_input("Alternative Interest Rate (%)", min_value=0.01, value=4.5, step=0.01)
                compare_years = st.slider("Alternative Loan Term (Years)", 1, 40, 25)
            with col2:
                compare_extra = st.number_input("Alternative Extra Payment ($)", min_value=0, value=100, step=50)
            
            if st.button("Compare Scenarios", key="compare_button", type="secondary"):
                st.session_state.scenario_comparison = True
                st.session_state.compare_df, st.session_state.compare_interest = calculate_amortization(
                    principal, compare_rate, compare_years, start_date, compare_extra, freq_map[payment_freq]
                )
                st.session_state.savings = st.session_state.total_interest - st.session_state.compare_interest
                st.session_state.monthly_diff = (
                    st.session_state.amortization_df.iloc[0]['Payment ($)'] - 
                    st.session_state.compare_df.iloc[0]['Payment ($)']
                )
            
            if st.session_state.scenario_comparison:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Interest Savings", f"${st.session_state.savings:,.2f}")
                with col2:
                    st.metric("Monthly Payment Difference", 
                             f"${abs(st.session_state.monthly_diff):,.2f} {'less' if st.session_state.monthly_diff > 0 else 'more'}",
                             delta=f"{abs(st.session_state.monthly_diff):.2f}")
                
                fig4 = go.Figure()
                fig4.add_trace(go.Scatter(
                    x=st.session_state.amortization_df["Period"],
                    y=st.session_state.amortization_df["Remaining Balance ($)"],
                    name="Current Scenario",
                    line=dict(color="#3498db")
                ))
                fig4.add_trace(go.Scatter(
                    x=st.session_state.compare_df["Period"],
                    y=st.session_state.compare_df["Remaining Balance ($)"],
                    name="Alternative Scenario",
                    line=dict(color="#e74c3c")
                ))
                fig4.update_layout(
                    title="Loan Balance Comparison",
                    xaxis_title="Payment Period",
                    yaxis_title="Remaining Balance ($)",
                    hovermode="x unified",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig4, use_container_width=True)

    # --- NEW FEATURES ADDED ---
    with st.container(border=True):
        st.subheader("📌 Additional Tools")
        
        # Early Payoff Calculator
        with st.expander("⏱ Early Payoff Calculator"):
            st.write("Calculate how much you can save by increasing your payments")
            extra_payment = st.number_input("Additional Monthly Payment ($)", min_value=0, value=200, step=50)
            if st.button("Calculate Early Payoff"):
                payoff_df, _ = calculate_amortization(
                    principal, rate, years, start_date, extra_payment, freq_map[payment_freq]
                )
                original_months = len(st.session_state.amortization_df)
                new_months = len(payoff_df)
                months_saved = original_months - new_months
                interest_saved = st.session_state.total_interest - payoff_df["Cumulative Interest ($)"].iloc[-1]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Months Saved", months_saved)
                with col2:
                    st.metric("Interest Saved", f"${interest_saved:,.2f}")
        
        # Refinance Break-Even Calculator
        with st.expander("💱 Refinance Break-Even Analysis"):
            st.write("Determine when refinancing makes financial sense")
            col1, col2 = st.columns(2)
            with col1:
                refi_rate = st.number_input("Refinance Rate (%)", min_value=0.01, value=4.0, step=0.01)
                refi_cost = st.number_input("Refinance Costs ($)", min_value=0, value=3000, step=100)
            with col2:
                refi_term = st.slider("Refinance Term (Years)", 1, 40, 30)
            
            if st.button("Calculate Break-Even"):
                refi_df, refi_interest = calculate_amortization(
                    st.session_state.amortization_df["Remaining Balance ($)"].iloc[0], 
                    refi_rate, refi_term, date.today(), 0, freq_map[payment_freq]
                )
                
                original_payment = st.session_state.amortization_df.iloc[0]['Payment ($)']
                refi_payment = refi_df.iloc[0]['Payment ($)']
                monthly_saving = original_payment - refi_payment
                
                if monthly_saving > 0:
                    break_even_months = refi_cost / monthly_saving
                    st.success(f"Break-even point: {break_even_months:.1f} months")
                    st.write(f"After {break_even_months:.1f} months, your savings will exceed the refinance costs")
                else:
                    st.error("This refinance option doesn't reduce your monthly payment")

# --- FOOTER ---
st.divider()
st.markdown("""
<div style="text-align: center; color: #7f8c8d; margin-top: 30px;">
    <p>This comprehensive mortgage analyzer includes:</p>
    <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
        <div style="background: white; padding: 12px 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            📊 Interactive Visualizations
        </div>
        <div style="background: white; padding: 12px 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            💳 DTI Analysis
        </div>
        <div style="background: white; padding: 12px 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            🏠 Affordability Calculator
        </div>
        <div style="background: white; padding: 12px 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            🔄 Scenario Comparison
        </div>
        <div style="background: white; padding: 12px 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            ⏱ Early Payoff Calculator
        </div>
        <div style="background: white; padding: 12px 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            💱 Refinance Analysis
        </div>
    </div>
</div>
""", unsafe_allow_html=True)