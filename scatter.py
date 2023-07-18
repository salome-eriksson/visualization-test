#! /usr/bin/env python3

import math
import numpy as np
import param
import pandas as pd
import holoviews as hv
import hvplot.pandas
import panel as pn

from algorithm_selector import AlgorithmSelectorReplace, AlgorithmSelectorExplicit
from report import Report
from experimentdata import ExperimentData


hv.extension('bokeh')

MARKERS = ["circle", "square", "triangle", "asterisk", "diamond", "cross", "star", "inverted_triangle", "plus", "x", "hex", "y",
           "circle_cross", "square_cross", "diamond_cross",
           "circle_dot", "square_dot", "triangle_dot", "diamond_dot", "hex_dot", "star_dot",
           "circle_x", "square_x", "circle_y", "square_pin", "triangle_pin"]
COLORS = ["black", "red", "blue", "teal", "orange", "purple", "olive", "lime"]

class Scatterplot(Report):
    xattribute = param.Selector()
    yattribute = param.Selector()
    relative = param.Boolean(default = False)
    xscale = param.Selector(default = "log", objects = ["log","linear"])
    yscale = param.Selector(default = "log", objects = ["log","linear"])
    groupby = param.Selector(default = "name", objects = ["name","domain"])
    fill_alpha = param.Number(default = 0.0, bounds=(0.0,1.0))
    marker_size = param.Integer(default = 75, bounds = (5,250))
    xsize = param.Integer(default = 500)
    ysize = param.Integer(default = 500)
    replace_zero = param.Number(default = 0)
    autoscale = param.Boolean(default = True)
    x_range = param.Range((0,0), precedence = -1)
    y_range = param.Range((0,0), precedence = -1)
    entries_selection_mode = param.Selector(default = "explicit", objects = ["explicit", "indicate versions by substring"])
    x_entries_substring = param.String(default = "", precedence = -1)
    y_entries_substring = param.String(default = "", precedence = -1)
    entries_list = param.String(default = "")

    
    def __init__(self, **params):
        # ~ print("Scatterplot init")
        algorithm_pairs = params.pop('algorithm_pairs', [])
        xalg = params.pop('xalg_string', "")
        yalg = params.pop('yalg_string', "")
        super().__init__(**params)
        self.set_experiment_data_dependent_parameters()
        # ~ print("Scatterplot init end")
        
    def set_experiment_data_dependent_parameters(self):
        # ~ print("Scatterplot set experiment data dependent parameters")
        self.param.xattribute.objects = self.experiment_data.numeric_attributes
        self.xattribute = self.experiment_data.numeric_attributes[0]
        self.param.yattribute.objects = self.experiment_data.numeric_attributes
        self.yattribute = self.experiment_data.numeric_attributes[0]
        # ~ print("Scatterplot set experiment data dependent parameters end")

    @param.depends('autoscale', watch=True)
    def set_scale_layout(self):
        if self.autoscale:
            self.param.x_range.precedence = -1
            self.param.y_range.precedence = -1
        else:
            self.param.x_range.precedence = None
            self.param.y_range.precedence = None

    @param.depends('entries_selection_mode', watch=True)
    def set_entries_selection_layout(self):
        if self.entries_selection_mode == "explicit":
            self.param.entries_list.precedence = None
            self.param.x_entries_substring.precedence = -1
            self.param.y_entries_substring.precedence = -1
        else:
            self.param.entries_list.precedence = -1
            self.param.x_entries_substring.precedence = None
            self.param.y_entries_substring.precedence = None

    def get_entries(self):
        entries = []
        if self.entries_selection_mode == "explicit":
            for line in self.entries_list.splitlines():
                new_entry = tuple(str.split(line))
                if len(new_entry) != 3:
                    print("wrong formatting")
                    return []
                entries.append(new_entry)
                
        else:
            algorithms = self.experiment_data.algorithms
            if self.x_entries_substring == "" and self.y_entries_substring == "":
                entries = [(x,x,x) for x in algorithms]
            else:
                for alg1 in algorithms:
                    if self.x_entries_substring in alg1:
                        if self.y_entries_substring == "":
                            entries.append((alg1, alg1, alg1))
                        else:
                            alg2 = alg1.replace(self.x_entries_substring, self.y_entries_substring)
                            if alg2 in algorithms:
                                name = alg1.replace(self.x_entries_substring, "")
                                entries.append((alg1, alg2, name))
        return entries
            
      
    def data_view(self):
        # ~ print("Scatterplot data view")
        logx = True if self.xscale == "log" else False
        logy = True if self.yscale == "log" else False
        xlabel = self.xattribute
        ylabel = self.yattribute
        

        overall_frame = pd.DataFrame(columns=['name', 'domain', 'problem','x', 'y'])
        overall_frame.set_index(['name','domain','problem'])
        data = self.experiment_data.data
        entries = self.get_entries()
        for (xalg, yalg, name) in entries:
            # ~ print(f"Gathering point for {name}")
            xcolumn = "{}_{}".format(xalg, self.xattribute)
            ycolumn = "{}_{}".format(yalg, self.yattribute)
            if xcolumn not in data or ycolumn not in data:
                continue
            new_frame = pd.DataFrame({'x':data[xcolumn], 'y':data[ycolumn], 'name':name})
            new_frame.reset_index(inplace=True)
            new_frame.set_index(['name','domain','problem'])
            overall_frame = pd.concat([overall_frame,new_frame])
        overall_frame = overall_frame.dropna(how='all')

        overall_frame['x'].replace(0, self.replace_zero, inplace=True)
        overall_frame['y'].replace(0, self.replace_zero, inplace=True)

        # drop rows containing a 0 in x if the x scale is logarithmic or if we do a relative plot
        if self.xscale == "log" or self.relative:
            overall_frame = overall_frame[overall_frame['x'] != 0]
        # drop rows containing a 0 in y if the y scale is logarithmic
        if self.yscale == "log":
            overall_frame = overall_frame[overall_frame['y'] != 0]
        
        # ~ print("Checking if relative")
        if self.relative:
            overall_frame['y'] = overall_frame['y']/overall_frame['x']

        # ~ print("Computing min/max")
        xmax = overall_frame['x'].max() if overall_frame['x'].max() is not np.nan else 1 
        xmin = overall_frame['x'].min() if overall_frame['x'].min() is not np.nan else 0.00001
        ymax = overall_frame['y'].max() if overall_frame['y'].max() is not np.nan else 1
        ymin = overall_frame['y'].min() if overall_frame['y'].min() is not np.nan else 0.00001
        if self.xscale == "log" and xmax <= 0:
            xmax = 0.0001
        if self.xscale == "log" and xmin <= 0:
            xmin = self.xmax/10.0
        if self.yscale == "log" and ymax <= 0:
            ymax = 0.0001
        if self.yscale == "log" and ymin <= 0:
            ymin = self.ymax/10.0


        # ~ print("computing failed values")
        x_failed = int(10 ** math.ceil(math.log10(xmax))) if self.xscale == "log" else xmax*1.1
        y_failed = int(10 ** math.ceil(math.log10(ymax))) if self.yscale == "log" else ymax*1.1
        overall_frame['x'] = overall_frame['x'].replace(np.nan,x_failed)
        overall_frame['y'] = overall_frame['y'].replace(np.nan,y_failed)
        if self.autoscale:
            self.x_range = (xmin*0.9, x_failed*1.1)
            self.y_range = (ymin*0.9, y_failed*1.1)
        
        # ~ print("Building plot")
        plot = overall_frame.hvplot.scatter(x='x', y='y',
                xlabel=xlabel, ylabel=ylabel, logx=logx, logy=logy, 
                frame_width = self.xsize, frame_height = self.ysize, by=self.groupby,
                hover_cols=['domain', 'problem'],
                marker=MARKERS, fill_color=COLORS, line_color=COLORS,
                fill_alpha=self.fill_alpha, size=self.marker_size)
        plot.opts(legend_position='right')
        plot.opts(xlim=(self.x_range))
        plot.opts(ylim=(self.y_range))

        # ~ print("Creating helper plots")
        helper_plots = hv.HLine(y_failed).opts(color="red", line_width=1)*hv.VLine(x_failed).opts(color="red", line_width=1)
        if self.relative:
            helper_plots = helper_plots * hv.HLine(1).opts(color="black", line_width=1)
        else:
            helper_plots = helper_plots * hv.Slope(slope=1, y_intercept=0).opts(color="black", line_width=1)

        overall_plot = plot * helper_plots
        overall_plot.opts(shared_axes=False)
        # ~ print("Scatterplot data view end")
        return overall_plot

    @param.depends('autoscale', 'entries_selection_mode', 'properties_file')
    def param_view(self):
        css = "font-correction { font-size: 10pt; }"
        # ~ print("Scatterplot param view")
        explanation_string = "available algorithms:\n{}".format("\n".join(self.experiment_data.algorithms))
        ret = pn.Column(pn.Param(self.param, widgets = {'entries_list' : pn.widgets.TextAreaInput(name="Entries List")}),
                        pn.pane.Str(explanation_string)
                        )
        # ~ print("Scatterplot param view return")
        return ret

