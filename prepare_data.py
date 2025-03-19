import pandas as pd
import matplotlib.pyplot as plt
def average_solar_production():
    df = pd.read_csv('example_data/solar/solar_generation_germany.csv')
    
    df['start_ts'] = pd.to_datetime(df['MTU'].str.split(' - ').str[0],format='%d.%m.%Y %H:%M')
    df.rename({'Solar - Actual Aggregated [MW]':'solar_production_mw'},axis='columns',inplace=True)
    df = df[df['solar_production_mw']!='-'].dropna(subset=['solar_production_mw'])

    df['solar_production_mw'] = df['solar_production_mw'].astype(int) 
    df = df[['start_ts','solar_production_mw']]
    
    df = df.groupby(by=df['start_ts'].dt.time)['solar_production_mw'].mean().reset_index(drop=False)

    df['solar_production_mw'] = df['solar_production_mw']/df['solar_production_mw'].max() 
    # print(df)
    # fig,ax = plt.subplots()

    # ax.plot(df['solar_production_mw'])
    df['start_ts'] = '2025-03-18T' + df['start_ts'].astype(str)
    df['start_ts'] = pd.to_datetime(df['start_ts'])
    return df

def prepare_da_prices():
    df = pd.read_csv('example_data/prices/da_prices.csv')
    df = df[df['Sequence']=='Sequence 1']
    df['start_ts'] = pd.to_datetime(df['MTU (CET/CEST)'].str.split(' - ').str[0],format='%d/%m/%Y %H:%M:%S')
    df.rename({'Day-ahead Price (EUR/MWh)':'da_price'},axis='columns',inplace=True)
    df = df[['start_ts','da_price']]
    return df

def merge_prices_and_solar():
    df_prices = prepare_da_prices()
    df_solar = average_solar_production()
    print(df_prices)
    df_merged = pd.merge(df_prices,df_solar,on='start_ts',how='inner')
    
    return df_merged
if __name__ == "__main__":
    merge_prices_and_solar()