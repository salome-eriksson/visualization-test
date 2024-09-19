#! /usr/bin/env python3

import base64 # for encoding the compressed json parameter dict as url
import json # for dumping the parameter dict as json
import logging
import param
import panel as pn
import zlib # for compressing the json parameter dict

from absolutetable import AbsoluteTablereport
from difftable import DiffTablereport
from experimentdata import ExperimentData
from problemtable import ProblemTablereport
from scatter import Scatterplot
from wisetable import WiseTablereport

pn.extension('floatpanel')
pn.extension('tabulator')
pn.extension('terminal')

class ReportViewer(param.Parameterized):
    reportType = param.Selector()
    properties_file = param.String(default="")
    custom_min_wins = param.Dict(default={})
    custom_aggregators = param.Dict(default={})
    param_config = param.String(precedence=-1)


    def __init__(self, **params):
        super().__init__(**params)
        self.logger = logging.getLogger("panel")

        self.setting_param_config = False
        self.setting_params = False

        self.reports = {
            "Absolute Report" : AbsoluteTablereport(name="Absolute Report"),
            "Diff Report" : DiffTablereport(name="Diff Report"),
            "Problem Report" : ProblemTablereport(name="Problem Report"),
            "Scatter Plot" : Scatterplot(name="Scatter Plot"),
            "Wise Report": WiseTablereport(name="Wise Report")
        }
        self.param.reportType.objects = [name for name in self.reports.keys()]
        self.reportType = self.param.reportType.objects[0]
        self.previous_reportType = self.reportType

        self.views = dict()
        for key, r in self.reports.items():
            self.views[key] = pn.Row(
                                  pn.Column(pn.Param(self.param, name=""), r.view_param, width=500, scroll=True),
                                  pn.panel(r.view_data, defer_load=True, scroll=True), sizing_mode='stretch_both'
                              )
        if self.param_config:
            set_from_param_config()
        else:
            self.experiment_data = ExperimentData()
            for r in self.reports.values():
                r.update_experiment_data(self.experiment_data)

        #register callback for creating config string for url
        self.param.watch(self.update_param_config,
            ["properties_file", "reportType", "custom_min_wins",
             "custom_aggregators"])
        self.reports["Absolute Report"].param.watch(
            self.update_param_config,
            ["attributes", "domains", "algorithms", "precision"])
        self.reports["Diff Report"].param.watch(
            self.update_param_config,
            ["attributes", "domains", "algorithm1", "algorithm2", "percentual",
             "precision"])
        self.reports["Problem Report"].param.watch(
            self.update_param_config,
            ["domain", "problem", "algorithms"])
        self.reports["Scatter Plot"].param.watch(
            self.update_param_config,
            ["xattribute", "yattribute", "entries_list", "relative",
             "groupby", "xscale", "yscale", "autoscale", "x_range", "y_range",
             "replace_zero", "xsize", "ysize", "marker_size", "marker_fill_alpha",
             "markers", "colors"])
        self.reports["Wise Report"].param.watch(
            self.update_param_config,
            ["attribute"])


    @param.depends('properties_file', watch=True)
    def update_property_file(self):
        self.experiment_data = ExperimentData(self.properties_file)
        for r in self.reports.values():
            r.update_experiment_data(self.experiment_data)


    @param.depends('custom_min_wins', 'custom_aggregators', watch=True)
    def update_attributes(self):
        self.experiment_data.set_attribute_customizations(
            self.custom_min_wins, self.custom_aggregators)
        for r in self.reports.values():
            r.view_data()


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
        params["custom_min_wins"] = self.custom_min_wins
        params["custom_aggregators"] = self.custom_aggregators
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
                "custom_min_wins": params.pop("custom_min_wins"),
                "custom_aggregators": params.pop("custom_aggregators"),
            })
            assert(params.pop("version") == "1.0")
            self.reports[self.reportType].set_params_from_dict(params)
        except Exception as ex:
            pass
        self.setting_params = False



viewer = ReportViewer()
debugger = pn.widgets.Debugger(name='debugger', level=logging.INFO, logger_names=["panel"], only_last=False)
view = pn.Column(viewer.view, debugger)
pn.state.location.sync(viewer, { "param_config" : "c" })
view.servable()
