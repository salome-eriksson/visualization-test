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



class ReportViewer(param.Parameterized):
    reportType = param.Selector()
    properties_file = param.String()
    version = param.String("1.0")
    param_config = param.String()

    def __init__(self, **params):
        print("ReportViewer init")
        super().__init__(**params)
        self.reports = {
            "Absolute Report" : AbsoluteTablereport(name="Absolute Report"),
            "Diff Report" : DiffTablereport(name="Diff Report"),
            "Problem Report" : ProblemTablereport(name="Problem Report"),
            "Scatter Plot" : Scatterplot(name="Scatter Plot")
        }
        self.param.reportType.objects = [name for name in self.reports.keys()]
        self.reportType = self.param.reportType.objects[0]
        self.previous_reportType = self.reportType
        self.experiment_data = ExperimentData("")

        self.views = dict()
        for key, r in self.reports.items():
            self.views[key] = pn.Row(
                                    pn.Column(pn.Param(self.param, name=""), r.param_view),
                                    pn.panel(r.data_view, defer_load=True), sizing_mode='stretch_both'
                                 )
        
        self.update_param_config()
        
        #register callback for creating config string for url
        self.param.watch(self.update_param_config, ["properties_file", "reportType"])
        self.reports["Absolute Report"].param.watch(
            self.update_param_config,
            ["attributes", "custom_min_wins", "custom_aggregators", "algorithms"])
        self.reports["Diff Report"].param.watch(
            self.update_param_config,
            ["attributes", "custom_min_wins", "custom_aggregators", 
             "algorithm1", "algorithm2", "percentual"])
        self.reports["Problem Report"].param.watch(
            self.update_param_config,
            ["domain", "problem"])
        self.reports["Scatter Plot"].param.watch(
            self.update_param_config,
            ["xattribute", "yattribute", "entries_list", "relative",
             "groupby", "xscale", "yscale", "autoscale", "x_range", "y_range",
             "replace_zero", "xsize", "ysize", "marker_size", "marker_fill_alpha"])
        
        print("ReportViewer init end")
    
    @param.depends('properties_file', watch=True)
    def update_property_file(self):
        print("ReportViewer update_property_file")
        self.experiment_data = ExperimentData(self.properties_file)
        for r in self.reports.values():
            r.update_experiment_data(self.experiment_data)
        print("ReportViewer update_property_file end")
    
        
    def view(self):
        print("ReportViewer view (end)")
        self.reports[self.previous_reportType].deactivate()
        self.previous_reportType = self.reportType
        return self.views[self.reportType]
        

    def update_param_config(self, *events):
        report = self.reports[self.reportType]
        report_no = sorted(self.reports.keys()).index(self.reportType)
        self.param_config = f"{self.properties_file};{report_no};{report.get_param_config()}"
        
    @param.depends("param_config", watch=True)
    def set_from_param_config(self):
        print(f"set from param {self.param_config}")
        parts = self.param_config.split(";")
        # We only want to execute this once when loading a new session (TODO: find better way)
        if self.properties_file == parts[0]:
            return
        # First update properties so the reports have the proper algorithms/attributes etc set up
        self.param.update({
            "properties_file" : parts[0],
            "reportType": sorted(self.reports.keys())[int(parts[1])]
        })
        self.reports[self.reportType].param.update(
           self.reports[self.reportType].get_params_from_string(parts[2:])
        )
        
viewer = ReportViewer()
view = pn.Row(viewer.view)
pn.state.location.sync(viewer, { "version" : "version", "param_config" : "config" })
view.servable()
