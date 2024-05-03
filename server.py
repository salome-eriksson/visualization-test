#! /usr/bin/env python3

import base64 # for encoding the compressed json parameter dict as url
import json # for dumping the parameter dict as json
import param
import panel as pn
import zlib # for compressing the json parameter dict

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
    properties_file = param.String(default="")
    param_config = param.String(precedence=-1)

    def __init__(self, **params):
        super().__init__(**params)

        self.setting_param_config = False
        self.setting_params = False
        
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
        if self.param_config:
            set_from_param_config()
        
        #register callback for creating config string for url
        self.param.watch(self.update_param_config, ["properties_file", "reportType"])
        self.reports["Absolute Report"].param.watch(
            self.update_param_config,
            ["attributes", "domains", "custom_min_wins", "custom_aggregators", "algorithms"])
        self.reports["Diff Report"].param.watch(
            self.update_param_config,
            ["attributes", "domains", "custom_min_wins", "custom_aggregators", 
             "algorithm1", "algorithm2", "percentual"])
        self.reports["Problem Report"].param.watch(
            self.update_param_config,
            ["domain", "problem"])
        self.reports["Scatter Plot"].param.watch(
            self.update_param_config,
            ["xattribute", "yattribute", "entries_list", "relative",
             "groupby", "xscale", "yscale", "autoscale", "x_range", "y_range",
             "replace_zero", "xsize", "ysize", "marker_size", "marker_fill_alpha",
             "markers", "colors"])


    @param.depends('properties_file', watch=True)
    def update_property_file(self):
        self.experiment_data = ExperimentData(self.properties_file)
        for r in self.reports.values():
            r.update_experiment_data(self.experiment_data)


    def view(self):
        if (self.previous_reportType != self.reportType):
            self.reports[self.previous_reportType].deactivate()
        self.previous_reportType = self.reportType
        return self.views[self.reportType]


    def update_param_config(self, *events):
        if self.setting_params:
            return
        self.setting_param_config = True
        params = self.reports[self.reportType].get_params_as_dict()
        if self.properties_file != self.param.properties_file.default:
            params["properties_file"] = self.properties_file
        params["reportType"] = sorted(self.reports.keys()).index(self.reportType)
        params["version"] = "1.0"
        self.param_config = base64.urlsafe_b64encode(zlib.compress(json.dumps(params).encode())).decode()
        self.setting_param_config = False


    @param.depends("param_config", watch=True)
    def set_from_param_config(self):
        if self.setting_param_config:
            return
        self.setting_params = True
        try:
            params = json.loads(zlib.decompress(base64.urlsafe_b64decode(self.param_config.encode())))
            self.param.update({
                "properties_file": params.pop("properties_file"),
                "reportType": sorted(self.reports.keys())[int(params.pop("reportType"))],
            })
            assert(params.pop("version") == "1.0")
            self.reports[self.reportType].set_params_from_dict(params)
        except Exception as ex:
            pass
        self.setting_params = False


viewer = ReportViewer()
view = pn.Row(viewer.view)
pn.state.location.sync(viewer, { "param_config" : "c" })
view.servable()
