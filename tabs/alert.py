import base64
import datetime
import io
import plotly.graph_objs as go
import cufflinks as cf
import dash
import plotly.express as px
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import pathlib
import pandas as pd
import numpy as np
from datetime import date, timedelta
import dash_auth
import dash_bootstrap_components as dbc
import dash_extensions as de

from app import app

# ____________________________________________

# get relative data folder
# PATH = pathlib.Path(__file__).parent
# DATA_PATH = PATH.joinpath("../Siemens Purchase Alert/data").resolve()
# df = pd.read_csv(DATA_PATH.joinpath("data1.csv"),parse_dates=['Date','Del/finish'])
# __________
# #Alert Date
# df['Payment Alert date'] = df['Date']-timedelta(60)
# print(df.info())
# print(df.head())

# ---------------------------------------------------------------------------------------

colors = {"graphBackground": "#F5F5F5", "background": "#ffffff", "text": "#000000"}

url = "https://assets10.lottiefiles.com/private_files/lf30_qcellpy3.json"
options = dict(loop=True, autoplay=True, rendererSettings=dict(preserveAspectRatio='xMidYMid slice'))

vendor = ['50053549',
          '50047177',
          '50052844',
          '50053896',
          '50054302',
          '50057062',
          '50057462',
          '50060106',
          '50064523',
          '50070756',
          '50075828',
          '50076936',
          '50080876',
          '50081495',
          '50175725',
          '50205300',
          '50222365',
          '50239285',
          ]
# ---------------------------------------------------------------------------------------
layout = dbc.Container([

    # 1
    dbc.Row([
        dbc.Col([
            dcc.Markdown(""" ### 
ADVANCE PAYMENT TRACKER""",
                         className="text-center font-weight-normal text-danger font-weight-bold"),
        ]),
    ]),

    # 2 Animation lottie
    html.Div(de.Lottie(options=options, width="10%", height="5%", url=url)),

    # 3 Upload button
    dbc.Row([
        dbc.Col([
            dcc.Upload(
                id="upload-data",
                children=html.Div(["Drag and Drop or ", html.A("Select Files")]),
                style={
                    "width": "100%",
                    "height": "60px",
                    "lineHeight": "60px",
                    "borderWidth": "1px",
                    "borderStyle": "dashed",
                    "borderRadius": "5px",
                    "textAlign": "center",
                    "margin": "10px",
                },
                # Allow multiple files to be uploaded
                multiple=True,
            )
        ], className="text-left", width={'size': 2, 'offset': 0, 'order': 1}),

    ]),


    # 4 Priority Info
    dbc.Row([
        dbc.Col([
            dcc.Markdown("""
                            ⭐⭐⭐ = Next 15 days

                            ⭐⭐ = Next 15-30 Days

                            ⭐ = After 30 Days""")
            # className="text-center font-weight-normal text-primary"),
        ], className="text-left font-weight-bold text-primary border", width={'size': 2, 'offset': 9, 'order': 0}),

        dbc.Col([
            dcc.Markdown("""-----------------------------
                BPO APPROVALS ------> CORP. APPROVALS ------> ACTUAL PAYMENT ------> TRANSIT TIME ------> GRN OPERATION ------ Delivery
                               15days                  10days                 15days               15days                5days""")
        

            # className="text-center font-weight-normal text-primary"),
        ], className="text-left font-weight-bold text-primary bg-secondary", width={'size': 9, 'offset': 2, 'order': 0})
    ]),


    # 5  Dash datatable
    dcc.Loading(children=[html.Div(id="output-data-upload", style={'width': '200vh', 'height': '80vh'})],
                color="#119DFF", type="cube", fullscreen=True),

    html.Br(),

    # 6  Inspect Vendor
    dbc.Row([
            dbc.Col([
                dcc.Markdown(""" ### 
    INSPECT VENDOR""",
                             className="text-center font-weight-normal text-primary font-weight-bold"),
            ]),
        ]),

    # 7 Parent-Child dpdn
    dbc.Row([
        dbc.Col([
            html.Label("Vendor:", style={'fontSize': 30, 'textAlign': 'center'}),
            dcc.Dropdown(
                id='vendor-dpdn',
                # options=[{'label': 50053549, 'value': 50053549}],
                options=[{'label': s, 'value': s} for s in sorted(vendor)],
                value='50053549',
                clearable=True,
                multi=False,
                searchable=True,  # allow user-searching of dropdown values
                search_value='',  # remembers the value searched in dropdown
                placeholder='Choose a Vendor ',  # gray, default text shown when no option is selected
                persistence=True,  # remembers dropdown value. Used with persistence_type
                persistence_type='local'  # remembers dropdown value selected until...
                # 'memory': browser tab is refreshed
                # 'session': browser tab is closed
                # 'local': browser cookies are deleted
            ),

        ], className="text-left", width={'size': 3, 'offset': 0, 'order': 1}),

        dbc.Col([
            html.Label("Materials:", style={'fontSize': 30, 'textAlign': 'center'}),
            dcc.Dropdown(id='materials-dpdn', options=[], multi=True,
                         placeholder='Material will automatically populate based on selected vendor', ),
        ], className="text-left", width={'size': 4, 'offset': 4, 'order': 2}),

    ]),

    # 8 Vendor Name display
    dbc.Row([
        dbc.Col([
            html.Div(id='vendor-name'),
        ], className="text-left font-weight-bold text-primary", width={'size': 4, 'offset': 0, 'order': 0}),
    ]),



    # 9 graph
    dcc.Loading(children=[dcc.Graph(id='Mygraph', style={'width': '200vh', 'height': '100vh'})], color="#119DFF",
                type="cube", fullscreen=False),

], fluid=True
)


