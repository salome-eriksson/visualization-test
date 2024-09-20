import param
import panel as pn

from experimentdata import ExperimentData

class Report(param.Parameterized):
    def __init__(self, experiment_data = ExperimentData(), param_dict = dict(), **params):
        super().__init__(**params)
        self.experiment_data = experiment_data
        self.param_view = pn.pane.Str("Placeholder Param View")
        self.data_view = pn.pane.Str("Placeholder Data View")


    def update_experiment_data(self, new_data):
        self.experiment_data = new_data
        param_updates = self.set_experiment_data_dependent_parameters()
        self.param.update(param_updates)

    def update_algorithm_names(self, mapping):
        pass


    # Returns a dictionary of parameters and values they should be set to
    # This dicitionary is batch updated in update_experiment_data.
    def set_experiment_data_dependent_parameters(self):
        return dict()


    def view_param(self):
        self.update_param_view()
        return self.param_view


    def view_data(self):
        self.update_data_view()
        return self.data_view


    # updates self.param_view
    def update_param_view(self):
        pass


    # updates self.data_view
    def update_data_view(self):
        pass


    # used by ReportWithPopup to remove the Problemtablereports
    def deactivate(self):
        pass


    def get_params_as_dict(self):
        d = { name : val for name, val in self.param.get_param_values()
            if val != self.param.params()[name].default }
        d.pop("name")
        return d


    def set_params_from_dict(self,params):
        pass
