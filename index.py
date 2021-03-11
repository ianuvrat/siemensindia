from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html

from app import app, server, dbc
from tabs import intro, alert, projection, report

style = {'maxWidth': '960px', 'margin': 'auto'}

app.layout = dbc.Container([
    dcc.Markdown('# SIEMENS INDIA',
                 className="text-center font-weight-normal text-primary"),
    dcc.Tabs(id='tabs', value='tab-intro', children=[
        dcc.Tab(label='Advance Vendor Payment Alert', value='tab-alert'),
        dcc.Tab(label='Reports', value='tab-report'),
        dcc.Tab(label='Inventory Projection', value='tab-projection'),

    ]),
    html.Div(id='tabs-content')
],fluid=True)

@app.callback(Output('tabs-content', 'children'),
              [Input('tabs', 'value')])
def render_content(tab):
    if tab == 'tab-intro': return intro.layout
    elif tab == 'tab-alert': return alert.layout
    elif tab == 'tab-report':return report.layout
    elif tab == 'tab-projection': return projection.layout


#--------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)