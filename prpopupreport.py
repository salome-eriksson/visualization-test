import logging
import panel as pn

from report import Report
from problemtable import ProblemTablereport


# adds functionality for creating popup ProblemTablereports
class PRPopupReport(Report):
    def __init__(self, experiment_data, **params):
        super().__init__(experiment_data, **params)
        self.data_view_column = pn.Column(self.data_view, pn.Column(height=0, width=0), sizing_mode='stretch_both', scroll=True)


    def view_data(self):
        try:
            self.update_data_view()
            self.data_view_column[0] = self.data_view
            return self.data_view_column
        except Exception as ex:
            self.logger.exception('Got exception on main handler')
            raise

    def add_problem_report_popup(self, domain, problem, algorithms):
        param_dict = {
            "domain" : domain,
            "problem": problem,
            "algorithms": algorithms
        }
        problem_report = ProblemTablereport(self.experiment_data, param_dict,
            sizing_mode = "stretch_width")
        self.data_view_column[1].append(pn.layout.FloatPanel(
            problem_report.view_data, name = f"{domain} - {problem}",
            contained = False, height = 750, width = 750, position = "center",
            config = {"closeOnEscape" : True}
        ))


    def deactivate(self):
        self.data_view_column[1].clear()
