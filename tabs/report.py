import pandas as pd
import numpy as np
import datetime

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

from app import app, dbc
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
colors = {"graphBackground": "#F5F5F5", "background": "#ffffff", "text": "#000000"}
layout =  dbc.Container([

        #1 PAGE TITLE
        dbc.Row([
                dbc.Col([
                    dcc.Markdown(""" ### 
        CONSOLIDATED REPORTS (CURRENT MONTH)""",
                                 className="text-center font-weight-normal text-danger font-weight-bold"),
                ]),
            ]),

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


        #2 Dropdown + Display
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(
                    id='report-dpdn',
                    multi=True,
                    searchable=False,
                    clearable=False,
                    disabled=True,
                    options=[
                        {'label': 'All Reports', 'value': 'excess'},
                        # {'label': 'Shortfall Report', 'value': 'short'},
                        # {'label': 'Match Report', 'value': 'match'}
                            ],
                    value='excess'
                           ),
                ],className="text-left font-weight-bold text-danger ", width={'size': 2, 'offset': 0, 'order': 0}),

            dbc.Col([
                html.Div(id='excess_info'),
            ], className="text-left font-weight-bold text-success border", width={'size': 2, 'offset': 0, 'order': 0}),

            dbc.Col([
                html.Div(id='short_info'),
            ], className="text-left font-weight-bold text-primary border", width={'size': 2, 'offset': 0, 'order': 0}),

            dbc.Col([
                html.Div(id='met_info'),
            ], className="text-left font-weight-bold text-danger border", width={'size': 2, 'offset': 0, 'order': 0}),
        ]),


        #3 DASH DATATABLE
        dcc.Loading(children=[html.Div(id="datatable_id1", style={'width': '200vh', 'height': '80vh'})],
                                        color="#119DFF", type="cube", fullscreen=False),

        dcc.Loading(children=[html.Div(id="datatable_id2", style={'width': '200vh', 'height': '80vh'})],
                                        color="#119DFF", type="cube", fullscreen=False),

        dcc.Loading(children=[html.Div(id="datatable_id3", style={'width': '200vh', 'height': '80vh'})],
                                        color="#119DFF", type="cube", fullscreen=False),

        ], fluid=True)

# ---------------------------------------------------------------------------------------

