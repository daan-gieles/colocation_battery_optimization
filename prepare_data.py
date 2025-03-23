import pandas as pd
import matplotlib.pyplot as plt

def estimate_solar_production(date='2025-01-05'):
    
    df = pd.read_csv('example_data/solar/solar_generation_germany.csv')
    
    df['start_ts'] = pd.to_datetime(df['MTU'].str.split(' - ').str[0],format='%d.%m.%Y %H:%M')
    df.rename({'Solar - Actual Aggregated [MW]':'solar_production_mw'},axis='columns',inplace=True)
    df = df[df['solar_production_mw']!='-'].dropna(subset=['solar_production_mw'])

    df['solar_production_mw'] = df['solar_production_mw'].astype(int) 
    df = df[['start_ts','solar_production_mw']]
    
    df['solar_production_mw'] = df['solar_production_mw']/df['solar_production_mw'].max() 
    df = df[df['start_ts'].dt.strftime('%Y-%m-%d')==date]

    return df

def prepare_da_prices(date='2025-01-09'):
    df = pd.read_csv('example_data/prices/da_prices_2025.csv')
    df = df[df['Sequence']=='Sequence 1']
    
    df['start_ts'] = pd.to_datetime(df['MTU (CET/CEST)'].str.split(' - ').str[0],format='%d/%m/%Y %H:%M:%S')

    df = df[df['start_ts'].dt.strftime('%Y-%m-%d')==date]
    
    df.rename({'Day-ahead Price (EUR/MWh)':'da_price'},axis='columns',inplace=True)
    df = df[['start_ts','da_price']]
    return df

def merge_prices_and_solar(date='2025-01-15'):
    df_prices = prepare_da_prices(date=date)
    df_solar = estimate_solar_production(date=date)
    df_merged = pd.merge(df_prices,df_solar,on='start_ts',how='inner')
    return df_merged
if __name__ == "__main__":
    merge_prices_and_solar()