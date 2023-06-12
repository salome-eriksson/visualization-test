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
    xmin = param.Number(default = 0, precedence=-1)
    ymin = param.Number(default = 0, precedence=-1)
    xmax = param.Number(default = 0, precedence=-1)
    ymax = param.Number(default = 0, precedence=-1)
    algorithm_selector = param.Selector()
    
    def __init__(self, **params):
        # ~ print("Scatterplot init")
        algorithm_pairs = params.pop('algorithm_pairs', [])
        xalg = params.pop('xalg_string', "")
        yalg = params.pop('yalg_string', "")
        super().__init__(**params)
        
        algorithm_selector_pos = -1
        if algorithm_pairs != []:
            algorithm_selector_pos = 1
        if xalg != "":
            algorithm_selector_pos = 0
        algorithm_selector_pos = max(0,algorithm_selector_pos)
        algorithm_selectors = [
          AlgorithmSelectorReplace(
            self.experiment_data.algorithms, xalg = xalg, yalg = yalg,
            name="select algorithm pairs based on replacing a substring"
          ),
          AlgorithmSelectorExplicit(
            self.experiment_data.algorithms, algorithm_pairs,
            name="select algorithm pairs explicitly"
          )
        ]
        self.param.algorithm_selector.objects = algorithm_selectors
        self.algorithm_selector = algorithm_selectors[algorithm_selector_pos]
        self.set_experiment_data_dependent_parameters()
        # ~ print("Scatterplot init end")
        
    def set_experiment_data_dependent_parameters(self):
        # ~ print("Scatterplot set experiment data dependent parameters")
        self.param.xattribute.objects = self.experiment_data.numeric_attributes
        self.xattribute = self.experiment_data.numeric_attributes[0]
        self.param.yattribute.objects = self.experiment_data.numeric_attributes
        self.yattribute = self.experiment_data.numeric_attributes[0]
        for algorithm_selector in self.param.algorithm_selector.objects:
            algorithm_selector.update_algorithms(self.experiment_data.algorithms)
        # ~ print("Scatterplot set experiment data dependent parameters end")

    @param.depends('autoscale', watch=True)
    def set_scale_restrictions(self):
        if self.autoscale:
            self.param.xmin.precedence=-1
            self.param.ymin.precedence=-1
            self.param.xmax.precedence=-1
            self.param.ymax.precedence=-1
        else:
            self.param.xmin.precedence=None
            self.param.ymin.precedence=None
            self.param.xmax.precedence=None
            self.param.ymax.precedence=None
      

    @param.depends('algorithm_selector', 'algorithm_selector.algorithm_pairs', 'xattribute', 'yattribute', 'relative',
    'xscale', 'yscale', 'groupby', 'fill_alpha', 'marker_size', 'xsize', 'ysize', 'replace_zero', 'autoscale',
    'xmin', 'xmax', 'ymin', 'ymax')
    def data_view(self):
        # ~ print("Scatterplot data view")
        logx = True if self.xscale == "log" else False
        logy = True if self.yscale == "log" else False
        xlabel = self.xattribute
        ylabel = self.yattribute
        

        overall_frame = pd.DataFrame(columns=['name', 'domain', 'problem','x', 'y'])
        overall_frame.set_index(['name','domain','problem'])
        data = self.experiment_data.data
        for (xalg, yalg, name) in self.algorithm_selector.algorithm_pairs:
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
        if self.autoscale:
            self.xmax = overall_frame['x'].max() if overall_frame['x'].max() is not np.nan else 1
            self.xmin = overall_frame['x'].min() if overall_frame['x'].min() is not np.nan else 0.00001
            self.ymax = overall_frame['y'].max() if overall_frame['y'].max() is not np.nan else 1
            self.ymin = overall_frame['y'].min() if overall_frame['y'].min() is not np.nan else 0.00001
            if self.xscale == "log" and self.xmax <= 0:
                self.xmax = 0.0001
            if self.xscale == "log" and self.xmin <= 0:
                self.xmin = self.xmax/10.0
            if self.yscale == "log" and self.ymax <= 0:
                self.ymax = 0.0001
            if self.yscale == "log" and self.ymin <= 0:
                self.ymin = self.ymax/10.0


        # ~ print("computing failed values")
        x_failed = int(10 ** math.ceil(math.log10(self.xmax))) if self.xscale == "log" else self.xmax*1.1
        y_failed = int(10 ** math.ceil(math.log10(self.ymax))) if self.yscale == "log" else self.ymax*1.1
        overall_frame['x'] = overall_frame['x'].replace(np.nan,x_failed)
        overall_frame['y'] = overall_frame['y'].replace(np.nan,y_failed)
        # ~ print("Building plot")
        plot = overall_frame.hvplot.scatter(x='x', y='y',
                xlabel=xlabel, ylabel=ylabel, logx=logx, logy=logy, 
                frame_width = self.xsize, frame_height = self.ysize, by=self.groupby,
                hover_cols=['domain', 'problem'],
                marker=MARKERS, fill_color=COLORS, line_color=COLORS,
                fill_alpha=self.fill_alpha, size=self.marker_size)
        plot.opts(legend_position='right')
        plot.opts(xlim=(self.xmin*0.9, x_failed*1.1))
        plot.opts(ylim=(self.ymin*0.9, y_failed*1.1))
        max_overall = max(x_failed,y_failed)

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

    @param.depends('algorithm_selector')
    def param_view(self):
        # ~ print("Scatterplot param view")
        retcol = pn.Column(pn.Param(self.param, name="Scatterplot", expand_button=False), self.algorithm_selector.param_view)
        # ~ print("Scatterplot param view return")
        return retcol
