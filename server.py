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

pn.extension('tabulator')
pn.extension('floatpanel')

# TODO: cannot run multiple sessions
# I get output on console but other than the first tab no visualization shows
# (other than default from beginning)
# Maybe I need instantiate?

class ReportViewer(param.Parameterized):
    reportType = param.Selector()
    properties_file = param.String()

    def __init__(self, **params):
        print("ReportViewer init")
        super().__init__(**params)
        self.reports = [
            AbsoluteTablereport(name="Absolute Report"),
            DiffTablereport(name="Diff Report"),
            ProblemTablereport(name="Problem Report"),
            Scatterplot(name="Scatter Plot")
        ]
        self.param.reportType.objects = [r.name for r in self.reports]
        self.param.reportType.default = self.reports[0].name
        self.reportType = self.reports[0].name
        self.experiment_data = ExperimentData("")

        self.views = dict()
        for r in self.reports:
            self.views[r.name] = pn.Row(
                                    pn.Column(pn.Param(self.param, name=""), r.param_view),
                                    pn.panel(r.data_view, defer_load=True), sizing_mode='stretch_both'
                                 )
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
pn.state.location.sync(viewer,
    {
        "properties_file" : "properties_file",
        "reportType" : "reportType",
    })
pn.state.location.sync(viewer.reports[0],
    {
        "attributes" : "ARattributes",
        "custom_min_wins" : "ARcustom_min_wins",
        "custom_aggregators" : "ARcustom_aggregators",
        "algorithms" : "ARalgorithms"
    })
pn.state.location.sync(viewer.reports[1],
    {
        "attributes" : "DRattributes",
        "custom_min_wins" : "DRcustom_min_wins",
        "custom_aggregators" : "DRcustom_aggregators",
        "algorithm1" : "DRalgorithm1",
        "algorithm2" : "DRalgorithm2",
        "percentual" : "DRpercentual"
    })

pn.state.location.sync(viewer.reports[2],
    {
        "domain" : "PRdomain",
        "problem" : "PRproblem"
    })
pn.state.location.sync(viewer.reports[3],
    {
        'xattribute' : 'SPxattribute',
        'yattribute' : 'SPyattribute',
        'entries_list' : 'SPentries_list',
        'relative': 'SPrelative',
        'xscale': 'SPxscale',
        'yscale': 'SPyscale',
        'groupby': 'SPgroupby',
        'fill_alpha': 'SPfill_alpha',
        'marker_size' : 'SPmarker_size',
        'xsize' : 'SPxsize',
        'ysize' : 'SPysize',
        'replace_zero' : 'SPreplace_zero',
        'autoscale' : 'SPautoscale',
        'x_range' : 'SPx_range',
        'y_range' : 'SP_range'
    })
view.servable()
