# from amplpy import AMPL, DataFrame
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import pathlib

from amplpy import AMPL, Environment
from dotenv import load_dotenv

load_dotenv(pathlib.Path.cwd() / '.env')

ampl = AMPL(Environment('/Users/liammills/Desktop/uni/Thesis/ampl_macos64'))#/Users/liammills/Desktop/uni/Thesis/ampl_macos64
ampl.setOption('solver', 'cplex')
ampl.setOption('license_uuid', os.environ.get('AMPL_UUID'))
ampl.read('./hems_pv_battery.mod')

N = 48  # Number of time slots in a day (half-hourly intervals)
Days = 365  # Number of days
etaBc = etaBd = np.sqrt(0.84)  # Battery charge and discharge efficiency
ebM = 10  # Max battery storage in kWh
ebm = 0  # Min battery storage in kWh
PbM = 5  # Max battery charge rate in kW
Pbm = 5  # Max battery discharge rate in kW
eb1 = 0  # Start-of-day battery state of charge (SOC)

ampl.param['etaBc'] = etaBc # etaBd also set
ampl.param['ebM'] = ebM
ampl.param['ebm'] = ebm
ampl.param['PbM'] = PbM # Pbm also set
ampl.param['eb1'] = eb1
ampl.param['N'] = N

# Read actual data
# df = pd.read_csv('./data/HalfHourly_PV_Load_Data/halfhourly_152786204.csv')
df = pd.read_csv('./data/HalfHourly_PV_Load_Data/halfhourly_289382707.csv')
df['total_load'] = df['total_load'] / (0.5 * 1000)  # Convert from Wh to kW for 30-min intervals
df['pv_generation'] = df['pv_generation'] / (0.5 * 1000)  # Convert from Wh to kW for 30-min intervals
df['pv_generation'] = df['pv_generation'].apply(lambda x: max(0, x)) # Remove negative values
df.rename(columns={
    'total_load': 'total_load_kWh',
    'pv_generation': 'pv_generation_kWh'
}, inplace=True)
df['time_of_use_tariff'] = 0.4 # TODO: Get actual tariff data
print(df)

# Mock-up df with historical data for a year
# np.random.seed(0)
# df = pd.DataFrame({
#     'total_load_kWh': np.random.rand(Days * N) * 10,
#     'pv_generation_kWh': np.random.rand(Days * N) * 5,
#     'time_of_use_tariff': np.random.rand(Days * N) * 0.4
# })

def plot_data(x, y, title, xlabel, ylabel, plot_type='line'):
    plt.figure(figsize=(12, 6))
    if plot_type == 'line':
        plt.plot(x, y)
    elif plot_type == 'step':
        plt.step(x, y, where='post')
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.show()

# plot_data(range(1, N + 1), df['total_load_kWh'].iloc[:N], "Total Load - Day 1", "Time Slot", "Load (kWh)")
# plot_data(range(1, N + 1), df['pv_generation_kWh'].iloc[:N], "PV Generation - Day 1", "Time Slot", "PV Generation (kWh)")

df_results = pd.DataFrame()

for day in range(Days):
    start = day * N
    end = start + N

    demand_data_day = df['total_load_kWh'].iloc[start:end].values
    pv_data_day = df['pv_generation_kWh'].iloc[start:end].values
    tariff_data_day = df['time_of_use_tariff'].iloc[start:end].values
    
    # if day == 0 or day == 150:  # Only plot for the first day and day 150
    #     plot_data(range(1, N + 1), demand_data_day, f"Total Load - Day {day+1}", "Time Slot", "Load (kWh)")
    #     plot_data(range(1, N + 1), pv_data_day, f"PV Generation - Day {day+1}", "Time Slot", "PV Generation (kWh)")

    ampl.set['D'] = list(range(1, N + 1))
    ampl.getParameter('Pd').setValues(demand_data_day)
    ampl.getParameter('Ppv').setValues(pv_data_day)
    ampl.getParameter('c_g').setValues(tariff_data_day)

    ampl.solve()

    Pgplus = ampl.getVariable('Pgplus').getValues().toPandas()['Pgplus.val'].values
    Pgminus = ampl.getVariable('Pgminus').getValues().toPandas()['Pgminus.val'].values
    Pbplus = ampl.getVariable('Pbplus').getValues().toPandas()['Pbplus.val'].values
    Pbminus = ampl.getVariable('Pbminus').getValues().toPandas()['Pbminus.val'].values
    sb = ampl.getVariable('sb').getValues().toPandas()['sb.val'].values
    dg = ampl.getVariable('dg').getValues().toPandas()['dg.val'].values
    eb = ampl.getVariable('eb').getValues().toPandas()['eb.val'].values

    df_day_result = pd.DataFrame({
        'Day': [day] * N,
        'TimeSlot': range(1, N + 1),
        'Pgplus': Pgplus,
        'Pgminus': Pgminus,
        'Pbplus': Pbplus,
        'Pbminus': Pbminus,
        'sb': sb,
        'dg': dg,
        'eb': eb
    })
    df_results = pd.concat([df_results, df_day_result], ignore_index=True)

    # if day == 0 or day == 150:  # Only plot for the first day and day 150
    #     plot_data(range(1, N + 1), Pgplus, f"Pgplus - Day {day+1}", "Time Slot", "Pgplus (kW)")
    #     plot_data(range(1, N + 1), Pgminus, f"Pgminus - Day {day+1}", "Time Slot", "Pgminus (kW)")
    #     plot_data(range(1, N + 1), Pbplus, f"Pbplus - Day {day+1}", "Time Slot", "Pbplus (kW)")
    #     plot_data(range(1, N + 1), Pbminus, f"Pbminus - Day {day+1}", "Time Slot", "Pbminus (kW)")
    #     plot_data(range(1, N + 1), sb, f"sb - Day {day+1}", "Time Slot", "Battery status", plot_type='step')
    #     plot_data(range(1, N + 1), dg, f"dg - Day {day+1}", "Time Slot", "Grid flow direction flag", plot_type='step')
    #     plot_data(range(1, N + 1), eb, f"eb - Day {day+1}", "Time Slot", "eb (kWh)")

df_results.to_csv('ampl_results.csv', index=False)

def plot_average_data(df, variable, title, xlabel, ylabel, plot_type='line'):
    avg_data = df.groupby('TimeSlot')[variable].mean()
    plot_data(avg_data.index, avg_data.values, title, xlabel, ylabel, plot_type)

plot_average_data(df_results, 'Pgplus', 'Average Power drawn from grid', 'Time Slot', 'Average Power drawn (Pgplus - kW)')
plot_average_data(df_results, 'Pbplus', 'Average Battery charge power', 'Time Slot', 'Average Battery charge power (Pbplus - kW)')
plot_average_data(df_results, 'Pbminus', 'Average Battery discharge power', 'Time Slot', 'Average Battery discharge power (Pbminus - kW)')
plot_average_data(df_results, 'sb', 'Average Battery Status', 'Time Slot', 'Average Battery Status (sb)', 'step')
