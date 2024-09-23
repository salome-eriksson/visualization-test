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
from cactus import Cactusplot

pn.extension('floatpanel')
pn.extension('tabulator')
pn.extension('terminal')

class ReportViewer(param.Parameterized):
    report_type = param.Selector()
    properties_file = param.String(default="")
    custom_min_wins = param.Dict(default={},
        doc="Dictionary mapping (numeric) attributes to True/False, indicating whether a lower value is better or not.")
    custom_aggregators = param.Dict(default={},
        doc="Dictionary mapping (numeric) attributes to the type of aggregation (sum, mean, gmean).")
    custom_algorithm_names = param.Dict(default={},
        doc="Dictionary mapping original algorithm names to custom names.")
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
            "Wise Report": WiseTablereport(name="Wise Report"),
            "Cactus Plot": Cactusplot(name="Cactus Plot")
        }

        self.param.report_type.objects = [name for name in self.reports.keys()]
        self.report_type = self.param.report_type.objects[0]
        self.previous_report_type = self.report_type

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
            ["properties_file", "report_type", "custom_min_wins",
             "custom_aggregators", "custom_algorithm_names"])
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
            ["x_attribute", "y_attribute", "entries_list", "relative",
             "group_by", "x_scale", "y_scale", "autoscale", "x_range", "y_range",
             "replace_zero", "x_size", "y_size", "marker_size", "marker_fill_alpha",
             "markers", "colors"])
        self.reports["Wise Report"].param.watch(
            self.update_param_config,
            ["attribute"])
        self.reports["Cactus Plot"].param.watch(
            self.update_param_config,
            ["attribute", "algorithms", "x_scale", "y_scale", "autoscale",
             "x_range", "y_range", "replace_zero", "x_size", "y_size", "colors"])


    @param.depends('properties_file', watch=True)
    def update_property_file(self):
        self.experiment_data = ExperimentData(self.properties_file)
        for r in self.reports.values():
            r.update_experiment_data(self.experiment_data)


    @param.depends('custom_min_wins', 'custom_aggregators', 'custom_algorithm_names', watch=True)
    def update_attributes(self):
        self.experiment_data.set_attribute_customizations(
            self.custom_min_wins, self.custom_aggregators)
        mapping = self.experiment_data.rename_columns(self.custom_algorithm_names)
        for r in self.reports.values():
            r.update_algorithm_names(mapping)
            r.view_data()


    def view(self):
        if (self.previous_report_type != self.report_type):
            self.reports[self.previous_report_type].deactivate()
        self.previous_report_type = self.report_type
        return self.views[self.report_type]


    def update_param_config(self, *events):
        if self.setting_params:
            return
        self.setting_param_config = True
        params = self.reports[self.report_type].get_params_as_dict()
        if self.properties_file != self.param.properties_file.default:
            params["properties_file"] = self.properties_file
        params["report_type"] = sorted(self.reports.keys()).index(self.report_type)
        params["version"] = "1.0"
        params["custom_min_wins"] = self.custom_min_wins
        params["custom_aggregators"] = self.custom_aggregators
        params["custom_algorithm_names"] = self.custom_algorithm_names
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
                "report_type": sorted(self.reports.keys())[int(params.pop("report_type"))],
                "custom_min_wins": params.pop("custom_min_wins"),
                "custom_aggregators": params.pop("custom_aggregators"),
                "custom_algorithm_names": params.pop("custom_algorithm_names"),
            })
            assert(params.pop("version") == "1.0")
            self.reports[self.report_type].set_params_from_dict(params)
        except Exception as ex:
            pass
        self.setting_params = False



viewer = ReportViewer()
debugger = pn.widgets.Debugger(name='debugger', level=logging.INFO, logger_names=["panel"], only_last=False)
view = pn.Column(viewer.view, debugger)
pn.state.location.sync(viewer, { "param_config" : "c" })
view.servable()
