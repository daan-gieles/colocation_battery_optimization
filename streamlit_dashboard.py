import streamlit as st
import optimization

def main():
    st.title('Optimization of co-located 1MW solar plant with a 1MWh battery')
    with st.expander("See explanation"):
        st.write("This is a hobby project in which I try to estimate the combined returns of a PV+battery (1MW/1MWh) combination")
        st.write("You can select a battery power level, a starting state-of-charge (SOC) and the option whether the battery is allowed to charge from the grid instead of just from the PV")
        st.write("The ETP (energy throughput) cost entry indicates what your cost/MWh is for charging/discharging the battery")
        st.write("You can run an optimization (using the HiGHS solver) using the EPEX day-ahead prices in Germany for the first ~3 months of 2025")
        st.write("Closing statements for now: this is no accurate representation of the value. To approximate it more accurately, one would also need to take into account the grid-fee-related benefits, the volatile intraday price development, the uncertainty of PV forecasts at the time of making trading decisions, the subsidy scheme in Germany, etc.")
    
    max_power = st.slider(label="Maximum absolute power limit [MW]",min_value=0.0,max_value=1.0,step=0.05)
    starting_soc = st.slider(label="Starting SOC [MWh]",min_value=0.0,max_value=1.0,step=0.05)
    etp_cost = st.number_input(label='ETP cost',value=10,min_value=0)
    charge_from_grid = st.checkbox(label='Battery allowed to charge from the grid (grey battery)',value=True)
    date = st.date_input(label='Select delivery date',min_value='2025-01-01',max_value='2025-03-17')
    
    click = st.button('Run optimization')
    if click:
        fig = optimization.generate_output(starting_soc=starting_soc,p_limit=max_power,charge_from_grid=charge_from_grid,date=date.strftime('%Y-%m-%d'),etp_cost=etp_cost)
        st.pyplot(fig)


if __name__== '__main__':
    main()