import pandas as pd

def pv_to_battery_rule(model):
    """
    An ex-post calculation of how much PV flows into the battery
    """
    p_series = [model.p[ts]() for ts in model.t]
    pv_series = [model.pv[ts] for ts in model.t]
    
    pv_to_battery_series = []
    
    for p,pv in zip(p_series,pv_series):
            
        pv_to_battery = max(0,min(p,pv))
        pv_to_battery_series.append(pv_to_battery)
    return pv_to_battery_series

def calculate_prevented_slippage(model,average_bid_ask_spread = 1):
    """
    Estimates the prevented costs arising from bid-ask spread as if we were trading intraday.
    """
    pv_to_battery_series = pv_to_battery_rule(model)
    prevented_slippage = [average_bid_ask_spread*pv_to_battery for pv_to_battery in pv_to_battery_series]

    return prevented_slippage