# ---------------------------------------------------------------------------------------

# Populate the OPTIONS of children dropdown based on parent dropdown
@app.callback(
    [Output('materials-dpdn', 'options'),
     Output("vendor-name", "children")],

    [Input("upload-data", "contents"),
     Input("upload-data", "filename"),
     Input('vendor-dpdn', 'value')])
def set_material_options(contents, filename, chosen_vendor):
    if contents is None or filename is None:  # Prevent callback trigger when not needed #
        raise PreventUpdate
    elif contents:
        contents = contents[0]
        filename = filename[0]
        df = parse_data(contents, filename)

        dff = df[df.Vendor == chosen_vendor]
        vendor_name = dff.loc[df.Vendor == chosen_vendor, 'Vendor2'].iloc[0]

    return [{'label': c, 'value': c} for c in sorted(dff.Material.unique())], 'VENDOR: {}'.format(vendor_name)


# Populate initial values of children dropdown
@app.callback(
    Output('materials-dpdn', 'value'),
    Input('materials-dpdn', 'options'))
def set_material_value(available_options):
    return [x['value'] for x in available_options]


# ---------------------------------------------------------------------------------------

##1 Parse data into df
def parse_data(contents, filename):
    content_type, content_string = contents.split(",")

    decoded = base64.b64decode(content_string)
    try:
        if "csv" in filename:
            # Assume that the user uploaded a CSV or TXT file
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")), parse_dates=['Date', 'Del/finish'])

            tdelta = datetime.timedelta(days=60)  # time_delta (2 months)

            df['today'] = datetime.date.today()  # today
            df['today'] = pd.to_datetime(df['today'])

            df['Payment Alert date'] = df['Date'] - tdelta  # alert Date
            df['BPO Approvals'] = df['Payment Alert date'] + datetime.timedelta(days=15)
            df['Corp. Approvals'] = df['BPO Approvals'] + datetime.timedelta(days=10)
            df['Actual Payment Date'] = df['Corp. Approvals'] + datetime.timedelta(days=15)

            df['Days to Alert'] = df['Payment Alert date'] - df['today']  # days to alert
            df['Days to Alert'] = (df['Days to Alert'] / np.timedelta64(1, 'D')).astype(int)

            df['Prioritize'] = df['Days to Alert'].apply(lambda x:

                                                         ' Alert date is passed' if x < 0
                                                         else (
                                                             '⭐⭐⭐' if x >= 0 and x < 15
                                                             else (
                                                                 '⭐⭐' if x >= 15 and x < 30
                                                                 else (
                                                                     '⭐' if x >= 30
                                                                     else (' Alert is not appicaple')
                                                                 )))
                                                         )

            for x in ["Date", "Del/finish", "today", "Payment Alert date", "BPO Approvals", "Corp. Approvals", "Actual Payment Date"]:
                if x in df.columns:
                    df[x] = pd.DatetimeIndex(df[x]).strftime("%Y-%m-%d")

            df['Vendor'] = df['Vendor'].astype(str)

            # print(df.info())
            # print(df.head())

        elif "xls" in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded), parse_dates=['Date', 'Del/finish'])


        elif "txt" or "tsv" in filename:
            # Assume that the user upl, delimiter = r'\s+'oaded an excel file
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")), delimiter=r"\s+", parse_dates=['Date', 'Del/finish'])
            df = pd.read_excel(io.BytesIO(decoded), parse_dates=['Date', 'Del/finish'])

    except Exception as e:
        print(e)
        return html.Div(["There was an error processing this file."])

    return df


