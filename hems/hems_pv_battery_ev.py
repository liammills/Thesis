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
ampl.read('./hems_pv_battery_ev.mod')

# Model parameters
N = 48  # Time slots in a day (half-hourly)
# Days = 30  # Number of days to simulate
etaBc = etaBd = np.sqrt(0.84)  # Battery efficiencies
eb1 = 0  # Initial state of charge

# EV-specific parameters
early_commute = 8  # Time to leave for work (in terms of half-hourly slots)
late_commute = 32  # Time to leave for home (in terms of half-hourly slots)
travel_perc = 0.2  # Percentage of battery used for travel

# Depends on model of EV
ebM = 40
ebm = 8.16
PbM = Pbm = 6.6
# max_charge = ones(48,1)*max_soc

# Set static parameters
ampl.param['etaBc'] = etaBc
ampl.param['eb1'] = eb1
ampl.param['early_commute'] = early_commute
ampl.param['late_commute'] = late_commute
ampl.param['travel_perc'] = travel_perc
ampl.param['N'] = N
ampl.param['ebM'] = ebM
ampl.param['ebm'] = ebm
ampl.param['PbM'] = PbM
ampl.param['Pbm'] = Pbm

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

def plot_data(x, y, title, xlabel, ylabel, plot_type='line', custom_ticks=None):
    plt.figure(figsize=(12, 6))
    if plot_type == 'line':
        plt.plot(x, y)
    elif plot_type == 'step':
        plt.step(x, y, where='post')
    plt.title('EV '+title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    if custom_ticks:
        plt.yticks(list(custom_ticks.keys()), list(custom_ticks.values()))
    plt.show()

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

def plot_average_data(df, variable, title, xlabel, ylabel, plot_type='line', custom_ticks=None):
    avg_data = df.groupby('TimeSlot')[variable].mean()
    plot_data(avg_data.index, avg_data.values, title, xlabel, ylabel, plot_type, custom_ticks)

plot_average_data(df_results, 'Pgplus', 'Average Power drawn from grid', 'Time Slot', 'Average Power drawn (Pgplus - kW)')
plot_average_data(df_results, 'Pbplus', 'Average Battery charge power', 'Time Slot', 'Average Battery charge power (Pbplus - kW)')
plot_average_data(df_results, 'Pbminus', 'Average Battery discharge power', 'Time Slot', 'Average Battery discharge power (Pbminus - kW)')
plot_average_data(df_results, 'sb', 'Average Battery Status', 'Time Slot', 'Average Battery Status (sb)', 'step', custom_ticks={0: 'Discharging', 1: 'Charging'})
