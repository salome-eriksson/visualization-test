import param
import pandas as pd
import panel as pn

from experimentdata import ExperimentData
from report import Report

class WiseTablereport(Report):
    attribute = param.Selector(default="--")
    algorithms = param.ListSelector()


    def __init__(self, experiment_data = ExperimentData(), param_dict = dict(), **params):
        super().__init__(experiment_data, **params)

        self.domain_wise = pn.widgets.Tabulator(pd.DataFrame(), disabled = True, sizing_mode="stretch_both")
        self.task_wise = pn.widgets.Tabulator(pd.DataFrame(), disabled = True, sizing_mode="stretch_both")
        self.comparison = pn.widgets.Tabulator(pd.DataFrame(), disabled = True, sizing_mode="stretch_both")

        self.data_view = pn.Column(
            pn.pane.HTML("Domain Wise", styles={'font-size': '12pt', 'font-family': 'Arial', 'font-weight': 'bold', 'padding-left': '10px'}),
            self.domain_wise,
            pn.pane.HTML("Task Wise", styles={'font-size': '12pt', 'font-family': 'Arial', 'font-weight': 'bold', 'padding-left': '10px'}),
            self.task_wise,
            pn.pane.HTML("Comparison", styles={'font-size': '12pt', 'font-family': 'Arial', 'font-weight': 'bold', 'padding-left': '10px'}),
            self.comparison
        )

        # ~ self.data_view.style.apply(func=self.style_table_by_row, axis=1)

        self.param_view = pn.Column(
            pn.Param(self.param.attribute),
            pn.pane.HTML("Algorithms", styles={'font-size': '10pt', 'font-family': 'Arial', 'padding-left': '10px'}),
            pn.widgets.CrossSelector.from_param(self.param.algorithms, definition_order = False, width = 475, styles={'padding-left': '10px'}),
            width=500
        )

        param_dict = self.set_experiment_data_dependent_parameters() | param_dict
        self.param.update(param_dict)


    def set_experiment_data_dependent_parameters(self):
        param_updates = super().set_experiment_data_dependent_parameters()
        self.param.attribute.objects = ["--"] + self.experiment_data.numeric_attributes
        param_updates["attribute"] = self.param.attribute.objects[0]
        self.param.algorithms.objects = self.experiment_data.algorithms
        self.param.algorithms.default = self.experiment_data.algorithms
        param_updates["algorithms"] = self.experiment_data.algorithms
        return param_updates

    # ~ def style_table_by_row(self, row):
        # ~ style = [""] * len(row)
        # ~ attribute = row.iloc[0]
        # ~ min_wins = self.experiment_data.attribute_info[attribute].min_wins
        # ~ if min_wins is None:
            # ~ return style

        # ~ numeric_values = pd.to_numeric(row,errors='coerce')
        # ~ min_val = numeric_values.dropna().min()
        # ~ max_val = numeric_values.dropna().max()
        # ~ if min_val == max_val:
            # ~ return style
        # ~ for i, val in enumerate(numeric_values):
            # ~ if not pd.isnull(val):
                # ~ percentage = (val - min_val) / (max_val-min_val)
                # ~ if min_wins:
                  # ~ percentage = 1-percentage
                # ~ green = (percentage*175).astype(int)
                # ~ blue = ((1-percentage)*255).astype(int)
                # ~ style[i] = style[i]+ "color: #00{:02x}{:02x};".format(green, blue)
        # ~ return style


    def update_data_view(self):
        # TODO: Check if patching the table would be an idea
        # https://panel.holoviz.org/reference/widgets/Tabulator.html#patching
        self.domain_wise.value = pd.DataFrame( {
           a1 : {a2 : 0 for a2 in self.algorithms} for a1 in self.algorithms
        })
        self.task_wise.value = pd.DataFrame( {
           a1 : {a2 : 0 for a2 in self.algorithms} for a1 in self.algorithms
        })

        if not self.attribute or self.attribute == "--":
            self.data_view.value = pd.DataFrame()
            return

        attribute_table = self.experiment_data.data.loc[self.attribute].copy()
        task_wise_dict = { a1 : {a2 : 0 for a2 in self.algorithms} for a1 in self.algorithms }

        for a1 in self.algorithms:
            for a2 in self.algorithms:
                attribute_table[(a1,a2)] = attribute_table[a1]-attribute_table[a2]
                task_wise_dict[a1][a2] = len(attribute_table[~(attribute_table[(a1,a2)] > 0)].index)

        self.task_wise.value = pd.DataFrame(task_wise_dict)

    def get_params_as_dict(self):
        return super().get_params_as_dict()


    # we set domain and problem sepearately because domain prepares the problem attribute with the possible values
    def set_params_from_dict(self, params):
        self.attribute = params["attribute"]
        self.algorithms = params["algorithms"]
