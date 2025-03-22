import streamlit as st
import optimization
import os

def main():
    st.title('Optimization of co-located 1MW solar plant with a 1MWh battery')
    
    max_power = st.slider(label="Maximum absolute power limit [MW]",min_value=0.0,max_value=1.0,step=0.05)
    starting_soc = st.slider(label="Starting SOC [MWh]",min_value=0.0,max_value=1.0,step=0.05)
    
    charge_from_grid = st.checkbox(label='Battery allowed to charge from the grid (grey battery)',value=True)
    date = st.date_input(label='Select delivery date',min_value='2025-01-01',max_value='2025-03-17')
    
    click = st.button('Run optimization')
    if click:
        fig = optimization.run_single_optimization(starting_soc=starting_soc,p_limit=max_power,charge_from_grid=charge_from_grid,date=date.strftime('%Y-%m-%d'))
        st.pyplot(fig)
    
    dir = st.text_input(label='mess around in directories on ST Cloud')
    click_dir = st.button('Print contents of directory')
    if click_dir:
        st.text(str(os.listdir(dir)))
if __name__== '__main__':
    main()