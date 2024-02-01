#! /usr/bin/env python3

import math
import numpy as np
import param
import pandas as pd
import holoviews as hv
import hvplot.pandas
import panel as pn

# ~ from algorithm_selector import AlgorithmSelectorReplace, AlgorithmSelectorExplicit
from report import Report
from experimentdata import ExperimentData


hv.extension('bokeh')

MARKERS = ["x","circle", "square", "triangle", "asterisk", "diamond", "cross", "star", "inverted_triangle", "plus", "x", "hex", "y",
           "circle_cross", "square_cross", "diamond_cross",
           "circle_dot", "square_dot", "triangle_dot", "diamond_dot", "hex_dot", "star_dot",
           "circle_x", "square_x", "circle_y", "square_pin", "triangle_pin"]
COLORS = ["black", "red", "blue", "teal", "orange", "purple", "olive", "lime"]


class Scatterplot(Report):
    xattribute = param.Selector(default="--")
    yattribute = param.Selector(default="--")
    entries_list = param.String(default="")
    available_algorithms = param.String()
    relative = param.Boolean(default = False)
    groupby = param.Selector(default = "name", objects = ["name","domain"])
    xscale = param.Selector(default = "log", objects = ["log","linear"])
    yscale = param.Selector(default = "log", objects = ["log","linear"])
    autoscale = param.Boolean(default = True)
    x_range = param.Range(default=(0,0), precedence = -1)
    y_range = param.Range(default=(0,0), precedence = -1)
    replace_zero = param.Number(default = 0)
    xsize = param.Integer(default = 500)
    ysize = param.Integer(default = 500)
    marker_size = param.Integer(default = 75, bounds = (5,250))
    marker_fill_alpha = param.Number(default = 0.0, bounds=(0.0,1.0))
    
    
    def __init__(self, **params):
        super().__init__(**params)
        self.param_view = pn.Column(
            pn.Param(self.param.xattribute),
            pn.Param(self.param.yattribute),
            pn.widgets.TextAreaInput.from_param(self.param.entries_list, auto_grow = True),
            pn.pane.Markdown(""),
            pn.Param(self.param.relative),
            pn.Param(self.param.groupby),
            pn.Param(self.param.xscale),
            pn.Param(self.param.yscale),
            pn.Param(self.param.autoscale),
            pn.Param(self.param.x_range),
            pn.Param(self.param.y_range),
            pn.Param(self.param.replace_zero),
            pn.Param(self.param.xsize),
            pn.Param(self.param.ysize),
            pn.Param(self.param.marker_size),
            pn.Param(self.param.marker_fill_alpha),
            pn.pane.Markdown("""
                ### Information
                In entries list you can specify several combinations of algorithms 
                that you want to compare against each other, one combination per row:
                
                - "alg1" will use alg1 on both the x and y axis, 
                  and has legend entry "alg1"
                - "alg1 alg2" will use alg1 on the x and alg2 on the y axis, 
                  and has legend entry "alg1 vs alg2"
                - "alg1 alg2 x" will use alg1 on the x and alg2 on the y axis, 
                  and has legend entry "x"
                
                If "Autoscale" is deactivated, you can specify the x and y ranges 
                of the plot yourself; otherwise it will be computed based on
                min/max values of the data points.
                
                For relative or log plots you can use "Replace zero" to replace 
                all 0 values with the chosen number. Otherwise data points with 
                a 0 will be dropped.
            """)
            
        )
        self.data_view_in_progress = False


    def set_experiment_data_dependent_parameters(self):
        param_updates = super().set_experiment_data_dependent_parameters()
        self.param.xattribute.objects = ["--", *self.experiment_data.numeric_attributes]
        param_updates["xattribute"] = "--"
        self.param.yattribute.objects = ["--", *self.experiment_data.numeric_attributes]
        param_updates["yattribute"] = "--"
        param_updates["available_algorithms"] =  "{}".format("\n".join(self.experiment_data.algorithms))
        return param_updates


    @param.depends('autoscale', watch=True)
    def set_scale_restrictions(self):
        value = -1 if self.autoscale else None
        self.param.x_range.precedence = value
        self.param.y_range.precedence = value


    def get_algorithm_pairs(self):
        entries = []
        for line in self.entries_list.splitlines():
            xalg = yalg = name = ""
            new_entry = tuple(str.split(line))
            if len(new_entry) == 3:
                xalg,yalg,name = new_entry
            elif len(new_entry) == 2:
                xalg,yalg = new_entry
                name = f"{xalg} vs {yalg}"
            elif len(new_entry) == 1:
                xalg = yalg = name = new_entry[0]
            else:
                continue
            invalid_algorithms = [alg for alg in [xalg,yalg] if alg not in self.experiment_data.algorithms]
            if not invalid_algorithms:
                entries.append((xalg,yalg,name))
        return entries


    def data_view(self):
        if self.data_view_in_progress:
            return
        algorithm_pairs = self.get_algorithm_pairs()
        if self.xattribute not in self.experiment_data.attributes or self.yattribute not in self.experiment_data.attributes or not algorithm_pairs:
            return

        self.data_view_in_progress = True
        logx = True if self.xscale == "log" else False
        logy = True if self.yscale == "log" else False
        xlabel = self.xattribute
        ylabel = self.yattribute

        # Build the DataFrame used in the plot.
        frames = []
        # TODO: this was a try to speed up the groupby part of hvplot, but it did not work
        index_order = [self.groupby, 'domain' if self.groupby == 'name' else 'name', 'problem']
        for (xalg, yalg, name) in algorithm_pairs:
            xcol = self.experiment_data.data.loc[self.xattribute][xalg]
            ycol = self.experiment_data.data.loc[self.yattribute][yalg]
            new_frame = pd.DataFrame({'x':xcol, 'y':ycol, 'name':name}).reset_index().set_index(index_order)
            frames.append(new_frame)
        overall_frame = pd.concat(frames).dropna(how='all')
        overall_frame.replace(0, self.replace_zero, inplace=True)
        overall_frame.sort_index(level=0, inplace=True)

        if self.relative:
            overall_frame = overall_frame[overall_frame['x'] != 0]
            overall_frame['y'] = overall_frame['y']/overall_frame['x']
        if self.xscale == "log":
            overall_frame = overall_frame[overall_frame['x'] > 0]
        if self.yscale == "log":
            overall_frame = overall_frame[overall_frame['y'] > 0]

        if overall_frame.empty:
            self.data_view_in_progress = False
            return pn.pane.Markdown("All points have been dropped")

        # Compute min and max values.
        xmax = overall_frame['x'].max()
        xmin = overall_frame['x'].min()
        ymax = overall_frame['y'].max()
        ymin = overall_frame['y'].min()

        # Compute failed values.
        x_failed = int(10 ** math.ceil(math.log10(xmax))) if self.xscale == "log" else xmax*1.1
        y_failed = int(10 ** math.ceil(math.log10(ymax))) if self.yscale == "log" else ymax*1.1
        overall_frame['x'].replace(np.nan,x_failed, inplace=True)
        overall_frame['y'].replace(np.nan,y_failed, inplace=True)
        
        # Compute ranges if they are not specified.
        if self.autoscale:
            self.param.update({
              "x_range" : (xmin*0.9, x_failed*1.1),
              "y_range" : (ymin*0.9, y_failed*1.1)
            })
        
        # Build the plot.
        plot = overall_frame.hvplot.scatter(x='x', y='y',
                xlabel=xlabel, ylabel=ylabel, logx=logx, logy=logy, 
                frame_width = self.xsize, frame_height = self.ysize, by=self.groupby,
                hover_cols=['domain', 'problem', 'name'],
                marker=MARKERS, fill_color=COLORS, line_color=COLORS,
                fill_alpha=self.marker_fill_alpha, size=self.marker_size)
        plot.opts(legend_position='right')
        plot.opts(xlim=(self.x_range))
        plot.opts(ylim=(self.y_range))

        # Create helper lines for failed values and equality.
        helper_plots = hv.HLine(y_failed).opts(color="red", line_width=1)*hv.VLine(x_failed).opts(color="red", line_width=1)
        if self.relative:
            helper_plots = helper_plots * hv.HLine(1).opts(color="black", line_width=1)
        else:
            helper_plots = helper_plots * hv.Slope(slope=1, y_intercept=0).opts(color="black", line_width=1)

        overall_plot = plot * helper_plots
        # overall_plot.opts(shared_axes=False) TODO: I don't think I need this?

        self.data_view_in_progress = False
        return overall_plot

    # TODO: figure out if we can do without the watcher, it causes unnecessary output
    @param.depends('available_algorithms', watch=True)
    def param_view(self):
        self.param_view[3] = pn.pane.Markdown(f"**Available Algorithms:**\n {self.available_algorithms}")
        return self.param_view


    def get_params_as_dict(self):
        d = super().get_params_as_dict()
        if "autoscale" not in d: # if it's not in the dict it is on its default value (True)
            if "x_range" in d:
                d.pop("x_range")
            if "y_range" in d:
                d.pop("y_range")
        if "available_algorithms" in d:
            d.pop("available_algorithms")
        return d


    def set_params_from_dict(self, params):
        if "x_range" in params:
            params["x_range"] = tuple(params["x_range"])
        if "y_range" in params:
            params["y_range"] = tuple(params["y_range"])
        self.param.update(params) #TODO: currently we need to make sure that the child calls this, maybe redesign...
