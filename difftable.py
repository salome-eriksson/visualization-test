import math
import numpy as np
import param
import pandas as pd
import panel as pn

from experimentdata import ExperimentData
from table import Tablereport

class DiffTablereport(Tablereport):
    algorithm1 = param.Selector(default="--")
    algorithm2 = param.Selector(default="--")
    percentual = param.Boolean(default=False)


    def __init__(self, experiment_data = ExperimentData(), param_dict = dict(), **params):
        super().__init__(experiment_data, **params)

        self.param_view.extend([
            pn.Param(self.param.algorithm1),
            pn.Param(self.param.algorithm2),
            pn.Row(
                pn.Param(self.param.percentual),
                pn.widgets.TooltipIcon(value="If true, the Diff column is computed with\n(Algorithm2/Algorithm1)-1 instead of\nAlgorithm2-Algorithm1.")
            ), #added separate tooltip since the checkbox widget does not seem to support making a tooltip from the param doc
            pn.pane.Markdown("""
                ### Information
                Data is organized by attribute, then domain, then problem.
                You can click on attributes/domains to unfold the next level,
                and reclick to fold again. Clicking on a concrete problem opens
                a ProblemReport comparing all attributes for this specific
                problem. Several popups can be open at the same time, but they
                will be removed when the ReportType is changed.

                Numeric values are aggregated over the set of instances where
                both algorithms have a value for the corresponding attribute.
                They are also color-coded, with blue denoting a worse
                and green a better value.
                """)
        ])
        param_dict = self.set_experiment_data_dependent_parameters() | param_dict
        self.param.update(param_dict)

    def set_experiment_data_dependent_parameters(self):
        param_updates = super().set_experiment_data_dependent_parameters()
        self.param.algorithm1.objects = ["--", *self.experiment_data.algorithms]
        self.param.algorithm2.objects = ["--", *self.experiment_data.algorithms]
        param_updates["algorithm1"] = "--"
        param_updates["algorithm2"] = "--"
        return param_updates


    def get_view_table(self):
        if self.algorithm1 == "--" or self.algorithm2 == "--" or self.algorithm1 == self.algorithm2:
            return pd.DataFrame()

        mapping = dict()
        retdata = self.table[["Index",self.algorithm1, self.algorithm2]].copy()
        col1_numeric = pd.to_numeric(self.table[self.algorithm1], errors="coerce")
        col2_numeric = pd.to_numeric(self.table[self.algorithm2], errors="coerce")
        if self.percentual:
            retdata["Diff"] = (col2_numeric / col1_numeric)-1
        else:
            retdata["Diff"] = col2_numeric - col1_numeric
        return retdata


    def get_current_columns(self):
        if self.algorithm1 != "--" and self.algorithm2 != "--":
            return [self.algorithm1, self.algorithm2]
        else:
            return []


    def style_table_by_row(self, row):
        style = super().style_table_by_row(row)
        attribute = row.name[0]
        min_wins = self.experiment_data.attribute_info[attribute].min_wins

        if min_wins is None:
            return style

        color = 'black'
        if (row["Diff"] > 0 and min_wins) or (row["Diff"] < 0 and not min_wins):
            color = 'red'
        elif (row["Diff"] < 0 and min_wins) or (row["Diff"] > 0 and not min_wins):
            color= 'green'
        style[-1] += f"color: {color}"
        return style


    def get_params_as_dict(self):
        return super().get_params_as_dict()


    def set_params_from_dict(self, params):
        super().set_params_from_dict(params)
        self.param.update(params) #TODO: currently we need to make sure that the child calls this, maybe redesign...
