#! /usr/bin/env python3

import param
import pandas as pd
import panel as pn

from report import Report

pn.extension('tabulator')


class ProblemTablereport(Report):
    domain = param.Selector(["--"])
    problem = param.Selector(["--"])

    def __init__(self, **params):
        print("ProblemTablereport init")
        super().__init__(**params)
        print("ProblemTablereport init end")

    def set_experiment_data_dependent_parameters(self):
        print("ProblemTablereport set_experiment_data_dependent_parameters")
        self.param.domain.objects = ["--"] + self.experiment_data.domains
        self.param.problem.objects = ["--"]
        self.param.update({
            "domain" : self.param.domain.objects[0],
            "problem": self.param.problem.objects[0]
        })
        print("ProblemTablereport set_experiment_data_dependent_parameters end")
    
    @param.depends('domain', watch=True)
    def update_problems(self):
        print("ProblemTablereport update_problems")
        if self.domain != "--": 
            self.param.problem.objects = ["--"] + self.experiment_data.problems[self.domain]
            self.problem = self.param.problem.objects[0]
        print("ProblemTablereport update_problems end")

    def data_view(self):
        print("ProblemTablereport data_view")
        if self.problem == "--":
            return pn.pane.Markdown()
        row = self.experiment_data.data.loc[(self.domain, self.problem)]
        
        entries = dict()
        tabulator_formatters = dict()
        attributes_sorted = sorted(self.experiment_data.attributes)
        for alg in self.experiment_data.algorithms:
            entries["attribute"] = attributes_sorted
            entries[alg] = [row[f"{alg}_{attribute}"] for attribute in attributes_sorted]
            tabulator_formatters[alg] = {'type': 'textarea'}
        view_data = pd.DataFrame(entries)
        view_data.set_index("attribute")
        
        self.view = pn.widgets.Tabulator(value=view_data, show_index=False, disabled = True, pagination=None, widths=250, formatters=tabulator_formatters)
        print("ProblemTablereport data_view end")
        return self.view
            
    def param_view(self):
        print("ProblemTablereport param_view (end)")
        return pn.Param(self.param)
