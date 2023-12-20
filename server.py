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
        print("ReportViewer init")
        super().__init__(**params)
        self.reports = [
            # ~ AbsoluteTablereport(name="Absolute Report"),
            # ~ DiffTablereport(name="Diff Report"),
            ProblemTablereport(name="Problem Report"),
            # ~ Scatterplot(name="Scatter Plot")
        ]
        self.param.reportType.objects = [r.name for r in self.reports]
        self.param.reportType.default = self.reports[0].name
        self.reportType = self.reports[0].name
        self.experiment_data = ExperimentData("")

        self.views = dict()
        for r in self.reports:
            self.views[r.name] = pn.Row(
                                    pn.Column(pn.Param(self.param, name=""), r.param_view),
                                    r.data_view)
        print("ReportViewer init end")
    
    @param.depends('properties_file', watch=True)
    def update_property_file(self):
        print("ReportViewer update_property_file")
        self.experiment_data = ExperimentData(self.properties_file)
        for r in self.reports:
            r.update_experiment_data(self.experiment_data)
        print("ReportViewer update_property_file end")
        
    def view(self):
        print("ReportViewer view (end)")
        return self.views[self.reportType]
        
        
viewer = ReportViewer()
view = pn.Row(viewer.view)
view.servable()
