import math, os, zipfile, glob
import pandas as pd
import numpy as np
from cycler import cycler
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
from striprtf.striprtf import rtf_to_text # required to read rtf formatted log file
import importlib.metadata # for getting package version
from datetime import datetime
import bplot

def _get_mpl_plt():
    """
    Returns the matplotlib.pyplot import reference so modifications to defaults can be made by advanced users.
    """
    return plt

class b_risk_results:
    """
    Class for reading B-RISK results and creating professional plots easily.

    The data property is a dict that stores the B-RISK result data. The keys are the names of the rooms and the values are dataframes of the result data.

    """

    def __open_filename(self, path_name, filename_suffix):
        """
        Provide an IO[bytes] object for the file specified by filename_suffix in either the directory or zipfile specified by pathname.

        Args:
            path_name (str): path to directory or zipfile containing the B-RISK results
            filename_suffix (str): The suffix of the desired file to read.

        Raises:
            Exception: If more than one file matches filename_suffix
            Exception: If path_name is not a directory or a zipfile

        Returns:
            IO[bytes]: Byte stream of specified file
        """        
        # name is either a directory or a zip folder
        if os.path.isdir(path_name):
            f = glob.glob(os.path.join('.', '*'+filename_suffix))
            if len(f) == 1:
                return open(f[0], 'rb')
            else:
                raise Exception(f'More than 1 file found for suffix "{filename_suffix}": {f}')
        elif zipfile.is_zipfile(path_name):
            with zipfile.ZipFile(path_name) as myzip:
                _matching_files = [n for n in myzip.namelist() if n.endswith(filename_suffix)]
                if len(_matching_files) == 1:
                    return myzip.open(_matching_files[0])
                else:
                    raise Exception(f'More than 1 file found for suffix "{filename_suffix}": {_matching_files}')
            pass
        else:
            raise Exception(f'{path_name} is not a directory or a zip file')

    def __init__(self, filename, figure_width=150, figure_height=150/1.6):
        """
        Create the b-risk results object. First read the data (log.rtf, input1.xml, results.xlsx), then run the setup code.
        Note that since a lot of plots are repetitive, a setup function is used to create the plotting functions.

        Args:
            filename (str): path to zipfile (no extension) or directory that contains the B-RISK results.
            figure_width (int, optional): Default with of figure in mm. Defaults to 150.
            figure_height (int or float, optional): Default height of figure in mm. Defaults to 150/1.6.

        Returns:
            b_risk_results: results
        """
        self.__filename = filename

        print(f'BPlot (B-RISK Plot) version: {importlib.metadata.version("bplot")} (Run on {datetime.today().strftime("%d-%m-%Y")})')

        # Step 1: Read B-RISK output log
        with self.__open_filename(filename, '_log.rtf') as f:
            self.log_text = rtf_to_text(f.read().decode()).split('\n')[:-2] # last two lines neglected as empty
        for i in range(len(self.log_text)):
            self.log_text[i] = self.log_text[i]
        print('READ Log')
        # print(self.log_text)

        # Get important times
        sprinkler_times = []
        smoke_detector_times = []
        for s in self.log_text:
            if 'Sprinkler' in s and 'responded' in s:
                __s = s.split()
                sprinkler_times.append(['Sprinkler '+__s[3], int(__s[0])])
                print(f'Found: {sprinkler_times[-1][0]} activated at {sprinkler_times[-1][1]} s')
            if 'Smoke detector' in s and 'operates' in s:
                __s = s.split()
                smoke_detector_times.append(['Smoke detector '+__s[4], int(__s[0])])
                print(f'Found: {smoke_detector_times[-1][0]} activated at {smoke_detector_times[-1][1]} s')

        self.sprinkler_times = sprinkler_times
        self.smoke_detector_times = smoke_detector_times


        # Step 2: Read B-RISK input file to get key parameters
        with self.__open_filename(filename, 'input1.xml') as f:
            tree = ET.parse(f)

            # for each room get name, height (because layer height is height above floor level)
            self.input_rooms = {}
            self.input_rooms_by_name = {}
            all_rooms = tree.findall('rooms/room')
            for r in all_rooms:
                _room = {'name': r.find('description').text,
                        'max height': float(r.find('max_height').text),
                        'min height': float(r.find('min_height').text),
                        'length': float(r.find('length').text),
                        'width': float(r.find('width').text)}
                self.input_rooms[int(r.attrib['id'])] = _room
                self.input_rooms_by_name[_room['name']] = _room
            print(f'READ input.xml ({len(self.input_rooms.keys())} rooms)')

        # Step 3: Read B-RISK Results
        def _valid_column(name): # for checking whether excel columns are valid and should be read
            if type(name) is str:
                return not 'Unnamed' in name
            else:
                return False
        self.data = pd.read_excel(io=self.__open_filename(filename, '_results.xlsx'), sheet_name=None, usecols=_valid_column)
        for i in range(len(self.data.keys())-1):
            # rename keys to room names
            self.data[self.input_rooms[i+1]['name']] = self.data.pop(f'Room {i+1}')
            # rename the 'CO2 Lower(%)' column with space separation
            self.data[self.input_rooms[i+1]['name']] = self.data[self.input_rooms[i+1]['name']].rename(columns={'CO Lower(ppm)': 'CO Lower (ppm)'})
            # rename the 'Layer (m)' column to 'Layer Height (m)' column
            self.data[self.input_rooms[i+1]['name']] = self.data[self.input_rooms[i+1]['name']].rename(columns={'Layer (m)': 'Layer Height (m)'})
        print(f"READ Results: From {self.data['Outside']['Time (sec)'].iloc[0]} to {self.data['Outside']['Time (sec)'].iloc[-1]} seconds")

        # Step 5: Set default matplotlib properties
        plt.rc('figure', 
                figsize=[figure_width/25.6, figure_height/25.6], # convert from mm to inches
                dpi=100)
        plt.rc('savefig', dpi=300)
        plt.rc('lines', linewidth=2)
        # COLOURS
        default_cycler = (cycler(linestyle=['-', '--', ':', '-.']) * cycler(color=['hotpink', 'orange', 'cornflowerblue', 'blueviolet']))
        plt.rc('axes', prop_cycle=default_cycler)
        plt.rc('figure', autolayout=True) # auto use tight_layout

        ###########################
        ###### Plotting Functions
        ###########################
      
        #### Single variable plots ####
        self.plot_mass_loss_rate = self.__single_var_plot('Mass Loss Rate (kg/s)')
        self.plot_plume_mass_flow = self.__single_var_plot('Plume (kg/s)')

        #### Room variable plots ####
        self._plot_hrr = self.__room_var_plot('HRR (kW)') # this core function is wrapped by plot_hrr below

        self.plot_layer_height = self.__room_var_plot('Layer Height (m)')
        self.plot_upper_layer_temp = self.__room_var_plot('Upper Layer Temp (C)')
        self.plot_lower_layer_temp = self.__room_var_plot('Lower Layer Temp (C)')
        self.plot_pressure = self.__room_var_plot('Pressure (Pa)')
        self.plot_visibility = self.__room_var_plot('Visibility (m)')

        #### Species ####
        self.plot_CO2_upper = self.__room_var_plot('CO2 Upper(%)')
        self.plot_CO2_lower = self.__room_var_plot('CO2 Lower(%)')
        self.plot_CO_upper = self.__room_var_plot('CO Upper (ppm)')
        self.plot_CO_lower = self.__room_var_plot('CO Lower (ppm)')
        self.plot_O2_upper = self.__room_var_plot('O2 Upper (%)')
        self.plot_O2_lower = self.__room_var_plot('O2 Lower (%)')
        self.plot_HCN_upper = self.__room_var_plot('HCN Upper (ppm)')
        self.plot_HCN_lower = self.__room_var_plot('HCN Lower (ppm)')

        #### Temperatures ####
        self.plot_ceiling_temp = self.__room_var_plot('Ceiling Temp (C)')
        self.plot_wall_temp_upper = self.__room_var_plot('Upper Wall Temp (C)')
        self.plot_wall_temp_lower = self.__room_var_plot('Lower Wall Temp (C)')
        self.plot_rad_on_floor = self.__room_var_plot('Rad on Floor (kW/m2)')
        self.plot_rad_on_target = self.__room_var_plot('Rad on Target (kW/m2)')

        #### Other ####
        self.plot_vent_flow_upper = self.__room_var_plot('Vent Flow to Upper Layer (kg/s)')
        self.plot_vent_flow_lower = self.__room_var_plot('Vent Flow to Lower Layer (kg/s)')
        self.plot_vent_flow_outside = self.__room_var_plot('Vent Flow to Outside (m3/s)')


    def get_rooms(self):
        """
        Get list of room names excluding "Outside"

        Returns:
            list(str): List of room names
        """        
        rooms = list(self.data.keys())
        rooms.remove('Outside')
        return rooms

    def get_max_time(self):
        """
        Get the maximum time for which there were recorded results.

        Returns:
            int: The maximum time for which there were recorded results.
        """        
        return self.data['Outside']['Time (sec)'].iloc[-1]

    
    def format_plot(self, ax, ylabel):
        """
        All axes are formatted with this function to ensure they have a consistent format.
        You can overwrite this function to change the basic formatting to suit your preferences.

        Args:
            ax (axes): Matplotlib axes to foramt
            ylabel (str): Y axes label
        """        
        ax.axes.set_xlim(left=0, right=self.get_max_time())
        ax.axes.set_xlabel('Time (s)')
        time_tick_spacing = math.ceil((self.get_max_time()/10)/60)*60
        ax.xaxis.set_major_locator(ticker.MultipleLocator(time_tick_spacing))
        ax.axes.set_ylim(bottom=0)
        ax.axes.set_ylabel(ylabel)


    def add_spk_lines(self, ax, **kwargs):
        """
        Add a vertical line and text marking when sprinklers activated to the axes.

        Args:
            ax (axes): matplotlib axes to mark
        """        
        for spk_name, spk_time in self.sprinkler_times:
            bplot.add_event_vline(ax, spk_time)
            bplot.add_event_text(ax, spk_time,
                     f'{spk_name}\n({spk_time} s)', **kwargs)

    def add_smoke_detector_lines(self, ax, **kwargs):
        """
        Add a vertical line and text marking when smoke detectors activated to the axes.

        Args:
            ax (axes): matplotlib axes to mark
        """        
        for sd_name, sd_time in self.smoke_detector_times:
            bplot.add_event_vline(ax, sd_time)
            bplot.add_event_text(ax, sd_time,
                     f'{sd_name}\n({sd_time} s)', **kwargs)


    def __single_var_plot(self, var_name, label_name=None):
        """
        Make a function to plot a variable that occurs once in an analysis (i.e. single variable) e.g. plume mass flow.

        Args:
            var_name (str): Column name (in the B-RISK results dataframe) to plot.
            label_name (str, optional): Label to use in plots. Defaults to None.

        Returns:
            function: Plotting function
        """        
        # Returns a function for plotting an analysis variable (e.g. HRR)
        if label_name is None: label_name = var_name

        def plot(show_spk=True):
            """
            Plot the variable.

            Args:
                show_spk (bool, optional): Add a vertical line when sprinklers activated. Defaults to True.

            Returns:
                figure, axes: plot
            """            
            fig, ax = plt.subplots()
            for r in self.get_rooms():
                ax.plot('Time (sec)', var_name, data=self.data[r], label=r)
            ax.legend()
            self.format_plot(ax, ylabel=label_name)
            if show_spk: self.add_spk_lines(ax)
            self.add_smoke_detector_lines(ax)
            return fig, ax
        
        return plot

    def __room_var_plot(self, var_name, label_name=None):
        """
        Make a function to plot a variable that occurs once for each room (i.e. room variable) e.g. upper layer temperature

        Args:
            var_name (str): Column name (in the B-RISK results dataframe) to plot
            label_name (str, optional): Label to use in plots. Defaults to None.

        Returns:
            function: Plotting function.
        """        
        # Returns a function for plotting a room variable (e.g. layer height)
        if label_name is None: label_name = var_name

        def plot(rooms=None, show_spk=True):
            """
            Plot the room variable.

            Args:
                rooms (list(str), optional): List of rooms to plot the variable for. Defaults to all rooms.
                show_spk (bool, optional): Add a vertical line when sprinklers activated. Defaults to True.

            Returns:
                figure, axes: plot
            """            
            if rooms is None: rooms = self.get_rooms()
            fig, ax = plt.subplots()
            for r in rooms:
                ax.plot('Time (sec)', var_name, data=self.data[r], label=r)
            ax.legend()
            self.format_plot(ax, ylabel=label_name)
            if show_spk: self.add_spk_lines(ax)
            self.add_smoke_detector_lines(ax)
            return fig, ax

        return plot

    ###########################
    #### Single variable plots
    ###########################

    def plot_hrr(self, rooms=None, show_spk=True, plot_vent_fire=True):
        """
        Plot the Heat Release Rate.
        A wrapper is required to provide the option to also plot the vent fire.

        Args:
            rooms (_type_, optional): List of rooms to plot the variable for. Defaults to all rooms.
            show_spk (bool, optional): _Whether to add a vertical line when sprinklers activated. Defaults to True.
            plot_vent_fire (bool, optional): Whether to add a line for the ventilation fire. Defaults to True.
        """
        fig, ax = self._plot_hrr(rooms=rooms)
        if plot_vent_fire is True:
            ax.plot('Time (sec)', 'Vent Fire (kW)', data=self.data['Outside'], label='Outside')
        return fig, ax

    ###########################
    #### Room variable plots
    ###########################

    def plot_room_FED_CO(self, rooms=None, monitoring_height=2, FED_threshold=0.3):
        """
        Plot the FED_CO for the rooms.

        Args:
            rooms (list(str), optional): Rooms to plot FED_CO for. Defaults to all rooms.
            monitoring_height (int, optional): Height (m) above floor of room to calculate FED at. Defaults to 2.
            FED_threshold (float, optional): Threshold to mark with horizontal line. Defaults to 0.3.
        """        
        if rooms is None: rooms = self.get_rooms()
        fig, ax = plt.subplots()
        for r in rooms:
            _times, _room_FED_CO = self.calculate_FED_CO_path([r], [], monitoring_height=monitoring_height, FED_threshold=FED_threshold)
            ax.plot(_times, _room_FED_CO, label=r)
        ax.legend()
        bplot.add_tenability_hline(ax, FED_threshold)
        self.format_plot(ax, ylabel='FED_CO')
        self.add_spk_lines(ax)
        self.add_smoke_detector_lines(ax)
        return fig, ax


    def plot_FED_CO_path(self, rooms, transition_times, monitoring_height=2, FED_threshold=0.3):
        """
        Plot the FED_CO along the egress path given by the list of rooms and the transition times.
        If the last transition time is omitted, FED is plotted until the end of the simulation.
        FED_CO is calculated according to the C/VM2 formula.
        FED calculation starts from time zero.

        Args:
            rooms (list(str)): List of rooms.
            transition_times (list(int)): List of times at which movement between rooms occurs. Last number is optional.
            monitoring_height (int, optional): Height (m) above floor of room to calculate FED at. Defaults to 2.
            FED_threshold (float, optional): Threshold to mark with horizontal line. Defaults to 0.3.
        """        
        fig, ax = plt.subplots()
        time, fed = self.calculate_FED_CO_path(rooms, transition_times, monitoring_height, FED_threshold)
        ax.plot(time, fed, label='egress path')
        ax.legend()
        bplot.add_tenability_hline(ax, FED_threshold)
        self.format_plot(ax, ylabel='FED_CO')
        self.add_spk_lines(ax)
        self.add_smoke_detector_lines(ax)
        # add vertical lines and annotations at top of graph
        _xmax = ax.get_xlim()[1]
        transition_times = [0] + transition_times
        if len(transition_times) == len(rooms)-1:
            transition_times.append(self.data[rooms[0]]['Time (sec)'].max())
        for i in range(len(rooms)):
            bplot.add_span_text(ax, transition_times[i], transition_times[i+1], rooms[i])
            bplot.add_user_vline(ax, transition_times[i+1])
        return fig, ax

    def calculate_FED_CO_path(self, rooms, transition_times, monitoring_height=2, FED_threshold=0.3):
        """
        Calculate the FED_CO along the egress path given by the list of rooms and the transition times.
        If the last transition time is omitted, FED is calculated until the end of the simulation.
        FED_CO is calculated according to the C/VM2 formula.
        FED calculation starts from time zero.

        Args:
            rooms (list(str)): List of rooms.
            transition_times (list(int)): List of times at which movement between rooms occurs. Last number is optional.
            monitoring_height (int, optional): Height (m) above floor of room to calculate FED at. Defaults to 2.
            FED_threshold (float, optional): Threshold to mark with horizontal line. Defaults to 0.3.

        Returns:
            times, FED_CO: List of time-FED data points.
        """        
        
        if len(rooms) - len(transition_times) not in [0, 1]:
            raise Exception('Invalid combination of rooms and transition_times')

        if len(transition_times) == len(rooms)-1:
            # FED measured in final room until end of data
            transition_times.append(self.data[rooms[0]]['Time (sec)'].max())

        # prepend 0 to transition times, because transition times will be used to slivce data
        transition_times = [0] + transition_times

        times = [0]
        FED_CO = [0]

        # make list of times
        dfs = []
        for i_r in range(len(rooms)):

            room_df = self.data[rooms[i_r]]

            # check if data start and end slice times exist, if not add them iin via interpolation
            if not transition_times[i_r] in room_df['Time (sec)'].values:
                # add row and add by interpolation
                room_df = pd.concat([room_df, pd.DataFrame({'Time (sec)': [transition_times[i_r]]})])
                room_df = room_df.sort_values('Time (sec)').reindex().interpolate(limit_area='inside')
            if not transition_times[i_r+1] in room_df['Time (sec)'].values:
                # add row and add by interpolation
                room_df = pd.concat([room_df, pd.DataFrame({'Time (sec)': [transition_times[i_r+1]]})])
                room_df = room_df.sort_values('Time (sec)').reindex().interpolate(limit_area='inside')

            # Select data slice
            room_df = room_df[room_df['Time (sec)'].between(transition_times[i_r], transition_times[i_r+1])]

            for i_t in range(1, len(room_df['Time (sec)'])-1):
                # average species concentrations over timestep
                if 0.5*(room_df['Layer Height (m)'].iloc[i_t]+room_df['Layer Height (m)'].iloc[i_t+1]) > monitoring_height: # monitoring height is in lower layer
                    CO2 = 0.5*(room_df['CO2 Lower(%)'].iloc[i_t] + room_df['CO2 Lower(%)'].iloc[i_t+1])
                    CO = 0.5*(room_df['CO Lower (ppm)'].iloc[i_t] + room_df['CO Lower (ppm)'].iloc[i_t+1])
                    O2 = 0.5*(room_df['O2 Lower (%)'].iloc[i_t] + room_df['O2 Lower (%)'].iloc[i_t+1])
                else: # monitoring height is in upper layer
                    CO2 = 0.5*(room_df['CO2 Upper(%)'].iloc[i_t] + room_df['CO2 Upper(%)'].iloc[i_t+1])
                    CO = 0.5*(room_df['CO Upper (ppm)'].iloc[i_t] + room_df['CO Upper (ppm)'].iloc[i_t+1])
                    O2 = 0.5*(room_df['O2 Upper (%)'].iloc[i_t] + room_df['O2 Upper (%)'].iloc[i_t+1])

                if CO2 > 0.02:
                    f = math.exp(CO2/5)
                else:
                    f = 1

                increment_FED_co = CO*(room_df['Time (sec)'].iloc[i_t+1]/60 - room_df['Time (sec)'].iloc[i_t]/60)*f/35000

                increment_FED_O2 = 0
                if O2 < 13: # include hypoxic effects if O2 concentration less than 13%
                    increment_FED_O2 = (room_df['Time (sec)'].iloc[i_t+1]/60 - room_df['Time (sec)'].iloc[i_t]/60) / math.exp(8.13-0.54*(20.9-O2))
                    
                new_FED_CO = FED_CO[-1] + increment_FED_co + increment_FED_O2
                if new_FED_CO > 1:
                    new_FED_CO = 1

                FED_CO.append(new_FED_CO)
                _time = room_df['Time (sec)'].iloc[i_t+1]
                times.append(_time)

        # Print FED exceeded time
        _t = np.interp(FED_threshold, FED_CO, times, right=np.nan, left=np.nan)
        _prefix = ' - '.join([f'{rooms[i]} ({transition_times[i]}-{transition_times[i+1]}s)' for i in range(len(rooms))])
        if np.isnan(_t):
            print(f'{_prefix}: Max FED_CO was {max(FED_CO):.3f}')
        else:
            print(f'{_prefix}: FED_CO exceeds {FED_threshold:.2f} at {int(_t)} s')

        return times, FED_CO


    def plot_room_FED_thermal(self, rooms=None, monitoring_height=2, FED_threshold=0.3):
        """
        Plot the FED_thermal for the rooms.

        Args:
            rooms (list(str), optional): List of rooms.
            monitoring_height (int, optional): Height (m) above floor of room to calculate FED at. Defaults to 2.
            FED_threshold (float, optional): Threshold to mark with horizontal line. Defaults to 0.3.
        """        
        if rooms is None: rooms = self.get_rooms()
        fig, ax = plt.subplots()
        for r in rooms:
            _times, _room_FED_thermal = self.calculate_FED_thermal_path([r], [], monitoring_height=monitoring_height)
            ax.plot(_times, _room_FED_thermal, label=r)
        ax.legend()
        bplot.add_tenability_hline(ax, FED_threshold)
        self.format_plot(ax, ylabel='FED_thermal')
        self.add_smoke_detector_lines(ax)
        return fig, ax

 
    def plot_FED_thermal_path(self, rooms, transition_times, monitoring_height=2, FED_threshold=0.3):
        """
        Plot the FED_thermal along the egress path given by the list of rooms and the transition times.
        If the last transition time is omitted, FED is plotted until the end of the simulation.
        FED_thermal is calculated according to the C/VM2 formula.
        FED calculation starts from time zero. Emissivity of the upper layer is taken as 1.


        Args:
            rooms (list(str)): List of rooms.
            transition_times (list(int)): List of times at which movement between rooms occurs. Last number is optional.
            monitoring_height (int, optional): Height (m) above floor of room to calculate FED at. Defaults to 2.
            FED_threshold (float, optional): Threshold to mark with horizontal line. Defaults to 0.3.
        """
        fig, ax = plt.subplots()
        time, fed = self.calculate_FED_thermal_path(rooms, transition_times, monitoring_height, FED_threshold=FED_threshold)
        ax.plot(time, fed, label='egress path')
        ax.legend()
        bplot.add_tenability_hline(ax, FED_threshold)
        self.format_plot(ax, ylabel='FED_thermal')
        self.add_spk_lines(ax)
        self.add_smoke_detector_lines(ax)
        # add vertical lines and annotations at top of graph
        transition_times = [0] + transition_times
        if len(transition_times) == len(rooms)-1:
            transition_times.append(self.data[rooms[0]]['Time (sec)'].max())
        for i in range(len(rooms)):
            bplot.add_span_text(ax, transition_times[i], transition_times[i+1], rooms[i])
            bplot.add_user_vline(ax, transition_times[i+1])
        return fig, ax


    def calculate_FED_thermal_path(self, rooms, transition_times, monitoring_height=2, FED_threshold=0.3):
        """
        Calculate the FED_thermal along the egress path given by the list of rooms and the transition times.
        If the last transition time is omitted, FED is calculated until the end of the simulation.
        FED_CO is calculated according to the C/VM2 formula.
        FED calculation starts from time zero. Emissivity of the upper layer is taken as 1.

        Args:
            rooms (list(str)): List of rooms.
            transition_times (list(int)): List of times at which movement between rooms occurs. Last number is optional.
            monitoring_height (int, optional): Height (m) above floor of room to calculate FED at. Defaults to 2.
            FED_threshold (float, optional): Threshold to mark with horizontal line. Defaults to 0.3.

        Returns:
            times, FED_CO: List of time-FED data points.
        """
        if len(rooms) - len(transition_times) not in [0, 1]:
            raise Exception('Invalid combination of rooms and transition_times')

        if len(transition_times) == len(rooms)-1:
            # FED measured in final room until end of data
            transition_times.append(self.data[rooms[0]]['Time (sec)'].max())

        # prepend 0 to transition times, because transition times will be used to slivce data
        transition_times = [0] + transition_times

        times = [0]
        FED_thermal = [0]

        # make list of times
        dfs = []
        for i_r in range(len(rooms)):

            room_df = self.data[rooms[i_r]]

            # check if data start and end slice times exist, if not add them iin via interpolation
            if not transition_times[i_r] in room_df['Time (sec)'].values:
                # add row and add by interpolation
                room_df = pd.concat([room_df, pd.DataFrame({'Time (sec)': [transition_times[i_r]]})])
                room_df = room_df.sort_values('Time (sec)').reindex().interpolate(limit_area='inside')
            if not transition_times[i_r+1] in room_df['Time (sec)'].values:
                # add row and add by interpolation
                room_df = pd.concat([room_df, pd.DataFrame({'Time (sec)': [transition_times[i_r+1]]})])
                room_df = room_df.sort_values('Time (sec)').reindex().interpolate(limit_area='inside')

            # Select data slice
            room_df = room_df[room_df['Time (sec)'].between(transition_times[i_r], transition_times[i_r+1])]

            for i_t in range(0, len(room_df['Time (sec)'])-1):
                # average species concentrations over timestep
                if 0.5*(room_df['Layer Height (m)'].iloc[i_t]+room_df['Layer Height (m)'].iloc[i_t+1]) > monitoring_height: # monitoring height is in lower layer
                    gas_temp = 0.5*(room_df['Lower Layer Temp (C)'].iloc[i_t]+room_df['Lower Layer Temp (C)'].iloc[i_t+1])
                    _layer_height = 0.5*(room_df['Layer Height (m)'].iloc[i_t]+room_df['Layer Height (m)'].iloc[i_t+1])
                    A = self.input_rooms_by_name[rooms[i_r]]['length'] / (2*(_layer_height - monitoring_height))
                    B = self.input_rooms_by_name[rooms[i_r]]['width'] / (2*(_layer_height - monitoring_height))
                    view_factor = (2/math.pi) * ((A/math.sqrt(1+A**2))*math.atan(B/math.sqrt(1+A**2)) + (B/math.sqrt(1+B**2))*math.atan(A/math.sqrt(1+B**2)))

                else: # monitoring height is in upper layer
                    gas_temp = 0.5*(room_df['Upper Layer Temp (C)'].iloc[i_t]+room_df['Upper Layer Temp (C)'].iloc[i_t+1])
                    view_factor = 1


                upper_layer_temperature = 0.5*(room_df['Upper Layer Temp (C)'].iloc[i_t]+room_df['Upper Layer Temp (C)'].iloc[i_t+1])
                # Upper layer is conservatively taken as 1.
                # Investigation shows that the emissivity of the upper layer becomes 1 within 60 seconds of a fast growth rate fire.
                upper_layer_emissivity = 1

                t_i_conv = (5*10**7) * gas_temp**-3.4
                if gas_temp < 25:
                    t_i_conv = 9e9 # set very large if temperature is below tolerability threshold of 25 deg C

                q = view_factor * upper_layer_emissivity * 5.67e-8 * (upper_layer_temperature+273)**4
                t_i_rad = 6.9*(q/1000)**-1.56 #/1000 is for W to kW
                if q < 2500:
                    t_i_rad = 9e9 # set very large if temperature is below tolerability threshold of 2.5 kW/m2

                increment_FED_thermal = (1/t_i_conv + 1/t_i_rad) * (room_df['Time (sec)'].iloc[i_t+1]/60 - room_df['Time (sec)'].iloc[i_t]/60)
                new_FED_thermal = FED_thermal[-1] + increment_FED_thermal
                if new_FED_thermal > 1:
                    new_FED_thermal = 1
                
                FED_thermal.append(new_FED_thermal)
                _time = room_df['Time (sec)'].iloc[i_t+1]
                times.append(_time)

        # Print FED exceeded time
        _t = np.interp(FED_threshold, FED_thermal, times, right=np.nan, left=np.nan)
        if np.isnan(_t):
            print(f'Max FED_thermal was {max(FED_thermal):.3f}')
        else:
            print(f'FED_thermal exceeds {FED_threshold:.2f} at {int(_t)} s')

        return times, FED_thermal


    def plot_room_FEDs(self, room_name, monitoring_height=2, FED_threshold=0.3):
        """
        Plot the FED_CO and FED_thermal for a room.

        Args:
            room_name (str): room name.
            monitoring_height (int, optional): Height (m) above floor of room to calculate FED at. Defaults to 2.
            FED_threshold (float, optional): Threshold to mark with horizontal line. Defaults to 0.3.
        """        
        fig, ax = plt.subplots()
        _times, _room_FED_thermal = self.calculate_FED_thermal_path([room_name], [], monitoring_height=monitoring_height, FED_threshold=FED_threshold)
        ax.plot(_times, _room_FED_thermal, label='FED_thermal')
        _times, _room_FED_CO = self.calculate_FED_CO_path([room_name], [], monitoring_height=monitoring_height, FED_threshold=FED_threshold)
        ax.plot(_times, _room_FED_CO, label='FED_CO')
        ax.legend()
        bplot.add_tenability_hline(ax, FED_threshold)
        self.format_plot(ax, ylabel='FED')
        self.add_smoke_detector_lines(ax)
        return fig, ax

