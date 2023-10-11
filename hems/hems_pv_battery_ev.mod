# Donald Azuatalam (donald.azuatalam@sydney.edu.au)
# Dr. Gregor Verbic and Dr. Archie Chapman
# Elias Williamson

# Set and Parameters
set D; # Set of half-hourly time steps

param c_g{d in D} >= 0; # Time of use tariff
param c_flat = 0.31317; # Flat tariff
param c_pv = 0.05; # Feed-in-tariff
param Pd{d in D} >= 0; # Electrical demand (daily load profile) in kW
param Ppv{d in D} >= 0; # Solar PV output (daily PV output profile) in kW
param PgM = 15; # Maximum capacity of grid connection in kW

# EV-specific parameters
param ebM{d in D} >= 0; # Battery maximum storage limit [kWh]
param ebm{d in D} >= 0; # Battery minimum storage limit [kWh]
param eb1 >= 0; # Start-of-day battery state of charge (SOC)
param ebN{d in D} = 0.2*ebM[d]; # End-of-day battery state of charge (SOC)
param PbM{d in D} >= 0; # Battery maximum charging rate [kW]
param Pbm{d in D} = PbM[d]; # Battery maximum discharge rate [kW]
param etaBc >= 0; # Battery charging efficiency
param etaBd = etaBc; # Battery discharging efficiency
param etaI = 1; # Inverter efficiency
param dt = 24/48; # Half-hourly time steps
param N; # Total number of time slots

# Commute Data
param early_commute >= 0;
param late_commute >= 0;
param travel_perc >= 0;

# Variables
var Pgplus{d in D} >= 0, <= PgM;
var Pgminus{d in D} >= 0, <= PgM;
var Pbplus{d in D} >= 0, <= PbM[d];
var Pbminus{d in D} >= 0, <= Pbm[d];
var eb{d in D} >= ebm[d], <= ebM[d];
var dg{d in D} binary;
var sb{d in D} binary;

# Objective Function: Minimize daily electricity cost
minimize cost: sum{d in D} (dt*c_g[d]*Pgplus[d] - dt*c_pv*Pgminus[d]);

# Constraints
subject to power_balance {d in D}: 
    Pgplus[d] - Pgminus[d] = etaI*(etaBc*Pbplus[d] - (1/etaBd)*Pbminus[d]) - etaI*Ppv[d] + Pd[d];

subject to battery_operation_ev {d in D}: 
    eb[d] = if d = 1 then eb1 else if d = early_commute then eb[d-1] - travel_perc*ebM[d] else if d = late_commute then eb[d-1] - travel_perc*ebM[d] else if d = N then ebN[d] else eb[d-1] + dt*etaBc*Pbplus[d-1] - dt*(1/etaBd)*Pbminus[d-1];

subject to grid_power_limit {d in D}: 
    Pgplus[d] <= PgM*dg[d];

subject to grid_import_export_limit {d in D}: 
    Pgminus[d] <= PgM*(1 - dg[d]);

subject to battery_charge_limit {d in D}: 
    Pbplus[d] <= PbM[d]*sb[d];

subject to battery_discharge_limit {d in D}: 
    Pbminus[d] <= Pbm[d]*(1 - sb[d]);
