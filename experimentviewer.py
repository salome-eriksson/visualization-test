import param
import panel as pn

from scatter import Scatterplot
from table import Tablereport

class ExperimentViewer(param.Parameterized):
    num_reports = param.Integer(default=0)

    def __init__(self, reports=[], **params):
        # ~ print("ExperimentViewer Init")
        super().__init__(**params)
        self.reports = []
        for report in reports:
            self.reports.append(pn.widgets.Select(options=[report]))
        self.num_reports = len(self.reports)
        # ~ print("ExperimentViewer Init end")

    @param.depends('num_reports', watch=True)
    def update_num_reports(self):
        # ~ print("ExperimentViewer update num reports")
        if self.num_reports < len(self.reports):
            self.reports = self.reports[0:self.num_reports]
        elif self.num_reports > len(self.reports):
            for i in range(len(self.reports), self.num_reports):
                report_types = [Scatterplot(name = "Scatterplot"),Tablereport(name = "Tablereport")]
                self.reports.append(pn.widgets.Select(options=report_types))
        # ~ print("ExperimentViewer update num reports end")

    def view(self):
        # ~ print("ExperimentViewer view")
        reports_view = pn.Row()
        for report in self.reports:
            reports_view.append(pn.Column(report, report.value.view))
        # ~ print("ExperimentViewer view return")
        return pn.Column(pn.Param(self.param),reports_view)

    def show(self):
        # ~ print("ExperimentViewer show")
        pn.Row(self.view).show()
