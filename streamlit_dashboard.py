import streamlit as st
import optimization
import time

def main():
    """
    Main streamlit logic
    """
    #This allows bullet lists
    st.markdown('''
            <style>
            [data-testid="stMarkdownContainer"] ul{
                padding-left:40px;
            }
            </style>
            ''', unsafe_allow_html=True)
    
    st.title('Trading optimization of solar plant with a battery')
    with st.expander("See explanation"):
        st.markdown("- This is a hobby project in which I try to estimate the combined returns of a PV+battery (1MW/1MWh) combination")
        st.markdown("- You can select a battery power level, a starting state-of-charge (SOC) and the option whether the battery is allowed to charge from the grid instead or solely from the PV")
        st.markdown("- The ETP (energy throughput) cost penalizes MWh's charged/discharged by the battery")
        st.markdown("- You can run an optimization (using the Gurobi solver) using the EPEX day-ahead prices in Germany for the first ~3 months of 2025")
        st.markdown("- Closing statements for now: this is no accurate representation of the value. To approximate it more accurately, one would also need to take into account the grid-fee-related benefits, the volatile intraday price development, the uncertainty of PV forecasts at the time of making trading decisions, the subsidy scheme in Germany, etc. Furthermore, the optimization optimizes on QH basis while DA prices (as of March 2025) still correspond to hourly contracts.")
    
    col_battery_power,col_battery_capacity = st.columns(2)
    with col_battery_power:
        max_power = st.slider(value=0.5,label="Absolute power limit battery [MW]",min_value=0.0,max_value=5.0,step=0.05)
    with col_battery_capacity:
        capacity_battery = st.slider(value=1.0,label="Battery capacity [MWh]",min_value=0.1,max_value=10.0,step=0.1)
    max_power_pv = st.slider(value=1.0,label="Maximum production capacity PV [MW]",min_value=0.1,max_value=10.0,step=0.1)

    starting_soc = st.slider(label="Starting state-of-charge (SOC) [%]",min_value=0.0,max_value=100.0,step=0.5)
    etp_cost = st.number_input(label='ETP cost [EUR/MWh]',value=1.0,min_value=0.0)
    col1,col2 = st.columns(2)
    with col1:
        charge_from_grid = st.checkbox(label='Battery allowed to charge from the grid',value=True)
    with col2:
        average_bid_ask_spread = st.number_input(value=1,label='Select the average bid-ask spread')        
    date = st.date_input(label='Select delivery date',min_value='2025-01-01',max_value='2025-03-17')
    
    click = st.button('Run optimization')
    if click:
        with st.expander('Explanation of figures',icon='ℹ️'):
            st.write('From top to bottom:')
            st.markdown("- The first figure shows the State-of-charge (SOC), PV production (PV), the battery power (Power), and the PV production flowing into the batter (PV to battery)")
            st.markdown("- The second figure shows the cumulative P&L for the colocation project, the cumulative P&L that would have been realized with only the PV, and the cumulative P&L that would have been realized with only the specified battery. This P&L does not yet account for the tax- grid-fee- or slippage-related benefits.")
            st.markdown("- The third figure shows the DA prices which were used in the optimization")
            st.markdown("- The fourth figure indicates the accumulated benefit that arises from not having to buy power on an illiquid market by flowing PV to the battery. This KPI is calculated based on the passed average bid-ask spread. The benit originates from PV and the battery 'meeting in the middle' instead of PV selling at a lower price than what the battery would buy at.")
        
        with st.spinner(text='Running optimization...'):   
            fig = optimization.generate_output(battery_capacity=capacity_battery,max_power_pv=max_power_pv,starting_soc=starting_soc,p_limit=max_power,charge_from_grid=charge_from_grid,date=date.strftime('%Y-%m-%d'),etp_cost=etp_cost,average_bid_ask_spread=average_bid_ask_spread)
            st.pyplot(fig)

if __name__== '__main__':
    main()