# ---------------------------------------------------------------------------------------

# Datatable callback
@app.callback(
    Output("output-data-upload", "children"),
    [Input("upload-data", "contents"),
     Input("upload-data", "filename")],
)
# Update datable
def update_table(contents, filename):
    table = html.Div()

    if contents:
        contents = contents[0]
        filename = filename[0]
        df = parse_data(contents, filename)  # calling parse_data to update dash table

        table = html.Div(
            [
                html.H5(filename),
                dash_table.DataTable(

                    id='datatable_id',
                    data=df.to_dict("records"),
                    columns=[
                        {'name': 'Material', 'id': 'Material', 'type': 'text', 'editable': False, 'selectable': True},
                        # {'name': 'Plus/minus', 'id': 'Plus/minus', 'type': 'text', 'editable': False, "hideable": True,
                        #  "deletable": True, 'selectable': True},
                        {'name': 'MRP elemnt', 'id': 'MRP elemnt', 'type': 'text', 'editable': False, "hideable": True,
                         'selectable': True},
                        {'name': 'MRP element data', 'id': 'MRP element data', 'type': 'text', 'editable': False,
                         "hideable": True, 'selectable': True},
                        {'name': 'Vendor', 'id': 'Vendor', 'type': 'text', 'editable': False, "hideable": True,
                         'selectable': True},
                        {'name': 'Vendor2', 'id': 'Vendor2', 'type': 'text', 'editable': False, "hideable": True,
                         'selectable': True},
                        {'name': 'MRPCn', 'id': 'MRPCn', 'type': 'text', 'editable': False, 'selectable': True},
                        {'name': 'Product', 'id': 'Product', 'type': 'text', 'editable': False, 'selectable': True},
                        {'name': 'PGr', 'id': 'PGr', 'type': 'text', 'editable': False, 'selectable': True},
                        # {'name': 'today', 'id': 'today', 'type': 'datetime', 'editable': False, "hideable": True,
                        #  "deletable": True, 'selectable': True},
                        {'name': 'Payment Alert date', 'id': 'Payment Alert date', 'type': 'datetime',
                         'editable': False, 'selectable': True},
                        {'name': 'Days to Alert', 'id': 'Days to Alert', 'type': 'numeric', 'editable': False,
                         'selectable': True},
                        {'name': 'BPO Approvals', 'id': 'BPO Approvals', 'type': 'datetime', 'editable': False,
                         'selectable': True},
                        {'name': 'Corp. Approvals', 'id': 'Corp. Approvals', 'type': 'datetime', 'editable': False,
                         'selectable': True},
                        {'name': 'Actual Payment Date', 'id': 'Actual Payment Date', 'type': 'datetime', 'editable': False,
                         'selectable': True},
                        {'name': 'Delivery Date', 'id': 'Date', 'type': 'datetime', 'editable': False,
                         'selectable': True},
                        # {'name': 'Del/finish', 'id': 'Del/finish', 'type': 'datetime', 'editable': False,
                        #  'selectable': True},
                        {'name': 'Prioritize', 'id': 'Prioritize', 'type': 'text', 'editable': False,
                         'selectable': True},

                    ],

                    tooltip_delay=0,  # 1000
                    tooltip_duration=None,  # 2000
                    # column headers
                    tooltip_header={
                        'Date': 'Delivery Date',
                        'PGr': 'Purchasing Group',
                        'Vendor': 'Vendor Code',
                        'Vendor2': 'Vendor Name',
                        'Days to Alert': '▲ = Ascending, ▼ = Descending',
                    },

                    editable=True,  # allow editing of data inside all cells
                    filter_action="native",  # allow filtering of data by user ('native') or not ('none')
                    sort_action="native",  # enables data to be sorted per-column by user or not ('none')
                    sort_mode="multi",  # sort across 'multi' or 'single' columns
                    column_selectable="multi",  # allow users to select 'multi' or 'single' columns
                    row_selectable="multi",  # allow users to select 'multi' or 'single' rows
                    row_deletable=False,  # choose if user can delete a row (True) or not (False)
                    selected_columns=[],  # ids of columns that user selects
                    selected_rows=[],  # indices of rows that user selects
                    page_action='native',
                    style_cell={'whiteSpace': 'normal', 'minWidth': 95, 'maxWidth': 95, 'width': 95},
                    fixed_rows={'headers': True, 'data': 0},
                    virtualization=False,
                    export_columns='all',  # 'all' or 'visible
                    export_format='xlsx',  # 'csv or 'none' or 'xlsx'

                    style_data_conditional=([

                        # 'filter_query', 'column_id', 'column_type', 'row_index', 'state', 'column_editable'.
                        # filter_query ****************************************

                        {
                            'if': {
                                'filter_query': '{Days to Alert} < 0',
                                'column_id': 'Days to Alert'
                            },
                            # 'backgroundColor': 'hotpink',
                            'color': 'red'
                        },

                        {
                            'if': {
                                'filter_query': '{MRP elemnt} = ShpgNt',
                                'column_id': 'MRP elemnt'
                            },
                            # 'backgroundColor': 'hotpink',
                            'color': 'blue'
                        },
                        {
                            'if': {
                                'filter_query': '{MRP elemnt} = PurRqs',
                                'column_id': 'MRP elemnt'
                            },
                            # 'backgroundColor': 'hotpink',
                            'color': 'red'
                        },
                        {
                            'if': {
                                'filter_query': '{MRP elemnt} = POitem',
                                'column_id': 'MRP elemnt'
                            },
                            # 'backgroundColor': 'hotpink',
                            'color': 'green'
                        },

                    ])
                ),

                html.Hr(),
                # html.Div("Raw Content"),
                # html.Pre(
                #     contents[0:200] + "...",
                #     style={"whiteSpace": "pre-wrap", "wordBreak": "break-all"},
                # ),
            ]
        )

        return table


