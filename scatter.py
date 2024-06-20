from bokeh.plotting import figure
from bokeh.models import HoverTool, TapTool, Legend, LegendItem, Span
from functools import partial
import math
import numpy as np
import param
import pandas as pd
import holoviews as hv
import hvplot.pandas
import panel as pn

from experimentdata import ExperimentData
from problemtable import ProblemTablereport
from prpopupreport import PRPopupReport

hv.extension('bokeh')

MARKERS = ["x", "circle", "square", "triangle", "asterisk",
           "diamond", "cross", "star", "inverted_triangle", "plus",
           "hex", "y", "circle_cross", "square_cross", "diamond_cross",
           "circle_x", "square_x", "square_pin", "triangle_pin"]
COLORS = ["black", "red", "blue", "teal", "orange",
          "purple", "olive", "lime", "cyan"]

def get_num_true(df):
    vc = df.value_counts()
    if True not in vc.index:
        return 0
    else:
        return vc[True]


class Scatterplot(PRPopupReport):
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
    marker_size = param.Integer(default = 7, bounds = (2,50))
    marker_fill_alpha = param.Number(default = 0.0, bounds=(0.0,1.0))
    markers = param.List(default=MARKERS)
    colors = param.List(default=COLORS)


    def __init__(self, experiment_data = ExperimentData(), param_dict = dict(), **params):
        super().__init__(experiment_data, **params)

        self.data_view = figure()
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
            pn.Param(self.param.markers),
            pn.Param(self.param.colors),
            pn.pane.Markdown("""
                ### Information
                In entries list you can specify several combinations of
                algorithms that you want to compare against each other, one
                combination per row:

                - "alg1" will use alg1 on both the x and y axis,
                  and has legend entry "alg1"
                - "alg1 alg2" will use alg1 on the x and alg2 on the y axis,
                  and has legend entry "alg1 vs alg2"
                - "alg1 alg2 x" will use alg1 on the x and alg2 on the y axis,
                  and has legend entry "x"
                - "\*x\* \*y\*" will search for all algorithm pairs whose name
                  only differs in that the first algorithm contains "x" and the
                  second contains "y". For example "\*base\* \*v1\*" would allow
                  you to easily compare the base and v1 versions of all
                  algorithms.

                If "Autoscale" is deactivated, you can specify the x and y
                ranges of the plot yourself; otherwise it will be computed
                based on min/max values of the data points.

                For relative or log plots you can use "Replace zero" to replace
                all 0 values with the chosen number. Otherwise data points with
                a 0 will be dropped.

                Clicking on a datapoint will highlight this point and open a
                popup with a ProblemTablereport for the particular problem.
                Clicking anywhere else in the plot removes the highlight.
                Several popups can be open at the same time, but they will be
                removed when the ReportType is changed.
            """)

        )
        self.data_view_in_progress = False
        param_dict = self.set_experiment_data_dependent_parameters() | param_dict
        self.param.update(param_dict)


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
            if xalg[0] == xalg[-1] == yalg[0] == yalg[-1] == '*':
                x_substring = xalg[1:-1]
                y_substring = yalg[1:-1]
                for alg in self.experiment_data.algorithms:
                    if x_substring in alg:
                        for alg2 in self.experiment_data.algorithms:
                            if y_substring in alg2 and alg.replace(x_substring, "") == alg2.replace(y_substring, ""):
                                entries.append((alg, alg2, f"{alg} vs {alg2}"))
            invalid_algorithms = [alg for alg in [xalg,yalg] if alg not in self.experiment_data.algorithms]
            if not invalid_algorithms:
                entries.append((xalg,yalg,name))
        return entries


    def on_click_callback(self, attr, old, new, df):
        old_set = set(old) if old else set()
        new_set = set(new)
        change = list((old_set - new_set) | (new_set - old_set))
        if change:
            domain = df.iloc[change[0]]['domain']
            problem = df.iloc[change[0]]['problem']
            algorithms = df.iloc[change[0]]['algs']
            self.add_problem_report_popup(domain, problem, algorithms)


    def update_data_view(self):
        if self.data_view_in_progress:
            return
        algorithm_pairs = self.get_algorithm_pairs()
        if self.xattribute not in self.experiment_data.attributes or self.yattribute not in self.experiment_data.attributes or not algorithm_pairs:
            return

        self.data_view_in_progress = True

        # Build the DataFrame used in the plot.
        frames = []
        index_order = [self.groupby, 'domain' if self.groupby == 'name' else 'name', 'problem']
        for (xalg, yalg, name) in algorithm_pairs:
            xcol = self.experiment_data.data.loc[self.xattribute][xalg]
            ycol = self.experiment_data.data.loc[self.yattribute][yalg]
            algs = [xalg] if xalg == yalg else [xalg, yalg]
            new_frame = pd.DataFrame({'x':xcol, 'y':ycol, 'yrel': ycol, 'name':name, 'algs': [algs]*len(xcol)}).reset_index().set_index(index_order)
            frames.append(new_frame)
        overall_frame = pd.concat(frames)
        overall_frame.replace(0, self.replace_zero, inplace=True)
        overall_frame.sort_index(level=0, inplace=True)
        overall_frame['yrel'] = overall_frame.y.div(overall_frame.x)
        overall_frame.loc[~np.isfinite(overall_frame['yrel'].astype(float)), 'yrel'] = np.nan
        xcol = 'x'
        ycol = 'y' if not self.relative else 'yrel'

        if self.xscale == "log":
            overall_frame = overall_frame[~(overall_frame[xcol] <= 0)]
        if self.yscale == "log":
            overall_frame = overall_frame[~(overall_frame[ycol] <= 0)]

        if overall_frame.empty:
            self.data_view_in_progress = False
            return pn.pane.Markdown("All points have been dropped")

        # Define axis labels
        tmp = overall_frame.replace(np.nan, np.Infinity)
        num_x_lower = get_num_true(tmp['x'] < tmp['y'])
        num_y_lower = get_num_true(tmp['y'] < tmp['x'])
        x_failed_table = (tmp['x'] == np.Infinity)
        y_failed_table = (tmp['y'] == np.Infinity)
        num_x_failed = get_num_true(x_failed_table)
        num_y_failed = get_num_true(y_failed_table)
        num_x_failed_single = get_num_true(x_failed_table & ~y_failed_table)
        num_y_failed_single = get_num_true(y_failed_table & ~x_failed_table)
        xlabel = self.xattribute + f" (lower: {num_x_lower}, failed: {num_x_failed}, failed single: {num_x_failed_single})"
        ylabel = self.yattribute + f" (lower: {num_y_lower}, failed: {num_y_failed}, failed single: {num_y_failed_single})"

        # Compute min and max values.
        xmax = overall_frame[xcol].max()
        xmin = overall_frame[xcol].min()
        ymax = overall_frame[ycol].max()
        ymin = overall_frame[ycol].min()
        if (self.xattribute == self.yattribute and not self.relative):
            xmax = max(xmax, ymax)
            ymax = xmax
            xmin = min(xmin, ymin)
            ymin = xmin

        # Compute failed values.
        x_failed = int(10 ** math.ceil(math.log10(xmax))) if self.xscale == "log" else xmax*1.1
        y_failed = int(10 ** math.ceil(math.log10(ymax))) if self.yscale == "log" else ymax*1.1
        overall_frame[xcol].replace(np.nan,x_failed, inplace=True)
        overall_frame[ycol].replace(np.nan,y_failed, inplace=True)

        # Compute ranges if they are not specified.
        if self.autoscale:
            self.param.update({
              "x_range" : (xmin*0.9, x_failed*1.1),
              "y_range" : (ymin*0.9, y_failed*1.1)
            })

        indices = []
        if self.groupby == "name":
            indices = [name for _, _, name in algorithm_pairs]
        else:
            indices = list(set(overall_frame.index.get_level_values(0)))
            indices.sort()

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
            if (width > self.xsize):
                ncols -= 1
                break

        plot = figure(width=self.xsize, height=self.ysize + 23*math.ceil(len(indices)/ncols),
                      x_axis_label=xlabel, y_axis_label = ylabel,
                      x_axis_type = self.xscale, y_axis_type = self.yscale,
                      x_range = self.x_range, y_range = self.y_range)

        # helper lines
        plot.renderers.extend([Span(location=x_failed, dimension='height', line_color='red')])
        plot.renderers.extend([Span(location=y_failed, dimension='width', line_color='red')])
        min_point = min(self.x_range[0],self.y_range[0])
        max_point = max(self.x_range[1],self.y_range[1])
        plot.line(x=[min_point, max_point], y=[1,1] if self.relative else [min_point, max_point], color='black')

        legend_items = []
        for i, index in enumerate(indices):
            df = overall_frame.loc[[index]].reset_index()
            p = plot.scatter(x=xcol, y=ycol, source=df,
                line_color=self.colors[i%len(COLORS)], marker=self.markers[i%len(MARKERS)],
                fill_color=self.colors[i%len(COLORS)], fill_alpha=self.marker_fill_alpha,
                size=self.marker_size, muted_fill_alpha = min(0.1,self.marker_fill_alpha))
            p.data_source.selected.on_change('indices', partial(self.on_click_callback, df=df))
            legend_items.append(LegendItem(label=index, renderers = [plot.renderers[i+3]]))


        # legend
        legend = Legend(items = legend_items)
        legend.click_policy='mute'
        plot.add_layout(legend, 'below')
        plot.legend.ncols = ncols

        # hover info
        plot.add_tools(HoverTool(tooltips=[
            ('Domain', '@domain'),
            ('Problem', '@problem'),
            ('Name', '@name'),
            ('x', '@x'),
            ('y', '@y'),
            ('yrel', '@yrel'),
            ]))
        plot.add_tools(TapTool())

        self.data_view = plot
        self.data_view_in_progress = False


    def update_param_view(self):
        self.param_view[3] = pn.pane.Markdown(f"**Available Algorithms:**\n {self.available_algorithms}")


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
