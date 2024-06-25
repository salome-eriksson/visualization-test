import numpy as np
import param
import pandas as pd
import panel as pn

from experimentdata import ExperimentData
from report import Report

class WiseTablereport(Report):
    attribute = param.Selector(default="--")


    def __init__(self, experiment_data = ExperimentData(), param_dict = dict(), **params):
        super().__init__(experiment_data, **params)

        self.domain_wise_table = pd.DataFrame()
        self.task_wise_table = pd.DataFrame()
        self.domain_wise = pn.widgets.Tabulator(pd.DataFrame(), disabled = True, pagination="remote", page_size=1000)
        self.task_wise = pn.widgets.Tabulator(pd.DataFrame(), disabled = True, pagination="remote", page_size=1000)
        self.comparison = pn.widgets.Tabulator(pd.DataFrame(), disabled = True, pagination="remote", page_size=100)

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
            pn.Param(self.param.attribute)
        )

        param_dict = self.set_experiment_data_dependent_parameters() | param_dict
        self.param.update(param_dict)


    def set_experiment_data_dependent_parameters(self):
        param_updates = super().set_experiment_data_dependent_parameters()
        self.param.attribute.objects = ["--"] + self.experiment_data.numeric_attributes
        param_updates["attribute"] = self.param.attribute.objects[0]


        d = { a1 : {a2 : 0 for a2 in self.experiment_data.algorithms} for a1 in self.experiment_data.algorithms }
        self.task_wise_table = pd.DataFrame(d)
        self.domain_wise_table = pd.DataFrame(d)

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
        if not self.attribute or self.attribute == "--":
            self.data_view.value = pd.DataFrame()
            return

        min_wins = self.experiment_data.attribute_info[self.attribute].min_wins

        attribute_table = self.experiment_data.data.loc[self.attribute].copy()
        domain_group = pd.DataFrame()
        attribute_table.replace([np.NaN, None], np.inf if min_wins else -np.inf, inplace=True)



        for a1 in self.experiment_data.algorithms:
            l = []
            for a2 in self.experiment_data.algorithms:
                attribute_table[(a1,a2)] = attribute_table[a1]-attribute_table[a2]
                attribute_table[(a1,a2,"win")] = np.sign(attribute_table[(a1,a2)])
                if min_wins:
                  attribute_table[(a1,a2,"win")] *= -1
                num_better = len(attribute_table[(attribute_table[(a1,a2,"win")] > 0)].index)
                self.task_wise_table.at[a1,a2] = num_better

                domain_group[(a1,a2,"win")] = attribute_table[(a1,a2,"win")].groupby(["domain"]).sum()
                self.domain_wise_table.at[a1,a2] = len(domain_group[domain_group[(a1,a2,"win")] > 0].index)

        domain_group["problem"] = "--"
        domain_group = domain_group.reset_index().set_index(["domain","problem"])
        tmp = pd.concat([attribute_table, domain_group]).sort_index()

        self.task_wise.value = self.task_wise_table[self.experiment_data.algorithms]
        self.domain_wise.value = self.domain_wise_table[self.experiment_data.algorithms]
        self.comparison.value = tmp[[("HEAD-blind-verify", "HEAD-blind-noverify"), ("HEAD-blind-verify", "HEAD-blind-noverify", "win")]]

    def get_params_as_dict(self):
        return super().get_params_as_dict()


    # we set domain and problem sepearately because domain prepares the problem attribute with the possible values
    def set_params_from_dict(self, params):
        self.attribute = params["attribute"]