# ---------------------------------------------------------------------------------------

# graph callback
@app.callback(
    Output("Mygraph", "figure"),

    [Input("upload-data", "contents"),
     Input("upload-data", "filename"),
     Input('materials-dpdn', 'value'),
     Input('vendor-dpdn', 'value')
     ],
)
# graph update
def update_graph(contents, filename, selected_materials, selected_vendor):
    if contents is None or filename is None:
        raise PreventUpdate

    elif contents:
        contents = contents[0]
        filename = filename[0]
        df = parse_data(contents, filename)  # calling parse_data to update dash table

        if len(selected_vendor) == 0:
            return dash.no_update
        else:
            print(df.head())
            print(df.shape)
            dff = df[(df.Vendor == selected_vendor) ]
            print(dff.shape)
            gantt_chrt = px.timeline(dff,
                                     x_start="Payment Alert date", x_end="Date",
                                     y="MRP element data",
                                     color="MRP elemnt",
                                     title="Gantt Chart for Vendor Code: {}".format(selected_vendor),
                                     text='Material')
            gantt_chrt.update_yaxes(autorange="reversed")  # otherwise tasks are listed from the bottom up
            gantt_chrt.update_layout(xaxis={'categoryorder': 'total ascending'},
                              title={'xanchor': 'center', 'yanchor': 'top', 'y': 0.9, 'x': 0.5, })

    return (gantt_chrt)
# ---------------------------------------------------------------------------------------


# if __name__ == "__main__":
#     app.run_server(debug=True)
