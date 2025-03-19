import prepare_data
import pyomo.environ as pyo
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def run_single_optimization(starting_soc = 0.1, p_limit = 0.1):

    def p_pv_to_battery_calculation(model,t):
        return model.pv[t] - model.p[t]


    def soc_calculation(model,t):
        preceding_t = [ts for ts in model.t if ts<=t]
        return starting_soc+ np.sum([model.p[t] for t in preceding_t])/4

    def constraint_p_max(model,t):
        return model.p[t]<=p_limit

    def constraint_p_min(model,t):
        return model.p[t]>=-p_limit

    def constraint_soc_lower(model,t):
        return model.soc[t]>=0

    def constraint_soc_upper(model,t):
        return model.soc[t]<=1

    model = pyo.ConcreteModel()
    df = prepare_data.merge_prices_and_solar()
    df = df.set_index('start_ts',drop=True)
    # df = df.head(1)
    # print(df.dtypes)
    #Define time index
    # model.t = pyo.Set(initialize = df.index)
    model.t = pyo.Set(initialize = df.index)
    
    # Parameters (given data)
    model.pv = pyo.Param(model.t,initialize = df.solar_production_mw,mutable=False)
    model.da = pyo.Param(model.t,initialize = df.da_price,mutable=False)
    
    #Variables
    # p>0 -> charging. p<0 -> discharging
    model.p = pyo.Var(model.t,within=pyo.Reals,initialize=0)

    # Expressions
    model.p_pv_to_battery = pyo.Expression(model.t,rule=p_pv_to_battery_calculation)    
    model.soc = pyo.Expression(model.t,rule=soc_calculation)    
    
    #Constraints
    model.constraint_p_max = pyo.Constraint(model.t,expr=constraint_p_max)
    model.constraint_p_min = pyo.Constraint(model.t,expr=constraint_p_min)
    model.constraint_soc_lower = pyo.Constraint(model.t,expr=constraint_soc_lower)
    model.constraint_soc_upper = pyo.Constraint(model.t,expr=constraint_soc_upper)
    # model.constraint_etp = pyo.Constraint(expr=constraint_etp)
    #Objective
    model.OBJ = pyo.Objective(rule=objective_expression,sense=pyo.maximize)
    
    #Run optimization
    
    # opt = pyo.SolverFactory('cbc')
    opt = pyo.SolverFactory('glpk')

    result = opt.solve(model)    
    
    ts_series =list(model.t.ordered_data())
    soc_series = [model.soc[ts]() for ts in ts_series]
    pv_series = [model.pv[ts] for ts in ts_series]
    p_series = [model.p[ts]() for ts in ts_series]
    fig,ax = plt.subplots()


    ax.plot(ts_series,soc_series,label='SOC')
    ax.plot(ts_series,pv_series,label='PV')
    ax.plot(ts_series,p_series,label='Power')
    ax.set_title(f'Single-shot optimization on 18-03. Max power {str(round(p_limit,2))}, starting SOC {str(round(starting_soc,1))}')
    ax.legend()

    ax.xaxis.set_major_locator(mdates.HourLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:00'))
    ax.xaxis.set_minor_locator(mdates.MinuteLocator(byminute=[15,30,45]))
    # plt.show()
    ax.tick_params(rotation=45,labelsize=7,axis='x')
    plt.tight_layout()
    
    return fig

def objective_expression(model):
    
    return sum(-model.da[t]*model.p[t] for t in model.t)
if __name__ == "__main__":
    run_single_optimization()