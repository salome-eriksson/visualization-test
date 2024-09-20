from functools import partial
import numpy as np
import param
import pandas as pd
import panel as pn

from experimentdata import ExperimentData
from prpopupreport import PRPopupReport

class WiseTablereport(PRPopupReport):
    attribute = param.Selector(default="--")


    def __init__(self, experiment_data = ExperimentData(), param_dict = dict(), **params):
        super().__init__(experiment_data, **params)

        self.domain_wise_table = pd.DataFrame()
        self.task_wise_table = pd.DataFrame()
        self.per_task_table = pd.DataFrame()
        self.per_domain_table = pd.DataFrame()
        self.domain_wise = pn.widgets.Tabulator(pd.DataFrame(), disabled = True, sortable=False, pagination="remote", page_size=1000)
        self.domain_wise.style.apply(func=partial(self.style_wise_by_row, table_type="domain"), axis=1)
        self.domain_wise.on_click(self.on_domain_wise_click_callback)
        self.task_wise = pn.widgets.Tabulator(pd.DataFrame(), disabled = True, sortable=False, pagination="remote", page_size=1000)
        self.task_wise.style.apply(func=partial(self.style_wise_by_row, table_type="task"), axis=1)
        self.task_wise.on_click(self.on_task_wise_click_callback)
        self.comparison = pn.widgets.Tabulator(pd.DataFrame(), disabled = True, pagination="remote", page_size=100)
        self.comparison.on_click(self.on_comparison_click_callback)
        self.current_comparison = None

        self.data_view = pn.Column(
            pn.pane.HTML("Domain Wise", styles={'font-size': '12pt', 'font-family': 'Arial', 'font-weight': 'bold', 'padding-left': '10px'}),
            self.domain_wise,
            pn.pane.HTML("Task Wise", styles={'font-size': '12pt', 'font-family': 'Arial', 'font-weight': 'bold', 'padding-left': '10px'}),
            self.task_wise,
            pn.pane.HTML("Comparison", styles={'font-size': '12pt', 'font-family': 'Arial', 'font-weight': 'bold', 'padding-left': '10px'}),
            self.comparison
        )

        self.param_view = pn.Column(
            pn.Param(self.param.attribute),
            pn.pane.Markdown("""
                ### Information

                Shows on how many domains/problems the row entry algorithm is
                better than the column entry algorithm. Clicking on a cell
                gives a detailed comparison table below the domain/task wise
                tables.

                When having a taskwise comparison open, klicking on a row will
                open a ProblemReport comparing all attributes for this specific
                problem.
            """)
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
        self.current_comparison = None

        return param_updates


    def style_wise_by_row(self, row, table_type):
        style = [""] * len(row)
        row_alg = row.name
        df = self.task_wise_table if table_type == "task" else self.domain_wise_table

        for i, (alg, val) in enumerate(row.items()):
            if df.at[alg, row_alg] < val:
                style[i] = style[i] + "font-weight:bold;"
            elif row.name == alg:
                style[i] = style[i] + "color:gray;"
        return style


    def on_domain_wise_click_callback(self, e):
        self.domain_wise.selection = []
        row_alg = self.domain_wise_table.iloc[e.row].name
        col_alg = e.column
        if col_alg not in self.domain_wise_table.columns:
            return
        self.current_comparison = "domain"
        self.comparison.sorters = []
        self.comparison.value = pd.DataFrame()
        self.comparison.value = self.per_domain_table[[(row_alg, col_alg, "win")]]


    def on_task_wise_click_callback(self, e):
        self.task_wise.selection = []
        row_alg = self.task_wise_table.iloc[e.row].name
        col_alg = e.column
        if col_alg not in self.task_wise_table.columns:
            return
        self.current_comparison = "problem"
        self.comparison.sorters = []
        self.comparison.value = pd.DataFrame()
        self.comparison.value = self.per_task_table[list({row_alg, col_alg, (row_alg, col_alg)})]


    def on_comparison_click_callback(self, e):
        self.comparison.selection = []
        if self.current_comparison == "domain":
            return
        row = self.comparison.value.iloc[e.row]
        domain = row.name[0]
        problem = row.name[1]
        algorithms = list(set(row.keys()).intersection(set(self.experiment_data.algorithms)))
        self.add_problem_report_popup(domain, problem, algorithms)


    def update_data_view(self):
        if not self.attribute or self.attribute == "--":
            self.data_view.value = pd.DataFrame()
            return

        min_wins = self.experiment_data.attribute_info[self.attribute].min_wins

        self.per_task_table = self.experiment_data.data.loc[self.attribute].copy()
        self.per_task_table.replace([np.NaN, None], np.inf if min_wins else -np.inf, inplace=True)

        for a1 in self.experiment_data.algorithms:
            l = []
            for a2 in self.experiment_data.algorithms:
                self.per_task_table[(a1,a2)] = self.per_task_table[a1]-self.per_task_table[a2]
                self.per_task_table[(a1,a2,"win")] = np.sign(self.per_task_table[(a1,a2)])
                if min_wins:
                  self.per_task_table[(a1,a2,"win")] *= -1
                num_better = len(self.per_task_table[(self.per_task_table[(a1,a2,"win")] > 0)].index)
                self.task_wise_table.at[a1,a2] = num_better

                self.per_domain_table[(a1,a2,"win")] = self.per_task_table[(a1,a2,"win")].groupby(["domain"]).sum()
                self.domain_wise_table.at[a1,a2] = len(self.per_domain_table[self.per_domain_table[(a1,a2,"win")] > 0].index)

        self.task_wise.value = self.task_wise_table[self.experiment_data.algorithms]
        self.domain_wise.value = self.domain_wise_table[self.experiment_data.algorithms]
        self.comparison.value = pd.DataFrame()

    def get_params_as_dict(self):
        return super().get_params_as_dict()


    # we set domain and problem sepearately because domain prepares the problem attribute with the possible values
    def set_params_from_dict(self, params):
        self.attribute = params["attribute"]
