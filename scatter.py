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
    algorithm_selector = param.Selector()
    
    def __init__(self, experiment_data, **params):
        super().__init__(experiment_data, **params)
        algorithm_selectors = []
        xalg = params['xalg_string'] if 'xalg_string' in params else ""
        yalg = params['yalg_string'] if 'yalg_string' in params else ""
        algorithm_pairs = params['algorithm_pairs'] if 'algorithm_pairs' in params else dict()
        algorithm_selectors = [
          AlgorithmSelectorReplace(
            experiment_data.algorithms, xalg = xalg, yalg = yalg,
            name="select algorithm pairs based on replacing a substring"
          ),
          AlgorithmSelectorExplicit(
            experiment_data.algorithms, algorithm_pairs,
            name="select algorithm pairs explicitly"
          )
        ]
        # ~ algorithm_selectors =[
          # ~ AlgorithmSelectorReplace(experiment_data.algorithms, name="select algorithm pairs based on replacing a substring"),
          # ~ AlgorithmSelectorExplicit(experiment_data.algorithms, name="select algorithm pairs explicitly")
        # ~ ]
        self.param.algorithm_selector.objects = algorithm_selectors
        self.algorithm_selector = algorithm_selectors[0]
        self.set_experiment_data_dependent_parameters()
        
    def update_experiment_data(self, experiment_data):
        super().update_experiment_data(experiment_data)
        self.set_experiment_data_dependent_parameters()
        
    def set_experiment_data_dependent_parameters(self):
        self.param.xattribute.objects = self.experiment_data.numeric_attributes
        self.param.yattribute.objects = self.experiment_data.numeric_attributes
        for algorithm_selector in self.param.algorithm_selector.objects:
            algorithm_selector.update_algorithms(self.experiment_data.algorithms)

    @param.depends('algorithm_selector', 'algorithm_selector.config_pairs', 'xattribute', 'yattribute', 'relative', 'xscale', 'yscale', 'groupby', 'fill_alpha', 'marker_size', 'xsize', 'ysize')
    def data_view(self):
        logx = True if self.xscale == "log" else False
        logy = True if self.yscale == "log" else False
        xlabel = self.xattribute
        ylabel = self.yattribute
        

        overall_frame = pd.DataFrame(columns=['name', 'domain', 'problem','x', 'y'])
        overall_frame.set_index(['name','domain','problem'])
        data = self.experiment_data.data
        for name, (xalg, yalg) in self.algorithm_selector.config_pairs.items():
            xcolumn = "{}_{}".format(xalg, self.xattribute)
            ycolumn = "{}_{}".format(yalg, self.yattribute)
            if xcolumn not in data or ycolumn not in data:
                continue
            new_frame = pd.DataFrame({'x':data[xcolumn], 'y':data[ycolumn], 'name':name})
            new_frame.reset_index(inplace=True)
            new_frame.set_index(['name','domain','problem'])
            overall_frame = pd.concat([overall_frame,new_frame])
        overall_frame = overall_frame.dropna(how='all')
        if self.relative:
            overall_frame['y'] = overall_frame['y']/overall_frame['x']

        x_max = overall_frame['x'].max() if overall_frame['x'].max() is not np.nan else 1
        x_min = overall_frame['x'].min() if overall_frame['x'].min() is not np.nan else 0.00001
        y_max = overall_frame['y'].max() if overall_frame['y'].max() is not np.nan else 1
        y_min = overall_frame['y'].min() if overall_frame['y'].min() is not np.nan else 0.00001
        if self.xscale == "log" and x_max <= 0:
            x_max = 0.0001
        if self.xscale == "log" and x_min <= 0:
            x_min = x_max/10.0
        if self.yscale == "log" and y_max <= 0:
            y_max = 0.0001
        if self.yscale == "log" and y_min <= 0:
            y_min = y_max/10.0
        
        x_failed = int(10 ** math.ceil(math.log10(x_max))) if self.xscale == "log" else x_max*1.1
        y_failed = int(10 ** math.ceil(math.log10(y_max))) if self.yscale == "log" else y_max*1.1
        overall_frame['x'] = overall_frame['x'].replace(np.nan,x_failed)
        overall_frame['y'] = overall_frame['y'].replace(np.nan,y_failed)
        plot = overall_frame.hvplot.scatter(x='x', y='y',
                xlabel=xlabel, ylabel=ylabel, logx=logx, logy=logy, 
                frame_width = self.xsize, frame_height = self.ysize, by=self.groupby,
                hover_cols=['domain', 'problem'],
                marker=MARKERS, fill_color=COLORS, line_color=COLORS,
                fill_alpha=self.fill_alpha, size=self.marker_size)
        plot.opts(legend_position='right')
        plot.opts(xlim=(x_min*0.9, x_failed*1.1))
        plot.opts(ylim=(y_min*0.9, y_failed*1.1))
        max_overall = max(x_failed,y_failed)

        helper_plots = hv.HLine(y_failed).opts(color="red", line_width=1)*hv.VLine(x_failed).opts(color="red", line_width=1)
        if self.relative:
            helper_plots = helper_plots * hv.HLine(1).opts(color="black", line_width=1)
        else:
            helper_plots = helper_plots * hv.Slope(slope=1, y_intercept=0).opts(color="black", line_width=1)

        overall_plot = plot * helper_plots
        overall_plot.opts(shared_axes=False)
        return overall_plot


    def param_view(self):
        return pn.Column(pn.Param(self.param, name="Scatterplot", expand_button=False), self.algorithm_selector.param_view)
