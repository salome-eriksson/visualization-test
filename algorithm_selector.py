import param
import panel as pn
import holoviews as hv

class AlgorithmSelector(param.Parameterized):
    #Each entry is a tuple (xalg, yalg, name)
    algorithm_pairs = param.List(default=[], precedence=-1) 
    def __init__(self, algorithms, **params):
        # ~ print("Algorithm Selector init")
        super().__init__(**params)
        self.algorithms = algorithms
        # ~ print("Algorithm Selector init end")

    def update_algorithms(self, algorithms):
        # ~ print("Algorithm Selector update algorithms")
        self.algorithms = algorithms             
        # ~ print("Algorithm Selector update algorithms end")


class AlgorithmSelectorReplace(AlgorithmSelector):
    xalg = param.String(default="")
    yalg = param.String(default="")

    def __init__(self, algorithms, **params):
        # ~ print("Algorithm Selector Replace init")
        super().__init__(algorithms, **params)
        self.update_algorithm_pairs()
        # ~ print("Algorithm Selector Replace init end")

    def update_algorithms(self, algorithms):
        # ~ print("Algorithm Selector Replace update algorithms")
        super().update_algorithms(algorithms)
        self.update_algorithm_pairs()
        # ~ print("Algorithm Selector Replace update algorithms end")

    @param.depends('xalg','yalg', watch=True)
    def update_algorithm_pairs(self):
        # ~ print("Algorithm Selector Replace update algorithm pairs")
        algorithm_pairs = []
        if self.xalg == "" and self.yalg == "":
            algorithm_pairs = [(x,x,x) for x in self.algorithms]
        else:
            for alg in self.algorithms:
                # ~ print(alg)
                if self.xalg in alg:
                    if self.yalg == "":
                        algorithm_pairs.append((alg, alg, alg))
                    else:
                        alg2 = alg.replace(self.xalg, self.yalg)
                        if alg2 in self.algorithms:
                            algorithm_pairs.append((alg, alg2, alg.replace(self.xalg, "")))
        # ~ print("updating algorithm pairs")
        self.algorithm_pairs = algorithm_pairs
        # ~ print("Algorithm Selector Replace update algorithm pairs end")

    @param.depends()
    def param_view(self):
        # ~ print("Algorithm Selector Replace param view")
        retparam = pn.Param(self.param, name="Version based Algorithm Selector")
        # ~ print("Algorithm Selector Replace param view (return)")
        return retparam

class AlgorithmSelectorExplicit(AlgorithmSelector):
    num_entries = param.Integer(default=0)

    def __init__(self, algorithms, algorithm_pairs, **params):
        # ~ print("Algorithm Selector Explicit init")
        super().__init__(algorithms, **params)
        self.widgets = []
        self.algorithm_pairs = algorithm_pairs
        for (x, y, n) in algorithm_pairs:
            xalg = pn.widgets.Select(options = self.algorithms, value = x, width=140)
            xalg.param.watch(self.update_algorithm_pairs, ['value'])
            yalg = pn.widgets.Select(options = self.algorithms, value = y, width=140)
            yalg.param.watch(self.update_algorithm_pairs, ['value'])
            name = pn.widgets.TextInput(value = n, width=140)
            name.param.watch(self.update_algorithm_pairs, ['value'])
            self.widgets.append((xalg, yalg, name))
        self.num_entries = len(algorithm_pairs) #this will trigger update_gui if algorithm pairs are given
        # ~ print("Algorithm Selector Explicit init end")

    
    def update_algorithms(self, algorithms):
        # ~ print("Algorithm Selector Explicit update algorithms")
        super().update_algorithms(algorithms)
        for (xalg,yalg,name) in self.widgets:
            xalg.options = self.algorithms
            yalg.options = self.algorithms
        self.update_algorithm_pairs()
        # ~ print("Algorithm Selector Explicit update algorithms end")

    def update_algorithm_pairs(self, *events):
        # ~ print("Algorithm Selector Explicit update algorithm pairs")
        self.algorithm_pairs = [(xalg.value, yalg.value, name.value) for (xalg, yalg, name) in self.widgets]
        # ~ print("Algorithm Selector Explicit update algorithm pairs end")

        
    @param.depends('num_entries', watch=True)
    def update_gui(self):
        # ~ print("Algorithm Selector Explicit update gui")
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
        # ~ print("Algorithm Selector Explicit update gui end")

    @param.depends('num_entries')
    def param_view(self):
        # ~ print("Algorithm Selector Explicit param view")
        column = pn.Column(pn.Param(self.param, name="Explicit Algorithm Selector"))
        column.append(pn.Row(pn.pane.Markdown("   x algorithm", width=150),
                             pn.pane.Markdown("   y algorithm", width=150),
                             pn.pane.Markdown("   name", width=150)))
        for (xalg,yalg,name) in self.widgets:
            column.append(pn.Row(xalg, yalg, name))
        # ~ print("Algorithm Selector Explicit param view return")
        return column
