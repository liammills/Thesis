from amplpy import AMPL, Environment
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import pathlib
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(pathlib.Path.cwd() / '.env')

ampl = AMPL(Environment('/Users/liammills/Desktop/uni/Thesis/ampl_macos64'))#/Users/liammills/Desktop/uni/Thesis/ampl_macos64
ampl.setOption('solver', 'cplex')
ampl.setOption('license_uuid', os.environ.get('AMPL_UUID'))
ampl.read('./hems_pv_battery.mod')

N = 48  # Number of time slots in a day (half-hourly intervals)
Days = 1 # Number of days to simulate
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

site_id = 152786204 # 289382707 | 152786204
df = pd.read_csv('./data/HalfHourly_PV_Load_Data/halfhourly_{}.csv'.format(site_id))
tou_df = pd.read_csv('./Data/tou_data.csv')
site_details_df = pd.read_csv('./data/site_details.csv')

selected_site = site_details_df[site_details_df['site_id'] == site_id]
state = selected_site['state'].values[0]
postcode = selected_site['postcode'].values[0]

df['total_load'] = df['total_load'] / (0.5 * 1000)  # Convert from Wh to kW for 30-min intervals
df['pv_generation'] = df['pv_generation'] / (0.5 * 1000)  # Convert from Wh to kW for 30-min intervals
df['pv_generation'] = df['pv_generation'].apply(lambda x: max(0, x)) # Remove negative values
df.rename(columns={
    'total_load': 'total_load_kWh',
    'pv_generation': 'pv_generation_kWh'
}, inplace=True)
if len(df) % 48 != 0:
    df = df.iloc[:-1]
tou_repeated = np.tile(tou_df['Cost(k) $/kWh'].values, 365)
df['time_of_use_tariff'] = tou_repeated[:len(df)]

def plot_daily_results(total_load, pv_generation, battery_soc, day, avg=False):
    start_idx = day * 48  # Assuming half-hourly data and 2-day horizon
    time_intervals = [t.strftime('%H:%M') for t in pd.date_range("00:00", "23:30", freq="30min").time]
    tick_locations = [time_intervals[i] for i in range(0, 48, 6)]
    tick_locations.append('24:00')
    plt.figure(figsize=(12, 6))
    formatted_date = (datetime(2019, 1, 1) + timedelta(days=day)).strftime('%B %d, %Y')
    if avg:
        title = f"Average Energy Metrics from January 1, 2019 to {formatted_date} ({state}, {postcode})"
    else:
        title = f"Energy Metrics for {formatted_date} ({state}, {postcode})"
    if avg:
        plt.plot(time_intervals, total_load, label='Total Load')
        plt.plot(time_intervals, pv_generation, label='PV Generation')
        plt.plot(time_intervals, battery_soc, label='Battery State of Charge')
    else:
        start_idx = day * 48
        plt.plot(time_intervals, total_load.iloc[start_idx:start_idx+48], label='Total Load')
        plt.plot(time_intervals, pv_generation.iloc[start_idx:start_idx+48], label='PV Generation')
        plt.plot(time_intervals, battery_soc.iloc[start_idx:start_idx+48], label='Battery State of Charge')  
    plt.legend()
    plt.title(title)
    plt.xlabel('Time of Day')
    plt.ylabel('kWh')
    plt.xticks(tick_locations)
    plt.tight_layout()
    plt.show()

df_results = pd.DataFrame()

for day in range(max(Days - 1, 1)):
    start = day * N
    end = start + 2*N

    demand_data_day = df['total_load_kWh'].iloc[start:end].values
    pv_data_day = df['pv_generation_kWh'].iloc[start:end].values
    tariff_data_day = df['time_of_use_tariff'].iloc[start:end].values

    ampl.set['D'] = list(range(1, 2*N + 1))
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
        'Pgplus': Pgplus[:N],
        'Pgminus': Pgminus[:N],
        'Pbplus': Pbplus[:N],
        'Pbminus': Pbminus[:N],
        'sb': sb[:N],
        'dg': dg[:N],
        'eb': eb[:N]
    })

    df_results = pd.concat([df_results, df_day_result], ignore_index=True)

df_results.to_csv('ampl_results.csv', index=False)

plot_daily_results(df['total_load_kWh'], df['pv_generation_kWh'], df_results['eb'], day)

end_idx = Days * int(N)
numeric_cols = df.select_dtypes(include=[np.number]).columns
avg_input = df[numeric_cols].iloc[:end_idx].groupby(np.arange(end_idx) % 48).mean()
avg_results = df_results.groupby('TimeSlot').mean()[:int(N)]
plot_daily_results(avg_input['total_load_kWh'], avg_input['pv_generation_kWh'], avg_results['eb'], day, True)

del df_day_result