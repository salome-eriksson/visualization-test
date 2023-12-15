#! /usr/bin/env python3

import param
import pandas as pd
import panel as pn

from report import Report

pn.extension('tabulator')


class ProblemTablereport(Report):
    domain = param.Selector()
    problem = param.Selector()

    def __init__(self, experiment_data = None, domain = "", problem = "", **params):
        super().__init__(**params)
        self.experiment_data = experiment_data
        if self.experiment_data:
            self.set_experiment_data_dependent_parameters()
        self.domain = domain
        self.problem = problem

    def set_experiment_data_dependent_parameters(self):
        self.param.domain.objects = self.experiment_data.domains
        self.domain = self.experiment_data.domains[0]
    
    @param.depends('domain', watch=True)
    def update_problems(self):
        if self.experiment_data:
            self.param.problem.objects = self.experiment_data.problems[self.domain]
            self.problem = self.experiment_data.problems[self.domain][0]

    def data_view(self):
        if not self.experiment_data or self.experiment_data.data.empty or self.domain == "" or self.problem == "":
            return pn.pane.Markdown("### Hello")
        row = self.experiment_data.data.loc[(self.domain, self.problem)]#.iloc[0]
        
        entries = dict()
        tabulator_formatters = dict()
        attributes_sorted = sorted(self.experiment_data.attributes)
        for alg in self.experiment_data.algorithms:
            entries["attribute"] = attributes_sorted
            entries[alg] = [row[f"{alg}_{attribute}"] for attribute in attributes_sorted]
            tabulator_formatters[alg] = {'type': 'textarea'}
        view_data = pd.DataFrame(entries)
        view_data.set_index("attribute")
        
        view = pn.widgets.Tabulator(value=view_data, show_index=False, disabled = True, pagination=None, widths=250, formatters=tabulator_formatters)
        return view
            
    def param_view(self):
        return pn.Param(self.param)
