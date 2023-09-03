import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from markov_functions import markov_weekday, markov_weekend
from hems import hems_week_ev

# Initialize variables and arrays
usage_iterations, availability_iterations = 5, 7
weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
costs_by_day = {day: np.zeros((usage_iterations, availability_iterations)) for day in weekdays}
max_charge_level, min_charge_level, charge_rate = 40, 8.16, 6.6
max_charge_array = np.ones(48) * max_charge_level

data_folder = './data'
csv_file_list = [file for file in os.listdir(data_folder) if file.endswith('.csv')]
print(csv_file_list)

# Monte Carlo simulation loop
for file_idx in range(24):
    csv_path = os.path.join(data_folder, csv_file_list[file_idx])
    data_frame = pd.read_csv(csv_path)
    
    # Perform checks and read demand, PV data
    if len(data_frame) != 17521 or data_frame.isnull().values.any():
        continue
    
    demand = data_frame.iloc[:, 2].values  # Assuming 3rd column is demand
    demand = demand[:17520]  # Remove 1st timestamp of the next year
    PV = data_frame.iloc[:, 1].values  # Assuming 2nd column is PV generation
    PV = PV[:17520]  # Remove 1st timestamp of the next year
    
    # Convert Wh to kW (data is in 5-minute increments)
    demand = demand / 1000 * 12
    PV = PV / 1000 * 12

    for avail_idx in range(availability_iterations):
        weekday_availability, weekday_min_charge = markov_weekday(min_charge_level, charge_rate)
        weekend_availability, weekend_min_charge = markov_weekend(min_charge_level, charge_rate)

        for usage_idx in range(usage_iterations):
            rand_usage = np.random.rand()
            daily_costs = hems_week_ev(rand_usage, demand, PV, weekday_availability, weekend_availability, max_charge_array, weekday_min_charge, weekend_min_charge)
            
            for day_idx, day in enumerate(weekdays):
                costs_by_day[day][usage_idx, avail_idx] = daily_costs[day_idx]

# Plotting
fig, axes = plt.subplots(4, 2)
for idx, ax in enumerate(axes.flatten()[:-1]):
    ax.hist(costs_by_day[weekdays[idx]].flatten())
    ax.set_title(weekdays[idx])
    
plt.show()
