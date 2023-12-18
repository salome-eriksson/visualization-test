#! /usr/bin/env python3

import param
import panel as pn
import copy

from experimentdata import ExperimentData
from report import Report
from scatter import Scatterplot
from absolutetable import AbsoluteTablereport
from difftable import DiffTablereport
from problemtable import ProblemTablereport

pn.extension()

class ReportViewer(param.Parameterized):
    reportType = param.Selector()
    properties_file = param.String()

    def __init__(self, **params):
        super().__init__(**params)
        self.reports = [
            AbsoluteTablereport(name="Absolute Report"),
            DiffTablereport(name="Diff Report"),
            ProblemTablereport(name="Problem Report"),
            Scatterplot(name="Scatter Plot")
        ]
        self.param.reportType.objects = [r.name for r in self.reports]
        self.reportType = self.reports[0].name
        self.experiment_data = ExperimentData("")
        
        param_view = pn.Column()
        param_view.append(pn.Param(self.param, name="", expand_button=False))
        data_view = pn.Column()
        for r in self.reports:
            param_view.append(r.param_view)
            data_view.append(r.data_view)
        self.full_view = pn.Row(param_view,data_view)
    
    @param.depends('properties_file', watch=True)
    def update_property_file(self):
        self.experiment_data = ExperimentData(self.properties_file)
        for r in self.reports:
            r.properties_file = self.properties_file
            r.update_experiment_data(self.experiment_data)
        
    def view(self):
        for i in range(len(self.reports)):
            if self.reports[i].name == self.reportType:
                self.full_view[0][i+1].visible = True
                self.full_view[1][i].visible = True
            else:
                self.full_view[0][i+1].visible = False
                self.full_view[1][i].visible = False
        return self.full_view
        
        
viewer = ReportViewer()
view = pn.Row(viewer.view)
view.servable()
