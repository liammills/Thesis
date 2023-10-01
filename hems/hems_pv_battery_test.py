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

# Hardcoded parameters
N = 4  # Number of time slots in a day
Days = 1  # Number of days
etaBc = etaBd = 0.9  # Battery charge and discharge efficiency
ebM = 10  # Max battery storage in kWh
ebm = 0  # Min battery storage in kWh
PbM = 5  # Max battery charge rate in kW
Pbm = 5  # Max battery discharge rate in kW
eb1 = 0  # Start-of-day battery state of charge (SOC)

ampl.param['etaBc'] = etaBc  # etaBd also set
ampl.param['ebM'] = ebM
ampl.param['ebm'] = ebm
ampl.param['PbM'] = PbM  # Pbm also set
ampl.param['eb1'] = eb1

# Hardcoded data for one day and 4 timeslots
demand_data_day = [5, 4, 3, 2]
pv_data_day = [0, 1, 2, 1]
tariff_data_day = [0.4, 0.4, 0.4, 0.4]

ampl.set['D'] = list(range(1, N + 1))
ampl.getParameter('Pd').setValues(demand_data_day)
ampl.getParameter('Ppv').setValues(pv_data_day)
ampl.getParameter('c_g').setValues(tariff_data_day)

ampl.solve()

# Collect results
variables = ['Pgplus', 'Pgminus', 'Pbplus', 'Pbminus', 'sb', 'dg', 'eb']
results = {var: ampl.getVariable(var).getValues().toPandas()[f'{var}.val'].values for var in variables}

# Convert to DataFrame for easier visualization
df_results = pd.DataFrame(results)
df_results['TimeSlot'] = range(1, N + 1)
print(df_results)

# Plot results
for var in variables:
    plt.figure()
    plt.plot(df_results['TimeSlot'], df_results[var])
    plt.title(f'{var} for 1 Day')
    plt.xlabel('Time Slot')
    plt.ylabel(var)
    plt.show()
