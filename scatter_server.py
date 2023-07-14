#! /usr/bin/env python3
from scatter import Scatterplot
import panel as pn


plot = Scatterplot()
explanation_string = """
            ### Explanation for entries selection
            To select which configurations you want to compare you can either (1)list them explicitly, 
            (2)or specify two versions (e.g. 'base' and 'v1').
            
            For (1), you need to enter your list into the field 'entries_list' such that each line
            whitespace-separated arguents, which represents one comparison from arg1 on x
            to arg2 on y with legend entry arg3.<br>
            *Example:*<br>
            *lmcut ipdb lmcut-to-ipdb*<br>
            *lmcut hmax lmcut-to-hmax*
            
            For (2), each config containing 'x_entries_substring' is used in one comparison on the x-axis,
            with the y-axis being the config you get when replacing 'x_entries_substring' with 'y_entries_substring.<br>
            If 'y_entries_substring' is empty, it will compare all configs containing 'x_entries_substring' with themselves,
            and if both are empty, then all configs are compared against themselves."""
view = pn.Column(
    pn.Row(plot.param_view, plot.data_view),
    pn.pane.Markdown(explanation_string)
    )
pn.state.location.sync(plot,
    {
        'properties_file': 'properties_file',
        'xattribute' : 'xattribute',
        'yattribute' : 'yattribute',
        'relative': 'relative',
        'xscale': 'xscale',
        'yscale': 'yscale',
        'groupby': 'groupby',
        'fill_alpha': 'fill_alpha',
        'marker_size' : 'marker_size',
        'xsize' : 'xsize',
        'ysize' : 'ysize',
        'replace_zero' : 'replace_zero',
        'autoscale' : 'autoscale',
        'x_range' : 'x_range',
        'y_range' : 'y_range',
        'entries_selection_mode' : 'entries_selection_mode',
        'x_entries_substring' : 'x_entries_substring',
        'y_entries_substring' : 'y_entries_substring',
        'entries_list' : 'entries_list'
    })
view.servable()
