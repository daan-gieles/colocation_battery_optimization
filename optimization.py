import prepare_data
import pyomo.environ as pyo
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ETP_COST = 25

def run_single_optimization(starting_soc = 0.1, p_limit = 0.1,date='2025-01-15',charge_from_grid=True):

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
    
    model = pyo.ConcreteModel()
    df = prepare_data.merge_prices_and_solar(date=date)

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
    
    # opt = pyo.SolverFactory('cbc')
    opt = pyo.SolverFactory('ipopt',executable='ipoptlinux',solver_io='nl')
    # opt.options['output_file'] = "ipopt_log.txt"
    result = opt.solve(model)    
    
    ts_series =list(model.t.ordered_data())
    soc_series = [model.soc[ts]() for ts in ts_series]
    pv_series = [model.pv[ts] for ts in ts_series]
    p_series = [model.p[ts]() for ts in ts_series]
    accumulated_pnl_series_colocation = np.cumsum([model.CF_colocation[ts]() for ts in ts_series])
    accumulated_pnl_series_pv = np.cumsum([model.CF_pv[ts]() for ts in ts_series])
    da_prices_series = [model.da[ts] for ts in ts_series]

    fig,(ax1,ax2,ax3) = plt.subplots(3,1,sharex=True)
    
    # ax1,ax2 = axes

    ax1.plot(ts_series,soc_series,label='SOC')
    ax1.plot(ts_series,pv_series,label='PV')
    ax1.plot(ts_series,p_series,label='Power')
    ax2.plot(ts_series,accumulated_pnl_series_colocation,label='P&L Colocation')
    ax2.plot(ts_series,accumulated_pnl_series_pv,label='P&L PV Only')
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

def objective_expression(model):
    
    return sum(-model.da[t]*(model.p[t]-model.pv[t]) for t in model.t)-sum(model.p[t]**2 for t in model.t)*ETP_COST/4

# 
if __name__ == "__main__":
    run_single_optimization()