import prepare_data
import pyomo.environ as pyo
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import calculate_kpis

plt.style.use('ggplot')


def generate_output(battery_capacity=4, max_power_pv=8, starting_soc=0.1, p_limit=0.1, date='2025-01-15', charge_from_grid=True, etp_cost=5, average_bid_ask_spread=1):
    """
    Does the optimization calls, plots results. Not as efficient as it could be...
    """

    model_colocation, _ = run_single_optimization_colocation(battery_capacity=battery_capacity, max_power_pv=max_power_pv,
                                                             starting_soc=starting_soc, p_limit=p_limit, date=date, charge_from_grid=charge_from_grid, etp_cost=etp_cost, average_bid_ask_spread=average_bid_ask_spread)
    model_battery, _ = run_single_optimization_colocation(battery_capacity=battery_capacity, max_power_pv=max_power_pv, starting_soc=starting_soc, p_limit=p_limit, date=date,
                                                          charge_from_grid=charge_from_grid, no_pv=True, etp_cost=etp_cost, average_bid_ask_spread=average_bid_ask_spread)

    # Extract data from the optimization model
    ts_series = list(model_colocation.t.ordered_data())
    soc_series = [model_colocation.soc[ts]() for ts in ts_series]
    pv_series = [model_colocation.pv[ts] for ts in ts_series]
    p_series = [model_colocation.p[ts]() for ts in ts_series]

    accumulated_pnl_series_colocation = np.cumsum(
        [model_colocation.CF_colocation[ts]() for ts in ts_series])
    accumulated_pnl_series_pv = np.cumsum(
        [model_colocation.CF_pv[ts]() for ts in ts_series])
    accumulated_pnl_series_battery_only = np.cumsum(
        [model_battery.CF_colocation[ts]() for ts in ts_series])

    da_prices_series = [model_colocation.da[ts] for ts in ts_series]

    # Calculate some KPIs
    pv_to_battery_series = calculate_kpis.pv_to_battery_rule(model_colocation)
    prevented_slippage = calculate_kpis.calculate_prevented_slippage(
        model_colocation, average_bid_ask_spread=average_bid_ask_spread)

    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, sharex=True)

    ax1.set_title(
        f'{date}. Battery: {str(round(p_limit, 1))}/{str(round(battery_capacity,2))} MW/MWh, Max PV Capacity: {str(round(max_power_pv,2))}MW. \n Starting SOC {str(round(starting_soc, 1))}%', fontsize=7)

    ax1.plot(ts_series, soc_series, label='SOC [MWh]')
    ax1.plot(ts_series, pv_series, label='PV [MW]')
    ax1.plot(ts_series, p_series, label='Power [MW]')
    ax1.plot(ts_series, pv_to_battery_series,
             label='PV to battery [MW]', linestyle='--')

    ax2.plot(ts_series, accumulated_pnl_series_colocation,
             label=f'Colocation: {round(accumulated_pnl_series_colocation[-1], 2)}EU')
    ax2.plot(ts_series, accumulated_pnl_series_pv,
             label=f'PV Only: {round(accumulated_pnl_series_pv[-1], 2)}EU')
    ax2.plot(ts_series, accumulated_pnl_series_battery_only,
             label=f'Battery Only: {round(accumulated_pnl_series_battery_only[-1], 2)}EU')

    ax3.plot(ts_series, da_prices_series, label='DA prices')

    ax4.plot(ts_series, np.cumsum(prevented_slippage))

    ax1.set_ylabel('Schedule', fontsize=9)
    ax2.set_ylabel('P&L', fontsize=9)
    ax3.set_ylabel('DA prices', fontsize=9)
    ax4.set_ylabel('Prevented \n slippage [EUR]', fontsize=9)

    ax4.xaxis.set_major_locator(mdates.HourLocator())
    ax4.xaxis.set_major_formatter(mdates.DateFormatter('%H:00'))
    ax4.xaxis.set_minor_locator(mdates.MinuteLocator(byminute=[15, 30, 45]))
    # plt.show()
    ax4.tick_params(rotation=90, labelsize=9, axis='x')

    ax1.legend(fontsize=7, bbox_to_anchor=(1, 1))
    ax2.legend(fontsize=7, bbox_to_anchor=(1, 1))
    ax3.legend(fontsize=7, bbox_to_anchor=(1, 1))
    # ax4.legend(fontsize=7,bbox_to_anchor=(1,1))

    plt.tight_layout()
    return fig


