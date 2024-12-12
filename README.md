# BPlot (B-RISK Plot)
A library to easily make professional plots from B-RISK Results. Tested with B-RISK version 2023.1.

## General Usage
1. Run your B-RISK analysis (bsest of the "auto-save results excel" is checked), click save (optional: reduce the "Excel output interval to 1s)
2. Either:
    a. Create a zip of the results folder (right-click the "basemodel_***" folder and click "Send to -> zip", then copy this folder to your working location).
    b. Copy the "basemodel_***" folder to your working directory.
3. Pass the path to the zip folder or the results directopry to the "b_risk_results" class constructor
```
import bplot as bp
results = bp.b_risk_results('basemodel_example.zip')
```
4. Make plots. 
Each plotting command returns the matplotlib figure and the axes so you can further customize the figures as required and then save them.
```
f, a = results.plot_hrr()
f.savefig('out.png')
```

Note that bplot assumes an upper layer emissivity of 1. Therefore, will give slightly higher FED_thermal than B-RISK will calculate.

See the "examples" directory for a tutorial which shows all the features of BPlot.

## Installation
Install directly from github with:
`pip install https://github.com/user/repository/archive/branch.zip`

## Default Styling
The default styling of plots (e.g. line colours, widths etc) is handled through the `event_style`, `user_style` and `tenability_style` objects in the BPlot package. See the Tutorial for how to modify the default styles.

### List of plot functions
#### Simulation parameter plots
 - plot_mass_loss_rate
 - plot_plume_mass_flow

#### Room parameter plots
 - plot_hrr
 - plot_layer_height
 - plot_upper_layer_temp
 - plot_lower_layer_temp
 - plot_pressure
 - plot_visibility
 - plot_vent_flow_upper
 - plot_vent_flow_lower
 - plot_vent_flow_outside

**Species**
 - plot_CO2_upper
 - plot_CO2_lower
 - plot_CO_upper
 - plot_CO_lower
 - plot_O2_upper
 - plot_O2_lower
 - plot_HCN_upper
 - plot_HCN_lower

**Temperatures**
 - plot_ceiling_temp
 - plot_wall_temp_upper
 - plot_wall_temp_lower
 - plot_rad_on_floor
 - plot_rad_on_target


## Development
Clone the repository, then `pip install -e .`

## Background - Getting Data from B-RISK
There are four ways of getting data out of B-RISK:
1. Excel output by clicking the Excel icon button in the top toolbbar ("Send Output to Excel File") or ticking the "Auto-save results excel" checkbox
2. Logfile output by clicking the printer icon in the toolbar ("Print Input & Results")
3. Exporting Monte-Carlo Results button for a single iteration (this works even if one calculation was doner e.g. in C/VM2 mode)
4. Reading the "dumpdata.dat" file

The advantages and limitations of each approach are discussed below. There is no perfect approach.

1. Export to Excel File
This option works ok, but you have to click the export button every time to save the results (the checkbox isn't saved if you close B-RISK).
There are a number of parameters e.g. sprinkler temperature, smoke obscuration at detector which are not saved (ambient values are written in the excel file for all time steps).
Also, B-RISK controls the number of rows that are written to be no more than 32000 rows across all rooms (see the `Create_excel` function in the decompile B-RISK).
There are some parameters that are not written to this file that are written in other formats e.g. upper layer emissivity.

2. Log file output
The variables to export have to be selected manually (this involves checking 20+ checkboxes.
The output format is not as easily read as csv and other formats.
The logfile must manually be saved after running an analysis.

3. Export Monte-Carlo Results
This exports similar results to option 1, however, with less mistakes. e.g the sprinkler temperature is actually written.
The major advantage is that data is written for every timestep that it is calculated (not a reduced number of rows as in option 1).
However, the data must be manually exported after every analysis which requires a number of clicks.
Furthermore, each room must be exported individually which becomes burdonsome for models with more than a few rooms.

4. Reading the "dumpdata.dat" file
The "dampdata.dat" file is a dump file written by b-risk. It is not meant for external use, but as a record of key calculated output parameters.
The results are written every timestep including some variables not available through the B-risk GUI e.g upper layer emissivity.
However, the species concentrations are written as mass fraction, but volume fractions are required to calculate teh FED_co.
This effectively makes this format useless. The other disadvantage is that the structure of this file could change with any B-Risk release.

B-RISK is a .NET application so is easy to decompile (you can use ILSpy or dnSpy). Some key functions are:
- `BRISK.MAIN.Create_excel()` writes the excel file for option 1
- `BRISK.frmInputs.save_dumpfile()` writes the "dumpdata.dat" file
- `BRISK.MDIFrmMain.Read_dumpfile()` reads the "dumpdata.dat" file
- `BRISK.frmInputs.ExportFromDump()` writes the excel file for option 3

