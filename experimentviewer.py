import param
import panel as pn

from scatter import Scatterplot
from experimentdata import ExperimentData

class ExperimentViewer(param.Parameterized):
    num_reports = param.Integer(default=0)
    properties_file = param.String()

    def __init__(self, reports=[], **params):
        print("ExperimentViewer Init")
        super().__init__(**params)
        self.experiment_data = ExperimentData(properties_file=self.properties_file)
        self.reports = []
        for report in reports:
            self.reports.append(pn.widgets.Select(options=[report]))
        self.num_reports = len(self.reports)

    @param.depends('num_reports', watch=True)
    def update_num_reports(self):
        print("ExperimentViewer update num reports")
        if self.num_reports < len(self.reports):
            self.reports = self.reports[0:self.num_reports]
        elif self.num_reports > len(self.reports):
            for i in range(len(self.reports), self.num_reports):
                report_types = [Scatterplot(self.experiment_data, name = "Scatterplot")]
                self.reports.append(pn.widgets.Select(options=report_types))

    @param.depends('properties_file', watch=True)
    def update_properties_file(self):
        print("ExperimentViewer update properties file")
        self.experiment_data = ExperimentData(properties_file=self.properties_file)
        for report in self.reports:
            report.value.update_experiment_data(self.experiment_data)

    def view(self):
        print("ExperimentViewer view")
        reports_view = pn.Row()
        for report in self.reports:
            report_view = pn.Column()
            report_view.append(report)
            report_view.append(pn.Row(report.value.param_view,report.value.data_view))
            reports_view.append(report_view)
        return pn.Column(pn.Param(self.param),reports_view)

    def show(self):
        print("ExperimentViewer show")
        pn.Row(self.view).show()
