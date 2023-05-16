import param
import panel as pn
import copy

from scatter import Scatterplot
from table import Tablereport

class ReportViewer(param.Parameterized):
    report=param.Selector()

    def __init__(self, **params):
        super().__init__(**params)
        self.param.report.objects = [Scatterplot(name = "Scatterplot"),Tablereport(name = "Tablereport")]
        self.report = self.param.report.objects[1]

    def view(self):
        if self.report is not None:
            return pn.Column(pn.Param(self.param, name="", expand_button=False), self.report.view);
        

class ExperimentViewer(param.Parameterized):
    num_reports = param.Integer(default=0)
    reports = param.List(precedence=-1)

    def __init__(self, reports=[ReportViewer()], **params):
        # ~ print("ExperimentViewer Init")
        super().__init__(**params)
        self.reports = reports
        self.num_reports = len(self.reports)
        # ~ print("ExperimentViewer Init end")

    @param.depends('num_reports', watch=True)
    def update_num_reports(self):
        # ~ print("ExperimentViewer update num reports")
        if self.num_reports < len(self.reports):
            self.reports = self.reports[0:self.num_reports]
        elif self.num_reports > len(self.reports):
            for i in range(len(self.reports), self.num_reports):
                self.reports.append(ReportViewer())
        # ~ print("ExperimentViewer update num reports end")

    def view(self):
        # ~ print("ExperimentViewer view")
        reports_view = pn.Row()
        for report in self.reports:
            reports_view.append(report.view)
        # ~ print("ExperimentViewer view return")
        return pn.Column(pn.Param(self.param),reports_view)

    def show(self):
        # ~ print("ExperimentViewer show")
        pn.Row(self.view).show()
