import streamlit as st
import optimization

def main():
    st.title('Optimization of co-located 1MW solar plant with a 1MWh battery')
    
    max_power = st.slider(label="Maximum absolute power limit [MW]",min_value=0.0,max_value=1.0,step=0.05)
    starting_soc = st.slider(label="Starting SOC [MWh]",min_value=0.0,max_value=1.0,step=0.05)
    click = st.button('Run optimization')
    if click:
        fig = optimization.run_single_optimization(starting_soc=starting_soc,p_limit=max_power)
        st.pyplot(fig)
if __name__== '__main__':
    main()