#parse data into df
def parse_data(contents, filename):
    content_type, content_string = contents.split(",")

    decoded = base64.b64decode(content_string)
    try:
        if "csv" in filename:
            # Assume that the user uploaded a CSV or TXT file
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
            # Handling null
            df = df.fillna(0)
            # Dropping blanks rows
            df = df.drop(df[df['Material'] == 0].index)
            # Excluding repetions
            df = df[df['MRP segmt'] == 2]
            # Dropping unwanted columns
            df.drop(df.columns[[1, 3, 5, 8, 15]], axis=1, inplace=True)
            # Renaming cols
            df.rename(columns={'      Rec./reqd qty': 'Rec./reqd qty',
                               '         Avail. qty': 'Avail. qty'}, inplace=True)
            # material list
            material_list = []
            for m in df['Material'].unique():
                material_list.append(m)
            # Formatting dates
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
            df['Resch.date'] = pd.to_datetime(df['Resch.date'])

            # Adding cols
            df['month'] = df['Date'].dt.month
            df['year'] = df['Date'].dt.year
            df['month_year'] = pd.to_datetime(df[['year', 'month']].assign(DAY=1))

            # ----------------------------------------------------
            df_short = pd.DataFrame([])
            df_met = pd.DataFrame([])
            df_excess = pd.DataFrame([])

            gbl = globals()

            for mat in material_list:

                dff = df[df['Material'] == mat]
                # current month
                cur_month = dff.loc[dff['Plus/minus'] == 'B', 'month_year'].iloc[0]
                # Current month dff
                dff = dff[dff['month_year'] <= cur_month]
                # Dropping PO history
                i = dff[((dff['Plus/minus'] == '+') & (dff['month_year'] < cur_month))].index
                dff = dff.drop(i)
                # PO df
                po_dff = dff[dff['Plus/minus'] == '+']
                # Available Stock
                stock = dff.loc[dff['Plus/minus'] == 'B', 'Rec./reqd qty'].iloc[0]
                # price
                price = dff.loc[dff['Plus/minus'] == 'B', 'price'].iloc[0]
                # Exception Code
                exp = dff['Exc.'].max()


                # PO df
                po_dff = dff[dff['Plus/minus'] == '+']
                # PO count
                po_count = len(po_dff)

                # concatenating PO no.
                po_list = []
                for p in po_dff['MRP element data']:
                    po_list.append(p)

                po_no = " , ".join(po_list)

                # concatenating Vendor code
                vendor_list = []
                for v in po_dff['Vendor']:
                    vendor_list.append(str(v))

                vendors = " , ".join(vendor_list)



                # Calculate monthly demand
                demand = []

                for req in dff['Rec./reqd qty']:
                    if req < 0:
                        demand.append(req)

                # Monthly Demand and Remaining stock
                tot_demand = round(sum(demand))
                diff = round(tot_demand + stock)
                amount = round((diff * price), 2)

                # ------------------------------------
                # If no PO
                if po_dff.empty:
                    data = {'Material': [mat],
                            'Price': [price],
                            'Stock': [stock],
                            'Demand': [tot_demand],
                            'Difference': [diff],
                            'Amount': [amount],
                            'Purchase Order': ['no'],
                            'Total Purchase Orders': [po_count],
                            'Purchase Order No.': [po_no],
                            'Vendor Code': [vendors],
                            }
                else:
                    data = {'Material': [mat],
                            'Price': [price],
                            'Stock': [stock],
                            'Demand': [tot_demand],
                            'Difference': [diff],
                            'Amount': [amount],
                            'Purchase Order': ['yes'],
                            'Total Purchase Orders': [po_count],
                            'Purchase Order No.': [po_no],
                            'Vendor Code': [vendors],
                            }

                temp = pd.DataFrame(data)

                # ------------------------------------
                # Appending records in consolidated df
                if diff > 0:
                    df_excess = df_excess.append(temp)
                elif diff < 0:
                    df_short = df_short.append(temp)
                elif diff == 0:
                    df_met = df_met.append(temp)

                # ------------------------------------
                # Creating individual df_xxxxxxx
                gbl['df_' + mat] = dff
        elif "xls" in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
        elif "txt" or "tsv" in filename:
            # Assume that the user upl, delimiter = r'\s+'oaded an excel file
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")), delimiter=r"\s+")


    except Exception as e:
        print(e)
        return html.Div(["There was an error processing this file."])

    return df_excess, df_short, df_met
#---------------------------------------------------------------------------------------



