#! /usr/bin/env python3

import param
import pandas as pd
import panel as pn

from report import Report

pn.extension('tabulator')


class ProblemTablereport(Report):
    domain = param.String()
    problem = param.String()

    def __init__(self, experiment_data, domain, problem, **params):
        super().__init__(**params)
        self.experiment_data = experiment_data
        self.domain = domain
        self.problem = problem

    def data_view(self):
        if self.experiment_data.data.empty:
            return pn.pane.Markdown("### Hello")
        row = self.experiment_data.data.loc[(self.domain, self.problem)]#.iloc[0]
        
        entries = dict()
        tabulator_formatters = dict()
        for alg in self.experiment_data.algorithms:
            entries["attribute"] = self.experiment_data.attributes
            entries[alg] = [row[f"{alg}_{attribute}"] for attribute in self.experiment_data.attributes]
            tabulator_formatters[alg] = {'type': 'textarea'}
        view_data = pd.DataFrame(entries)
        view_data.set_index("attribute")
        
        view = pn.widgets.Tabulator(value=view_data, show_index=False, disabled = True, pagination=None, widths=250, formatters=tabulator_formatters)
        return view
            
