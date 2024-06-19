import math
import numpy as np
import param
import pandas as pd
import panel as pn

from table import Tablereport

class AbsoluteTablereport(Tablereport):
    algorithms = param.ListSelector()


    def __init__(self, **params):
        super().__init__(**params)

        self.param_view = pn.Column(
            pn.pane.HTML("Attributes", styles={'font-size': '10pt', 'font-family': 'Arial', 'padding-left': '10px'}),
            pn.widgets.CrossSelector.from_param(self.param.attributes, definition_order = False, width = 475, styles={'padding-left': '10px'}),
            pn.pane.HTML("Domains", styles={'font-size': '10pt', 'font-family': 'Arial', 'padding-left': '10px'}),
            pn.widgets.CrossSelector.from_param(self.param.domains, definition_order = False, width = 475, styles={'padding-left': '10px'}),
            pn.pane.HTML("Algorithms", styles={'font-size': '10pt', 'font-family': 'Arial', 'padding-left': '10px'}),
            pn.widgets.CrossSelector.from_param(self.param.algorithms, definition_order = False, width = 475, styles={'padding-left': '10px'}),
            pn.Param(self.param.precision),
            pn.pane.Markdown("""
                ### Information
                Data is organized by attribute, then domain, then problem.
                You can click on attributes/domains to unfold the next level,
                and reclick to fold again. Clicking on a concrete problem opens
                a ProblemReport comparing all attributes for this specific
                problem. Several popups can be open at the same time, but they
                will be removed when the ReportType is changed.

                Numeric values are aggregated over the set of instances where
                all selected algorithms have a value for the corresponding
                attribute. You can customize which aggregator to use with the
                dictionary "custom aggregators", for example `{"expansions" :
                "gmean"}`. Currently supported aggregators are "sum", "mean"
                and "gmean".

                Numeric values are also color-coded, with blue denoting a worse
                and green a better value. You can customize whether the smaller
                value is better or not with the dictionary "custom min wins",
                for example `{"expansions" : True}` means smaller is better.
                """),
            width=500
        )


    def set_experiment_data_dependent_parameters(self):
        param_updates = super().set_experiment_data_dependent_parameters()
        self.param.algorithms.objects = self.experiment_data.algorithms
        self.param.algorithms.default = self.experiment_data.algorithms
        param_updates["algorithms"] = self.experiment_data.algorithms
        return param_updates


    def compute_view_data(self):
        return self.table_data[["Index"] + self.algorithms]


    def get_current_columns(self):
        return self.algorithms


    def style_table_by_row(self, row):
        style = super().style_table_by_row(row)
        attribute = row.name[0]
        min_wins = self.experiment_data.attribute_info[attribute].min_wins

        if min_wins is None:
            return style

        numeric_values = pd.to_numeric(row,errors='coerce')
        min_val = numeric_values.dropna().min()
        max_val = numeric_values.dropna().max()
        if min_val == max_val:
            return style
        for i, val in enumerate(numeric_values):
            if not pd.isnull(val):
                percentage = (val - min_val) / (max_val-min_val)
                if min_wins:
                  percentage = 1-percentage
                green = (percentage*175).astype(int)
                blue = ((1-percentage)*255).astype(int)
                style[i] = style[i]+ "color: #00{:02x}{:02x};".format(green, blue)
        return style


    def param_view(self):
        return self.param_view


    def get_params_as_dict(self):
        params = super().get_params_as_dict()

        # shorten the algorithms parameter by using indices instead of the attribute names
        if "algorithms" in params:
            params["algorithms"] = [self.param.algorithms.objects.index(a) for a in params["algorithms"]]
        return params


    def set_params_from_dict(self, params):
        super().set_params_from_dict(params)
        if "algorithms" in params:
            params["algorithms"] = [self.param.algorithms.objects[x] for x in params["algorithms"]]
        self.param.update(params) #TODO: currently we need to make sure that the child calls this, maybe redesign...