# Datatable callback
@app.callback(
    [Output("datatable_id1", "children"),
     Output("datatable_id2", "children"),
     Output("datatable_id3", "children"),
     Output('excess_info', 'children'),
     Output('short_info', 'children'),
     Output('met_info', 'children')],

     [Input("upload-data", "contents"),
     Input("upload-data", "filename"),
     Input('report-dpdn', 'value')],
    # [Input("upload-data", "contents"),
    #  Input("upload-data", "filename")],
)
# Update datable
def update_table(contents, filename, chsn_val):

    if contents is None or filename is None:  # Prevent callback trigger when not needed #
        raise PreventUpdate
    elif contents:
        contents = contents[0]
        filename = filename[0]
        df_excess, df_short, df_met = parse_data(contents, filename)

        table1 = html.Div([
            html.Br(),
            html.H6('Excess Items'),
            dash_table.DataTable(
                id='datatable_id1',
                columns=[{"name": i, "id": i} for i in df_excess.columns],
                data= df_excess.to_dict('records'),
                editable=False,  # allow editing of data inside all cells
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

                tooltip_delay=0,  # 1000
                tooltip_duration=None,  # 2000
                # column headers
                tooltip_header={
                    'Total Purchase Orders': '▲ = Ascending, ▼ = Descending',
                    'Difference': '▲ = Ascending, ▼ = Descending',
                    'Amount': '▲ = Ascending, ▼ = Descending',
                    'Stock': '▲ = Ascending, ▼ = Descending',
                    'Demand': '▲ = Ascending, ▼ = Descending',
                    'Price': 'Moving Avg. Price',
                    'Days to Alert': '▲ = Ascending, ▼ = Descending',
                },


                style_data_conditional=([

                    # 'filter_query', 'column_id', 'column_type', 'row_index', 'state', 'column_editable'.
                    # filter_query ****************************************
                    {
                        'if': {
                            'filter_query': '{Difference} < 0',
                            'column_id': 'Difference'
                        },
                        # 'backgroundColor': 'hotpink',
                        'color': 'red'
                    },
                    {
                        'if': {
                            'filter_query': '{Purchase Order} = no',
                            'column_id': 'Purchase Order'
                        },
                        # 'backgroundColor': 'hotpink',
                        'color': 'black'
                    },
                    {
                        'if': {
                            'filter_query': '{Purchase Order} = yes',
                            'column_id': 'Purchase Order'
                        },
                        # 'backgroundColor': 'hotpink',
                        'color': 'red'
                    },
                ])
            ),

            ])
        ######################################
        table2 = html.Div([
            html.Br(),
            html.H6('Shortfall Items'),
            dash_table.DataTable(
                id='datatable_id1',
                columns=[{"name": i, "id": i} for i in df_short.columns],
                data=df_short.to_dict('records'),
                editable=False,  # allow editing of data inside all cells
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

                tooltip_delay=0,  # 1000
                tooltip_duration=None,  # 2000
                # column headers
                tooltip_header={
                    'Total Purchase Orders': '▲ = Ascending, ▼ = Descending',
                    'Difference': '▲ = Ascending, ▼ = Descending',
                    'Amount': '▲ = Ascending, ▼ = Descending',
                    'Stock': '▲ = Ascending, ▼ = Descending',
                    'Demand': '▲ = Ascending, ▼ = Descending',
                    'Price': 'Moving Avg. Price',
                    'Days to Alert': '▲ = Ascending, ▼ = Descending',
                },

                style_data_conditional=([

                    # 'filter_query', 'column_id', 'column_type', 'row_index', 'state', 'column_editable'.
                    # filter_query ****************************************
                    {
                        'if': {
                            'filter_query': '{Difference} < 0',
                            'column_id': 'Difference'
                        },
                        # 'backgroundColor': 'hotpink',
                        'color': 'red'
                    },
                    {
                        'if': {
                            'filter_query': '{Purchase Order} = no',
                            'column_id': 'Purchase Order'
                        },
                        # 'backgroundColor': 'hotpink',
                        'color': 'black'
                    },
                    {
                        'if': {
                            'filter_query': '{Purchase Order} = yes',
                            'column_id': 'Purchase Order'
                        },
                        # 'backgroundColor': 'hotpink',
                        'color': 'blue'
                    },
                ])
            ),

        ])
        ######################################
        table3 = html.Div([
            html.Br(),
            html.H6('Items demand met'),
            dash_table.DataTable(
                id='datatable_id1',
                columns=[{"name": i, "id": i} for i in df_met.columns],
                data=df_met.to_dict('records'),
                editable=False,  # allow editing of data inside all cells
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

                tooltip_delay=0,  # 1000
                tooltip_duration=None,  # 2000
                # column headers
                tooltip_header={
                    'Total Purchase Orders': '▲ = Ascending, ▼ = Descending',
                    'Difference': '▲ = Ascending, ▼ = Descending',
                    'Amount': '▲ = Ascending, ▼ = Descending',
                    'Stock': '▲ = Ascending, ▼ = Descending',
                    'Demand': '▲ = Ascending, ▼ = Descending',
                    'Price': 'Moving Avg. Price',
                    'Days to Alert': '▲ = Ascending, ▼ = Descending',
                },

                style_data_conditional=([

                    # 'filter_query', 'column_id', 'column_type', 'row_index', 'state', 'column_editable'.
                    # filter_query ****************************************
                    {
                        'if': {
                            'filter_query': '{Difference} < 0',
                            'column_id': 'Difference'
                        },
                        # 'backgroundColor': 'hotpink',
                        'color': 'red'
                    },
                    {
                        'if': {
                            'filter_query': '{Purchase Order} = no',
                            'column_id': 'Purchase Order'
                        },
                        # 'backgroundColor': 'hotpink',
                        'color': 'black'
                    },
                    {
                        'if': {
                            'filter_query': '{Purchase Order} = yes',
                            'column_id': 'Purchase Order'
                        },
                        # 'backgroundColor': 'hotpink',
                        'color': 'blue'
                    },
                ])
            ),

        ])

        return table1, table2, table3, 'Total Excess materials : {}'.format(len(df_excess)), 'Total Short materials : {}'.format(len(df_short)), 'Total Match materials : {}'.format(len(df_met)),