def run_single_optimization_colocation(battery_capacity=4, max_power_pv=8, starting_soc=0.1, p_limit=0.1, date='2025-01-15', charge_from_grid=True, no_pv=False, etp_cost=5, average_bid_ask_spread=1):
    """
    Runs a single optimization using passed battery/PV specifications.
    """
    def soc_calculation(model, t):
        """
        Defines the calculation for the SOC at time-index t
        """
        preceding_t = [ts for ts in model.t if ts <= t]
        return battery_capacity*starting_soc/100+np.sum([model.p[t] for t in preceding_t])/4

    def constraint_p_max(model, t):
        """
        Constrains charging power of the battery. Depends on whether the battery is allowed to charge from the grid
        """
        if charge_from_grid:
            return model.p[t] <= p_limit
        else:
            return model.p[t] <= model.pv[t]

    def constraint_p_min(model, t):
        """
        Constrains discharging power of the battery.
        """
        return model.p[t] >= -p_limit

    def constraint_soc_lower(model, t):
        """Sets lower limit of the SOC"""
        return model.soc[t] >= 0

    def constraint_soc_upper(model, t):
        """Sets upper limit of the SOC"""
        return model.soc[t] <= battery_capacity

    def cashflow_rule_colocation(model, t):
        """
        Defines the cashflow calculation at time-index t
        """
        return model.da[t]*(model.pv[t]-model.p[t])/4

    def cashflow_rule_only_pv(model, t):
        """
        Defines the cashflow calculation at time-index t of the PV-only scenario
        """
        return model.da[t]*model.pv[t]/4

    # Trick for including an absolute value term in the objective
    def absolute_value_constraint(model, t):
        """
        Some trickery to get access to the absolute value in the objective function. t1[t]+t2[t] would always be equal to abs(p[t])
        """
        return model.t1[t]-model.t2[t] == model.p[t]

    def objective_expression(model):
        """
        Defines the objective calculation. One term for the profit, one term that penalizes energy throughput in the battery
        """
        return sum(-model.da[t]*(model.p[t]-model.pv[t]) for t in model.t)/4-sum((model.t1[t]+model.t2[t]) for t in model.t)*etp_cost/4
        # return sum(-model.da[t]*(model.p[t]-model.pv[t]) for t in model.t)

    model = pyo.ConcreteModel()
    df = prepare_data.merge_prices_and_solar(date=date)

    if no_pv:
        df['solar_production_mw'] = 0

    # Scale the solar production to the production capacity
    df['solar_production_mw'] *= max_power_pv

    df = df.set_index('start_ts', drop=True)

    model.t = pyo.Set(initialize=df.index)

    # Parameters (given data)
    model.pv = pyo.Param(
        model.t, initialize=df.solar_production_mw, mutable=False)
    model.da = pyo.Param(model.t, initialize=df.da_price, mutable=False)

    # Variables
    # p>0 -> charging. p<0 -> discharging
    model.p = pyo.Var(model.t, within=pyo.Reals, initialize=0)

    # Expressions
    model.soc = pyo.Expression(model.t, rule=soc_calculation)

    # Constraints
    model.constraint_p_max = pyo.Constraint(model.t, expr=constraint_p_max)
    model.constraint_p_min = pyo.Constraint(model.t, expr=constraint_p_min)
    model.constraint_soc_lower = pyo.Constraint(
        model.t, expr=constraint_soc_lower)
    model.constraint_soc_upper = pyo.Constraint(
        model.t, expr=constraint_soc_upper)

    # Trick to get the absolute value to work in the objective function. Based on https://math.stackexchange.com/questions/432003/converting-absolute-value-program-into-linear-program
    model.t1 = pyo.Var(model.t, within=pyo.NonNegativeReals, initialize=0)
    model.t2 = pyo.Var(model.t, within=pyo.NonNegativeReals, initialize=0)
    model.abs_value_constraint = pyo.Constraint(
        model.t, expr=absolute_value_constraint)

    # Objective
    model.OBJ = pyo.Objective(rule=objective_expression, sense=pyo.maximize)

    model.CF_colocation = pyo.Expression(
        model.t, expr=cashflow_rule_colocation)
    model.CF_pv = pyo.Expression(model.t, expr=cashflow_rule_only_pv)

    # Run optimization

    opt = pyo.SolverFactory('appsi_highs')
    # opt = pyo.SolverFactory('gurobi')

    result = opt.solve(model)
    return model, result

