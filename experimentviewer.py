import param
import panel as pn
import copy

from scatter import Scatterplot
from table import Tablereport

class ReportViewer(param.Parameterized):
    report = param.Selector()

    def __init__(self, **params):
        super().__init__(**params)
        self.param.report.objects = [Scatterplot(name = "Scatterplot"),Tablereport(name = "Tablereport")]
        self.report = self.param.report.objects[1]

    def viewer_param_view(self):
        return pn.Param(self.param, name="", expand_button=False)
    
    def report_param_view(self):
        return self.report.param_view

    def report_data_view(self):
        return self.report.data_view

class ExperimentViewer(param.Parameterized):
    num_reports = param.Integer(default=0)
    report_viewers = param.List(precedence=-1)

    def __init__(self, report_viewers=[ReportViewer()], **params):
        # ~ print("ExperimentViewer Init")
        super().__init__(**params)
        self.report_viewers = report_viewers
        self.num_reports = len(self.report_viewers)
        # ~ print("ExperimentViewer Init end")

    @param.depends('num_reports', watch=True)
    def update_num_reports(self):
        # ~ print("ExperimentViewer update num reports")
        if self.num_reports < len(self.report_viewers):
            self.report_viewers = self.reports[0:self.num_reports]
        elif self.num_reports > len(self.report_viewers):
            new_report_viewers = []
            for i in range(len(self.report_viewers), self.num_reports):
                new_report_viewers.append(ReportViewer())
            self.report_viewers = self.report_viewers + new_report_viewers
        # ~ print("ExperimentViewer update num reports end")

    def overall_view(self):
        # ~ print("ExperimentViewer view")
        overall_view = pn.Row()
        for viewer in self.report_viewers:
            col = pn.Column(viewer.viewer_param_view,
                            pn.Row(viewer.report_param_view, viewer.report_data_view))
            overall_view.append(col)
        # ~ print("ExperimentViewer view return")
        return overall_view

    def show(self):
        col = pn.Column(pn.Param(self.param), self.overall_view)
        col.show()
