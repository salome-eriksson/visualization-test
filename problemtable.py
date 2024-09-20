import param
import pandas as pd
import panel as pn

from experimentdata import ExperimentData
from report import Report

class ProblemTablereport(Report):
    domain = param.Selector(default="--")
    problem = param.Selector(default="--")
    algorithms = param.ListSelector()


    def __init__(self, experiment_data = ExperimentData(), param_dict = dict(), sizing_mode = "stretch_both", **params):
        super().__init__(experiment_data, **params)

        self.data_view = pn.widgets.Tabulator(
                value=pd.DataFrame(), disabled = True, sortable=False, pagination="remote", page_size=10000, widths=250,
                frozen_columns = ["attribute"], show_index = False, sizing_mode=sizing_mode)
        self.data_view.style.apply(func=self.style_table_by_row, axis=1)

        self.param_view = pn.Column(
            pn.Param(self.param.domain),
            pn.Param(self.param.problem),
            pn.pane.HTML("Algorithms", styles={'font-size': '10pt', 'font-family': 'Arial', 'padding-left': '10px'}),
            pn.widgets.CrossSelector.from_param(self.param.algorithms, definition_order = False, width = 475, styles={'padding-left': '10px'}),
            width=500
        )

        param_dict = self.set_experiment_data_dependent_parameters() | param_dict
        self.param.update(param_dict)
        # Setting the domain triggers update_problems, which overwrites problem
        # -> we need to set it again
        if "problem" in param_dict:
            self.problem = param_dict["problem"]


    def set_experiment_data_dependent_parameters(self):
        param_updates = super().set_experiment_data_dependent_parameters()
        self.param.domain.objects = ["--"] + self.experiment_data.domains
        self.param.problem.objects = ["--"]
        param_updates["domain"] = self.param.domain.objects[0]
        param_updates["problem"] = self.param.problem.objects[0]
        self.param.algorithms.objects = self.experiment_data.algorithms
        self.param.algorithms.default = self.experiment_data.algorithms
        param_updates["algorithms"] = self.experiment_data.algorithms

        self.data_view.formatters = { alg : {'type' : 'textarea'} for alg in self.experiment_data.algorithms }
        return param_updates

    def update_algorithm_names(self, mapping):
        self.param.algorithms.objects = self.experiment_data.algorithms
        self.algorithms = [mapping[x] for x in self.algorithms]



    @param.depends('domain', watch=True)
    def update_problems(self):
        self.param.problem.objects = ["--"]
        if self.domain != "--":
            self.param.problem.objects += self.experiment_data.problems[self.domain]
        self.problem = self.param.problem.objects[0]


    def style_table_by_row(self, row):
        style = [""] * len(row)
        attribute = row.iloc[0]
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


    def update_data_view(self):
        if not self.problem or self.problem == "--":
            self.data_view.value = pd.DataFrame()
        else:
            self.data_view.value = self.experiment_data.data[self.algorithms].xs((self.domain, self.problem), level=(1,2)).reset_index()


    def get_params_as_dict(self):
        return super().get_params_as_dict()


    # we set domain and problem sepearately because domain prepares the problem attribute with the possible values
    def set_params_from_dict(self, params):
        self.domain = params["domain"]
        self.problem = params["problem"]
        self.algorithms = params["algorithms"]
