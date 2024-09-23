from bokeh.plotting import figure
from bokeh.models import HoverTool, TapTool, Legend, LegendItem, Span
import math
import numpy as np
import param
import pandas as pd
import holoviews as hv
import hvplot.pandas
import panel as pn

from experimentdata import ExperimentData
from report import Report

hv.extension('bokeh')

COLORS = ["black", "red", "blue", "teal", "orange",
          "purple", "olive", "lime", "cyan"]


class Cactusplot(Report):
    attribute = param.Selector(default="--")
    algorithms = param.ListSelector()
    x_scale = param.Selector(default = "log", objects = ["log","linear"])
    y_scale = param.Selector(default = "linear", objects = ["log","linear"])
    autoscale = param.Boolean(default = True)
    x_range = param.Range(default=(0,0), precedence = -1)
    y_range = param.Range(default=(0,0), precedence = -1)
    replace_zero = param.Number(default = 0,
        doc = "Replace all 0 values with the chosen number. Afterwards, all 0 values will be dropped.")
    x_size = param.Integer(default = 500)
    y_size = param.Integer(default = 500)
    colors = param.List(default=COLORS)


    def __init__(self, experiment_data = ExperimentData(), param_dict = dict(), **params):
        super().__init__(experiment_data, **params)

        self.data_view = figure()
        self.param_view = pn.Column(
            pn.Param(self.param.attribute),
            pn.pane.HTML("Algorithms", styles={'font-size': '10pt', 'font-family': 'Arial', 'padding-left': '10px'}),
            pn.widgets.CrossSelector.from_param(self.param.algorithms, definition_order = False, width = 475, styles={'padding-left': '10px'}),
            pn.Param(self.param.x_scale),
            pn.Param(self.param.y_scale),
            pn.Param(self.param.autoscale),
            pn.Param(self.param.x_range),
            pn.Param(self.param.y_range),
            pn.Param(self.param.replace_zero),
            pn.Param(self.param.x_size),
            pn.Param(self.param.y_size),
            pn.Param(self.param.colors),
            pn.pane.Markdown("""
                ### Information
                TODO
            """)

        )
        self.data_view_in_progress = False
        param_dict = self.set_experiment_data_dependent_parameters() | param_dict
        self.param.update(param_dict)


    def set_experiment_data_dependent_parameters(self):
        param_updates = super().set_experiment_data_dependent_parameters()
        self.param.attribute.objects = ["--", *self.experiment_data.numeric_attributes]
        param_updates["attribute"] = "--"
        self.param.algorithms.objects = self.experiment_data.algorithms
        self.param.algorithms.default = self.experiment_data.algorithms
        param_updates["algorithms"] = self.experiment_data.algorithms
        return param_updates


    def update_algorithm_names(self, mapping):
        self.param.algorithms.objects = self.experiment_data.algorithms
        self.algorithms = [mapping[x] for x in self.algorithms]


    @param.depends('autoscale', watch=True)
    def set_scale_restrictions(self):
        value = -1 if self.autoscale else None
        self.param.x_range.precedence = value
        self.param.y_range.precedence = value


    def update_data_view(self):
        if self.data_view_in_progress:
            return
        if self.attribute not in self.experiment_data.attributes or len(self.algorithms) == 0:
            return

        self.data_view_in_progress = True

        # Build the DataFrame used in the plot.
        frames = []
        max_values = {}
        for alg in self.algorithms:
            xcol = np.sort(self.experiment_data.data.loc[self.attribute][alg].dropna())
            max_values[alg] = len(xcol)
            ycol = np.array(range(1,len(xcol)+1))
            new_frame = pd.DataFrame({'x':xcol, 'y':ycol, 'name':alg})
            frames.append(new_frame)
        overall_frame = pd.concat(frames)
        overall_frame.replace(0, self.replace_zero, inplace=True)

        if self.x_scale == "log":
            overall_frame = overall_frame[~(overall_frame['x'] <= 0)]
        if self.y_scale == "log":
            overall_frame = overall_frame[~(overall_frame['y'] <= 0)]

        if overall_frame.empty or pd.isnull(overall_frame['x']).all() or pd.isnull(overall_frame['y']).all():
            self.data_view = pn.pane.Markdown("All points have been dropped")
            self.data_view_in_progress = False
            return

        # Define axis labels
        xlabel = self.attribute
        ylabel = "amount"

        # Compute min and max values.
        xmax = overall_frame['x'].max()
        xmin = overall_frame['x'].min()
        ymax = overall_frame['y'].max()
        ymin = overall_frame['y'].min()

        for alg in self.algorithms:
            overall_frame.loc[len(overall_frame)] = [xmax, max_values[alg], alg]
        overall_frame.set_index("name", inplace=True)

        # Compute ranges if they are not specified.
        if self.autoscale:
            self.param.update({
              "x_range" : (xmin*0.9, xmax*1.1),
              "y_range" : (ymin*0.9, ymax*1.1)
            })

        indices = self.algorithms

        # compute appropriate number of columns and height of legend
        indices_length = [len(i) for i in indices]
        ncols = 1
        for i in range(len(indices)):
            ncols += 1
            nrows = math.ceil(len(indices)/ncols)
            if (nrows*(ncols-1) >= len(indices)): #no rows gained
                continue
            max_num_chars_per_column = [max(indices_length[x*nrows:min((x+1)*nrows, len(indices))]) for x in range(ncols)]
            width = sum([7*x+20 for x in max_num_chars_per_column])+20
            if (width > self.x_size):
                ncols -= 1
                break

        plot = figure(width=self.x_size, height=self.y_size + 23*math.ceil(len(indices)/ncols),
                      x_axis_label=xlabel, y_axis_label = ylabel,
                      x_axis_type = self.x_scale, y_axis_type = self.y_scale,
                      x_range = self.x_range, y_range = self.y_range)


        legend_items = []
        for i, index in enumerate(indices):
            df = overall_frame.loc[[index]]
            p = plot.step(x='x', y='y', source=df,
                line_color=self.colors[i%len(COLORS)])
            legend_items.append(LegendItem(label=index, renderers = [plot.renderers[i]]))


        # legend
        legend = Legend(items = legend_items)
        legend.click_policy='mute'
        plot.add_layout(legend, 'below')
        plot.legend.ncols = ncols

        # hover info - not working at the moment
        # ~ plot.add_tools(HoverTool(tooltips=[
            # ~ ('x', '@x'),
            # ~ ('y', '@y'),
            # ~ ]))

        self.data_view = pn.Column(plot, sizing_mode="fixed", scroll=True)
        self.data_view_in_progress = False


    def get_params_as_dict(self):
        d = super().get_params_as_dict()
        if "autoscale" not in d: # if it's not in the dict it is on its default value (True)
            if "x_range" in d:
                d.pop("x_range")
            if "y_range" in d:
                d.pop("y_range")
        return d


    def set_params_from_dict(self, params):
        if "x_range" in params:
            params["x_range"] = tuple(params["x_range"])
        if "y_range" in params:
            params["y_range"] = tuple(params["y_range"])
        self.param.update(params) #TODO: currently we need to make sure that the child calls this, maybe redesign...
