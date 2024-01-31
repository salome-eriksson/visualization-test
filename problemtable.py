#! /usr/bin/env python3

import param
import pandas as pd
import panel as pn

from report import Report


class ProblemTablereport(Report):
    domain = param.Selector(default="--")
    problem = param.Selector(default="--")


    def __init__(self, domain=None, problem=None, sizing_mode="stretch_both", **params):
        print("ProblemTablereport init")
        super().__init__(**params)
        self.sizing_mode = sizing_mode
        if domain and problem:
            self.domain = domain
            self.problem = problem
        print("ProblemTablereport init end")


    def set_experiment_data_dependent_parameters(self):
        print("ProblemTablereport set_experiment_data_dependent_parameters")
        param_updates = super().set_experiment_data_dependent_parameters()
        self.param.domain.objects = ["--"] + self.experiment_data.domains
        self.param.problem.objects = ["--"]
        param_updates["domain"] = self.param.domain.objects[0]
        param_updates["problem"] = self.param.problem.objects[0]
        print("ProblemTablereport set_experiment_data_dependent_parameters end")
        return param_updates


    @param.depends('domain', watch=True)
    def update_problems(self):
        print("ProblemTablereport update_problems")
        if self.domain != "--": 
            self.param.problem.objects = ["--"] + self.experiment_data.problems[self.domain]
            self.problem = self.param.problem.objects[0]
        print("ProblemTablereport update_problems end")


    def data_view(self):
        print("ProblemTablereport data_view")
        if not self.problem or self.problem == "--":
            return pn.pane.Markdown()

        tabulator_formatters = dict()
        for alg in self.experiment_data.algorithms:
            tabulator_formatters[alg] = {'type': 'textarea'}
        view_data = self.experiment_data.data.xs((self.domain, self.problem), level=(1,2))
        self.view = pn.widgets.Tabulator(
                value=view_data, disabled = True, pagination="remote", page_size=10000, widths=250, 
                formatters=tabulator_formatters, frozen_columns=['attribute'], sizing_mode=self.sizing_mode)
        print("ProblemTablereport data_view end")
        return self.view


    def param_view(self):
        print("ProblemTablereport param_view (end)")
        return pn.Param(self.param)


    def get_params_as_dict(self):      
        return super().get_params_as_dict()


    # we set domain and problem sepearately because domain prepares the problem attribute with the possible values
    def set_params_from_dict(self, params):
        self.domain = params["domain"]
        self.problem = params["problem"]
