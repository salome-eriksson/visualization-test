import param
import panel as pn
import holoviews as hv

class AlgorithmSelector(param.Parameterized):
    config_pairs = param.Dict(default={}, precedence=-1) 
    def __init__(self, algorithms, **params):
        super().__init__(**params)
        self.algorithms = algorithms

    def update_algorithms(self, algorithms):
        self.algorithms = algorithms

    def update_configs(self):
        pass

class AlgorithmSelectorReplace(AlgorithmSelector):
    xalg = param.String(default="")
    yalg = param.String(default="")

    def __init__(self, algorithms, **params):
        super().__init__(algorithms, **params)
        self.update_configs()

    def update_algorithms(self, algorithms):
        super().update_algorithms(algorithms)
        self.update_configs()

    @param.depends('xalg','yalg', watch=True)
    def update_configs(self):
        config_pairs = {}
        if self.xalg == "" and self.yalg == "":
            config_pairs = {x:(x,x) for x in self.algorithms}
        else:
            for alg in self.algorithms:
                if self.xalg in alg:
                    if self.yalg == "":
                        config_pairs[alg] = (alg,alg,)
                    else:
                        alg2 = alg.replace(self.xalg, self.yalg)
                        if alg2 in self.algorithms:
                            config_pairs[alg.replace(self.xalg, "").replace("--","-")] = (alg, alg2)
        self.config_pairs = config_pairs


    def param_view(self):
        return pn.Param(self.param, name="Version based Algorithm Selector")

class AlgorithmSelectorExplicit(AlgorithmSelector):
    num_entries = param.Integer(default=0)

    def __init__(self, algorithms, algorithm_pairs, **params):
        super().__init__(algorithms, **params)
        self.widgets = []
        self.num_entries = len(algorithm_pairs)
        self.algorithm_pairs = algorithm_pairs
        self.update_gui()
        i = 0
        for (name, (xalg, yalg)) in algorithm_pairs.items():
          self.widgets[i][0].value = xalg
          self.widgets[i][1].value = yalg
          self.widgets[i][2].value = name
          i+=1

    def update_algorithms(self, algorithms):
        super().update_algorithms(algorithms)
        for (xalg,yalg,name) in self.widgets:
            xalg.options = self.algorithms
            yalg.options = self.algorithms
        self.update_algorithm_pairs()

    def update_algorithm_pairs(self, *events):
        self.algorithm_pairs = {name.value: (xalg.value, yalg.value) for (xalg, yalg, name) in self.widgets}

        
    @param.depends('num_entries', watch=True)
    def update_gui(self):
        self.widgets = self.widgets[0:self.num_entries]
        for i in range(len(self.widgets),self.num_entries):
            xalg = pn.widgets.Select(options = self.algorithms, width=140)
            xalg.param.watch(self.update_algorithm_pairs, ['value'])
            yalg = pn.widgets.Select(options = self.algorithms, width=140)
            yalg.param.watch(self.update_algorithm_pairs, ['value'])
            name = pn.widgets.TextInput(value = f"entry {i+1}", width=140)
            name.param.watch(self.update_algorithm_pairs, ['value'])
            self.widgets.append((xalg, yalg, name))
        self.update_algorithm_pairs(None)

    def param_view(self):
        column = pn.Column(pn.Param(self.param, name="Explicit Algorithm Selector"))
        column.append(pn.Row(pn.pane.Markdown("   x algorithm", width=150),
                             pn.pane.Markdown("   y algorithm", width=150),
                             pn.pane.Markdown("   name", width=150)))
        for (xalg,yalg,name) in self.widgets:
            column.append(pn.Row(xalg, yalg, name))
        return column
