import math
import numpy as np
import param
import pandas as pd
import panel as pn
import bokeh


pn.extension('tabulator')

def style_table_by_row(x):
    is_aggregate = (x['problem'] == "")
    numeric_values = pd.to_numeric(x,errors='coerce')
    min_val = numeric_values.dropna().min()
    max_val = numeric_values.dropna().max()
    min_equal_max = max_val - min_val == 0
    retarray = []
    for elem in numeric_values:
        formatting_string = ""
        if not min_equal_max != 0 and pd.notna(elem):
            val = ((elem - min_val) / (max_val-min_val)*255).astype(int)
            formatting_string = "color: #00{:02x}{:02x};".format(val,255-val)
        if is_aggregate:
            formatting_string += "background-color: #d1d1e0;"
        retarray.append(formatting_string)
    return retarray
    
def filter_by_active_domains(x, active_domains):
    return x[x["domain"].isin(active_domains) | x["problem"].isin([""])]




arrays = [
    np.array(["bar", "bar", "baz", "baz", "foo", "foo", "qux", "qux"]),
    np.array(["one", "two", "one", "two", "one", "two", "one", "two"]),
]

domains = ["bar", "baz", "foo", "qux"]
active_domains = []

#aggregate over domain
df = pd.DataFrame(np.random.randn(8, 4), index=arrays)
df = df.rename_axis(['domain', 'problem'])
df2 = df.groupby(level=0).agg('sum')
df2['problem'] = ""
df2 = df2.set_index('problem',append=True)
df = pd.concat([df,df2]).sort_index()
df = df.reset_index(['domain', 'problem'])




view = pn.widgets.Tabulator(df, show_index=False, disabled = True)
# ~ view.add_filter(pn.bind(filter_by_active_domains,active_domains=active_domains))
def callback(e):
    domain = df.iloc[e.row]["domain"]
    if df.iloc[e.row]["problem"] != "":
        return
    if domain in active_domains:
        active_domains.remove(domain)
    else:
        active_domains.append(domain)
    view.add_filter(pn.bind(filter_by_active_domains,active_domains=active_domains))
    view.style.apply(func=style_table_by_row, axis=1)
    
view.add_filter(pn.bind(filter_by_active_domains,active_domains=active_domains))
# ~ view.style.apply(func=style_table_by_row, axis=1)
view.on_click(callback)
view.show()
