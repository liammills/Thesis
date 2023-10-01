# Thesis

**Author**

Liam Mills, University of Sydney

Supervised by Gregor Verbič, PhD

## How to run

**Note**: If on an M1/M2 chip, install Rosetta 2 with `softwareupdate --install-rosetta` to ensure compatibility with AMPL modules.

### Using Poetry
1. `poetry shell`
2. `poetry install`
3. `cd hems`
4. `python3 hems_pv_battery`
5. `exit` to exit poetry shell

## External Libraries Used
 - [AmplPy](https://amplpy.readthedocs.io/)
 - [Pandas](https://pandas.pydata.org/)

**Potential**

 - [Pyomo](pyomo.org)
 - [OR Tools (Google)](https://developers.google.com/optimization)
 - [Open NEM Py](https://github.com/opennem/opennempy)
 - [MMS Monthly CLI](https://github.com/prakaa/mms-monthly-cli)
