# EV ADJUSTED MILP HEMS MODEL (Use of Prosumer Owned EVs for Flexibility Services)
# Donald Azuatalam (donald.azuatalam@sydney.edu.au)
# Dr. Gregor Verbic and Dr. Archie Chapman
# Elias Williamson

# SETS
set D; /* Set of half-hourly time steps for 2 days */
#set ebM; /* Set of different values for max storage limit - half hourly */
#set ebm; /* Set of different values for min storage limit - half hourly */

# PARAMETERS
# Tariff data
param c_g{d in D} >= 0; /* Time of use tariff */
param c_flat = 0.31317; /* Flat tariff */
param c_pv = 0.05; /* Feed-in-tariff */

# EV battery Vectorisation
#param ebM{d in D} >= 0;   /* Battery maximum storage limit [kWh] */
#param ebm{d in D} >= 0;   /* Battery minimum storage limit [kWh]*/

# Demand Data
param Pd{d in D} >= 0;  /* Electrical demand (daily load profile) in kW */
param Ppv{d in D} >= 0;  /* Solar PV output (daily PV output profile) in kW */
param PgM = 15;  /* Maximum capacity of grid connection in kW */

# EV Battery and Inverter Data
param ebM{d in D} >= 0;  /* Battery maximum storage limit [kWh] */ #----Vectorised so that the EV can be charged for work
param ebm{d in D} >= 0;  /* Battery minimum storage limit [kWh]*/
param eb1 >= 0;  /* Start-of-day battery state of charge (SOC) */
param ebN{d in D} = 0.2*ebM[d];  /* End-of-day (day 2 in a 2-day rolling horizon) battery state of charge (SOC) -  20% Max SOC*/
param PbM{d in D} >= 0;  /* Battery maximum charging rate [kW] */   #---> vectorised to account for EV being unavailable
param Pbm{d in D} = PbM[d]; /* Battery maximum discharge rate [kW] */  #---> vectorised to account for EV being unavailable
param etaBc >= 0; /* Battery charging efficiency */
param etaBd = etaBc; /* Battery discharging efficiency */
param etaI = 1; /* Inverter efficiency. This is because the inverter efficiency is already accounted for in the PV data */
param dt = 24/48; /* Half hourly time steps */
param N = 96; /* Total number of time-slots for 2 days */

# Commute Data
param early_commute >= 0; /* Time to leave for work - dictates at what time the commute is decreased from battery charge*/
param late_commute >= 0; /* Time to leave for home - dictates at what time the commute is decreased from battery charge*/
param travel_perc >= 0; /*Percentage of EV battery used for commute/travel.*/

# VARIABLES
var Pgplus{d in D} >= 0, <= PgM;  /* Power flowing from grid to customer in kW */
var Pgminus{d in D} >= 0, <= PgM;  /* Power flowing from customer to grid in kW */
var Pbplus{d in D} >= 0, <= PbM[d];  /* Battery charge power in kW */                
var Pbminus{d in D} >= 0, <= Pbm[d];  /* Battery discharge power in kW */
var eb{d in D} >= ebm[d], <= ebM[d];  /* Battery state of charge */               #---- currently edited to set min value for operation of vehicle,
var dg{d in D} binary;   /* Direction of grid power flow (0: demand->grid, 1: grid->demand) */
var sb{d in D} binary;  /* Battery charging status (0: discharge, 1: charge) */

# OBJECTIVE FUNCTION
minimize cost: sum{d in D} (dt*c_g[d]*Pgplus[d] - dt*c_pv*Pgminus[d]); /* Objective function with Time of Use Tariff */
#minimize cost: sum{d in D} (dt*c_flat*Pgplus[d] - dt*c_pv*Pgminus[d]); /* Objective function with Flat Tariff */

subject to
# CONSTRAINTS
# Equality Constraints
Equality_constraint1 {d in D}: Pgplus[d] - Pgminus[d] = etaI*(etaBc*Pbplus[d] - (1/etaBd)*Pbminus[d]) - etaI*Ppv[d] + Pd[d]; /* Power balance constraint */
#Equality_constraint2 {d in D}: eb[d] = if d = 1 then eb1 else if d = N then ebN else eb[d-1] + dt*etaBc*Pbplus[d-1] - dt*(1/etaBd)*Pbminus[d-1]; /* Battery operation */# -- original statement

#Equality_constraint2 {d in D}: eb[d] = if d = 1 then eb1 else if d = 17 then eb[d-1] - 0.1*ebM[d] else if d = 35 then eb[d-1] - 0.1*ebM[d] 
#else if d = N then ebN[d] else eb[d-1] + dt*etaBc*Pbplus[d-1] - dt*(1/etaBd)*Pbminus[d-1]; /* EV Battery operation */

Equality_constraint2 {d in D}: eb[d] = if d = 1 then eb1 else if d = early_commute then eb[d-1] - travel_perc*ebM[d] else if d = late_commute then eb[d-1] - travel_perc*ebM[d] 
/*else if d = early_commute + 48 then eb[d-1] - travel_perc*ebM[d] else if d = late_commute + 48 then eb[d-1] - travel_perc*ebM[d]*/
else if d = N then ebN[d] else eb[d-1] + dt*etaBc*Pbplus[d-1] - dt*(1/etaBd)*Pbminus[d-1]; /* EV Battery operation */

# Inequality Constraints
Inequality_constraint1 {d in D}: Pgplus[d] <= PgM*dg[d];  /* Power limiting strategy  */
Inequality_constraint2 {d in D}: Pgminus[d] <= PgM*(1 - dg[d]);  /* Import/Export constraint - can't import and export at the same time */
Inequality_constraint3 {d in D}: Pbplus[d] <= PbM[d]*sb[d];   /* Battery charging constraint */
Inequality_constraint4 {d in D}: Pbminus[d] <= Pbm[d]*(1 - sb[d]); /* Battery charge/discharge constraint - can't charge and discharge at the same time */
