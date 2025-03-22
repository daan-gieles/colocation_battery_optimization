import prepare_data
import pyomo.environ as pyo
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.dates as mdates



def generate_output(starting_soc = 0.1, p_limit = 0.1,date='2025-01-15',charge_from_grid=True,etp_cost = 5):
    model_colocation,result_colocation = run_single_optimization_colocation(starting_soc = starting_soc, p_limit = p_limit,date=date,charge_from_grid=charge_from_grid,etp_cost=etp_cost)
    model_battery,result_battery = run_single_optimization_colocation(starting_soc = starting_soc, p_limit = p_limit,date=date,charge_from_grid=charge_from_grid,no_pv=True,etp_cost=etp_cost)
    
    #Generate plots
    ts_series =list(model_colocation.t.ordered_data())
    soc_series = [model_colocation.soc[ts]() for ts in ts_series]
    pv_series = [model_colocation.pv[ts] for ts in ts_series]
    p_series = [model_colocation.p[ts]() for ts in ts_series]
    accumulated_pnl_series_colocation = np.cumsum([model_colocation.CF_colocation[ts]() for ts in ts_series])
    accumulated_pnl_series_pv = np.cumsum([model_colocation.CF_pv[ts]() for ts in ts_series])
    accumulated_pnl_series_battery_only =  np.cumsum([model_battery.CF_colocation[ts]() for ts in ts_series])
    
    da_prices_series = [model_colocation.da[ts] for ts in ts_series]

    fig,(ax1,ax2,ax3) = plt.subplots(3,1,sharex=True)
    
    # ax1,ax2 = axes

    ax1.plot(ts_series,soc_series,label='SOC')
    ax1.plot(ts_series,pv_series,label='PV')
    ax1.plot(ts_series,p_series,label='Power')
    ax2.plot(ts_series,accumulated_pnl_series_colocation,label=f'P&L Colocation: {round(accumulated_pnl_series_colocation[-1],2)}EU')
    ax2.plot(ts_series,accumulated_pnl_series_pv,label=f'P&L PV Only: {round(accumulated_pnl_series_pv[-1],2)}EU')
    ax2.plot(ts_series,accumulated_pnl_series_battery_only,label=f'P&L Battery Only: {round(accumulated_pnl_series_battery_only[-1],2)}EU')
    ax3.plot(ts_series,da_prices_series,label='DA prices')
    
    ax1.set_ylabel('SOC/PV/Battery Power')
    ax2.set_ylabel('DA prices')
    ax3.set_ylabel('P&L')

    ax1.set_title(f'Single-shot optimization on {date}. Max power {str(round(p_limit,2))}, starting SOC {str(round(starting_soc,1))}')

    ax3.xaxis.set_major_locator(mdates.HourLocator())
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%H:00'))
    ax3.xaxis.set_minor_locator(mdates.MinuteLocator(byminute=[15,30,45]))
    # plt.show()
    ax3.tick_params(rotation=45,labelsize=7,axis='x')
    ax1.legend()
    ax2.legend()
    ax3.legend()

    plt.tight_layout()
    return fig
def run_single_optimization_colocation(starting_soc = 0.1, p_limit = 0.1,date='2025-01-15',charge_from_grid=True,no_pv=False,etp_cost=5):

    def soc_calculation(model,t):
        preceding_t = [ts for ts in model.t if ts<=t]
        return starting_soc+np.sum([model.p[t] for t in preceding_t])/4

    def constraint_p_max(model,t):
        if charge_from_grid:
            return model.p[t]<=p_limit
        else:
            return model.p[t]<=model.pv[t]

    def constraint_p_min(model,t):
        return model.p[t]>=-p_limit

    def constraint_soc_lower(model,t):
        return model.soc[t]>=0

    def constraint_soc_upper(model,t):
        return model.soc[t]<=1

    def cashflow_rule_colocation(model,t):
        return -model.da[t]*(model.p[t]-model.pv[t])/4
    
    def cashflow_rule_only_pv(model,t):
        return model.da[t]*model.pv[t]/4
    
    def objective_expression(model):
    
        # return sum(-model.da[t]*(model.p[t]-model.pv[t]) for t in model.t)-sum(model.p[t]**2 for t in model.t)*ETP_COST/4
        return sum(-model.da[t]*(model.p[t]-model.pv[t]) for t in model.t)
    model = pyo.ConcreteModel()
    df = prepare_data.merge_prices_and_solar(date=date)
    
    if no_pv:
        df['solar_production_mw']=0

    df = df.set_index('start_ts',drop=True)
    
    model.t = pyo.Set(initialize = df.index)
    
    # Parameters (given data)
    model.pv = pyo.Param(model.t,initialize = df.solar_production_mw,mutable=False)
    model.da = pyo.Param(model.t,initialize = df.da_price,mutable=False)
    
    #Variables
    # p>0 -> charging. p<0 -> discharging
    model.p = pyo.Var(model.t,within=pyo.Reals,initialize=0)

    # Expressions    
    model.soc = pyo.Expression(model.t,rule=soc_calculation)    
    
    #Constraints
    model.constraint_p_max = pyo.Constraint(model.t,expr=constraint_p_max)
    model.constraint_p_min = pyo.Constraint(model.t,expr=constraint_p_min)
    model.constraint_soc_lower = pyo.Constraint(model.t,expr=constraint_soc_lower)
    model.constraint_soc_upper = pyo.Constraint(model.t,expr=constraint_soc_upper)
    # model.constraint_etp = pyo.Constraint(expr=constraint_etp)
    #Objective
    model.OBJ = pyo.Objective(rule=objective_expression,sense=pyo.maximize)
    
    model.CF_colocation = pyo.Expression(model.t,expr=cashflow_rule_colocation)
    model.CF_pv = pyo.Expression(model.t,expr=cashflow_rule_only_pv)

    #Run optimization
    
    opt = pyo.SolverFactory('appsi_highs')

    result = opt.solve(model)
    
    
    return model,result



# 
if __name__ == "__main__":
    generate_output()