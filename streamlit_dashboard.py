import streamlit as st
import optimization

def main():
    #This allows bullet lists
    st.markdown('''
            <style>
            [data-testid="stMarkdownContainer"] ul{
                padding-left:40px;
            }
            </style>
            ''', unsafe_allow_html=True)
    
    st.title('Optimization of co-located 1MW solar plant with a 1MWh battery')
    with st.expander("See explanation"):
        st.markdown("- This is a hobby project in which I try to estimate the combined returns of a PV+battery (1MW/1MWh) combination")
        st.markdown("- You can select a battery power level, a starting state-of-charge (SOC) and the option whether the battery is allowed to charge from the grid instead of just from the PV")
        st.markdown("- The ETP (energy throughput) cost which penalizes MWh charged/discharged")
        st.markdown("- You can run an optimization (using the Gurobi solver) using the EPEX day-ahead prices in Germany for the first ~3 months of 2025")
        st.markdown("- Closing statements for now: this is no accurate representation of the value. To approximate it more accurately, one would also need to take into account the grid-fee-related benefits, the volatile intraday price development, the uncertainty of PV forecasts at the time of making trading decisions, the subsidy scheme in Germany, etc.")
    
    max_power = st.slider(value=0.5,label="Maximum absolute power limit [MW]",min_value=0.0,max_value=1.0,step=0.05)
    starting_soc = st.slider(label="Starting SOC [MWh]",min_value=0.0,max_value=1.0,step=0.05)
    etp_cost = st.number_input(label='ETP cost [EUR/MWh]',value=1.0,min_value=0.0)
    col1,col2 = st.columns(2)
    with col1:
        charge_from_grid = st.checkbox(label='Battery allowed to charge from the grid',value=True)
    with col2:
        average_bid_ask_spread = st.number_input(value=1,label='Select the average bid-ask spread')        
    date = st.date_input(label='Select delivery date',min_value='2025-01-01',max_value='2025-03-17')
    
    click = st.button('Run optimization')
    if click:
        exp = st.expander('Explanation of figures',icon='ℹ️')
        with exp:
            st.write('From top to bottom:')
            st.markdown("- The first figure shows the State-of-charge (SOC), PV production (PV), the battery power (Power), and the PV production flowing into the batter (PV to battery)")
            st.markdown("- The second figure shows the cumulative P&L for the colocation project, the cumulative P&L that would have been realized with only the PV, and the cumulative P&L that would have been realized with only the specified battery. This P&L does not yet account for the tax- grid-fee- or slippage-related benefits.")
            st.markdown("- The third figure shows the DA prices which were used in the optimization")
            st.markdown("- The fourth figure indicates the accumulated benefit that arises from not having to buy power on an illiquid market by flowing PV to the battery. This KPI is calculated based on the passed average bid-ask spread")
            
            
        fig = optimization.generate_output(starting_soc=starting_soc,p_limit=max_power,charge_from_grid=charge_from_grid,date=date.strftime('%Y-%m-%d'),etp_cost=etp_cost,average_bid_ask_spread=average_bid_ask_spread)
        st.pyplot(fig)

if __name__== '__main__':
    main()