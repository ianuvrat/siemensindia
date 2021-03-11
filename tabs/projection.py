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

colors = {"graphBackground": "#F5F5F5", "background": "#ffffff", "text": "#000000"}
alert = dbc.Alert("Alert : Materials with 3 or more POs will reflect incorrect 'PO adjustments' and 'Amount' ",
                  color="danger",
                  dismissable=False),
                 # duration=10000)     # dismissable=False),  # use dismissable or duration=5000 for alert to close in x milliseconds
######################################################################################################################################################################################################################

layout = dbc.Container([

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
    # 1 Material dpdn
    dbc.Row([
        dbc.Col([
            html.Div(id="the_alert", children=[]),        # Alert
            html.Label("Material:", style={'fontSize': 30, 'textAlign': 'center'}),
            dcc.Dropdown(
                id='material-dpdn',
                #options=[],
                #options=[{'label': s, 'value': s} for s in sorted(df['Material'].unique())],
                value='100707429',
                clearable=False,
                multi=False,
                searchable=True,  # allow user-searching of dropdown values
                search_value='',  # remembers the value searched in dropdown
                placeholder='Choose a material ',  # gray, default text shown when no option is selected
                persistence=True,  # remembers dropdown value. Used with persistence_type
                persistence_type='local'  # remembers dropdown value selected until...
                # 'memory': browser tab is refreshed
                # 'session': browser tab is closed
                # 'local': browser cookies are deleted
            ),
        ], className="text-left", width={'size': 3, 'offset': 0, 'order': 0}),

        dbc.Col([
            html.Div(id='po_count'),
        ], className="text-left text-info font-weight-bold ", width={'size': 2, 'offset': 0, 'order': 0}),
    ]),

    html.Br(),
    # 2 Display Info
    dbc.Row([
        dbc.Col([
            html.Div(id='stock_data'),
        ], className="text-left text-success ", width={'size': 2, 'offset': 0, 'order': 0}),
        dbc.Col([
            html.Div(id='demand_data'),
        ], className="text-left text-danger ", width={'size': 2, 'offset': 0, 'order': 0}),
        dbc.Col([
            html.Div(id='diff_data'),
        ], className="text-left font-italic ", width={'size': 2, 'offset': 0, 'order': 0}),
        dbc.Col([
            html.Div(id='po1'),
        ], className="text-left ", width={'size': 2, 'offset': 0, 'order': 0}),

        dbc.Col([
            html.Div(id='bal1_data'),
        ], className="text-left font-weight-bold text-primary ", width={'size': 2, 'offset': 0, 'order': 0}),

        dbc.Col([
            html.Div(id='bal1_price'),
        ], className="text-left font-weight-bold text-success ", width={'size': 2, 'offset': 0, 'order': 0}),

    ],className='p-1 border border-primary border-bottom-0'),

    # 3 PO Adjustment display
    dbc.Row([

        dbc.Col([
            html.Div(id='po2'),
        ], className="text-left ", width={'size': 2, 'offset': 6, 'order': 0}),

        dbc.Col([
            html.Div(id='bal2_data'),
        ], className="text-left font-weight-bold text-primary", width={'size': 2, 'offset': 0, 'order': 0}),

        dbc.Col([
            html.Div(id='bal2_price'),
        ], className="text-left font-weight-bold text-success ", width={'size': 2, 'offset': 0, 'order': 0}),

    ],className='p-1 border border-primary border-top-0'),

    # 4 Bar Chart
    dcc.Loading(children=[dcc.Graph(id='my_bar')],color="#119DFF", type="cube", fullscreen=False),

    # 6  Inspect Vendor
    dbc.Row([
        dbc.Col([
            dcc.Markdown(""" ### 
Current Month Transactions""",
                         className="text-center font-weight-normal text-primary font-weight-bold"),
        ]),
    ]),

    # 5 Dash datatable
    html.Div(id="output-data-upload2", style={'width': '200vh', 'height': '100vh'}),

], fluid=True)
######################################################################################################################################################################################################################

#parse upload data to df
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
            # Excluding repetitions
            df = df[df['MRP segmt'] == 2]
            # Dropping unwanted columns
            df.drop(df.columns[[1, 3, 5, 8, 15]], axis=1, inplace=True)
            # Renaming cols
            df.rename(columns={'      Rec./reqd qty': 'Rec./reqd qty',
                               '         Avail. qty': 'Avail. qty'}, inplace=True)
            # # Formatting dates
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
            df['Resch.date'] = pd.to_datetime(df['Resch.date'])
            # # Adding cols
            df['month'] = df['Date'].dt.month
            df['year'] = df['Date'].dt.year
            df['month_year'] = pd.to_datetime(df[['year', 'month']].assign(DAY=1))
        elif "xls" in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
        elif "txt" or "tsv" in filename:
            # Assume that the user upl, delimiter = r'\s+'oaded an excel file
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")), delimiter=r"\s+")


    except Exception as e:
        print(e)
        return html.Div(["There was an error processing this file."])

    return df

# ------------------------------------------------------------------------------------------------
# Parsing upload contents to dropdown
@app.callback(
              Output('material-dpdn', 'options'),

              [Input("upload-data", "contents"),
               Input("upload-data", "filename")],
)
def parse_uploads(contents, filename):
    if contents is None or filename is None:  # Prevent callback trigger when not needed #
        raise PreventUpdate
    elif contents:
        contents = contents[0]
        filename = filename[0]
        df = parse_data(contents, filename)

        return [{'label': s, 'value': s } for s in sorted(df['Material'].unique())]
# ------------------------------------------------------------------------------------------------
########################################################################################  BAR CHART  ########################################################################################################################
# Connecting the Dropdown values to the Bargraph
@app.callback(
    Output(component_id='my_bar', component_property='figure'),

    [Input("upload-data", "contents"),
     Input("upload-data", "filename"),
     Input(component_id='material-dpdn', component_property='value')]
)
def build_graph(contents, filename,chosen_material):

    if contents is None or filename is None:  # Prevent callback trigger when not needed #
        raise PreventUpdate
    elif contents:
        contents = contents[0]
        filename = filename[0]
        df = parse_data(contents, filename)

        # Material df
        dff = df[df['Material'] == chosen_material]
        # Groupby and converting to df
        gb_dff = dff.groupby(['month_year', 'Plus/minus'])['Rec./reqd qty'].sum().to_frame(name='Quantity').reset_index()
        # Plotting
        fig = px.bar(gb_dff, x='month_year', y='Quantity',
                     color="Plus/minus",
                     text='Quantity',
                     title="M-o-M Inventory Projection: Material {}".format(chosen_material),
                     labels={'month_year': 'Month & Year'},
                     barmode='relative',  # 'group' or 'overlay'
                     # facet_col='month_year',
                     # facet_row="Plus/minus"
                     # height=600
                     )

        fig.update_layout(xaxis={'categoryorder': 'total ascending'},
                          title={'xanchor': 'center', 'yanchor': 'top', 'y': 0.9, 'x': 0.5, })

        fig.update_traces(texttemplate='%{text:.2s}', textposition='inside')
        # fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')

        return fig

#########################################################################################  Display Info  ######################################################################################################################
# Connecting drpdwn to display info
@app.callback(
    [Output('stock_data', 'children'),
     Output('demand_data', 'children'),
     Output('diff_data', 'children'),
     Output('bal1_data', 'children'),
     Output('bal2_data', 'children'),
     Output('po1', 'children'),
     Output('po2', 'children'),
     Output('bal1_price', 'children'),
     Output('bal2_price', 'children'),
     Output("the_alert", "children"),
     Output("po_count", "children")],

    [Input("upload-data", "contents"),
     Input("upload-data", "filename"),
     Input('material-dpdn', 'value')]
)
def build_graph(contents, filename,chosen_material):

    if contents is None or filename is None:  # Prevent callback trigger when not needed #
        raise PreventUpdate
    elif contents:
        contents = contents[0]
        filename = filename[0]
        df = parse_data(contents, filename)

        # ------- FILTERING DF  --------
        # Material df
        dff = df[df['Material'] == chosen_material]
        # Current Month
        cur_month = dff.loc[dff['Plus/minus'] == 'B', 'month_year'].iloc[0]
        # Current month dff + Overdue Demand
        dff = dff[dff['month_year'] <= cur_month]
        # Dropping PO history
        i = dff[((dff['Plus/minus'] == '+') & (dff['month_year'] < cur_month))].index
        dff = dff.drop(i)
        # Available Stock
        stock = dff.loc[dff['Plus/minus'] == 'B', 'Rec./reqd qty'].iloc[0]
        # price
        price = dff.loc[dff['Plus/minus'] == 'B', 'price'].iloc[0]
        # Exception Code
        exp = dff['Exc.'].max()
        # PO df
        po_dff = dff[dff['Plus/minus'] == '+']
        # No. of POs
        po_len = len(po_dff)

        print('Current Month: {}'.format(cur_month))
        print('Exception code: {}'.format(exp))
        print('Moving Avg. Price: {}'.format(price))

        # If no PO
        if po_dff.empty:
            print('No Purchase Order')

        ############ MONTHLY DEMAND AND REMAINING STOCK   ##########
        # loop for to calculate monthly demand
        demand = []
        for req in dff['Rec./reqd qty']:
            if req < 0:
                demand.append(req)
        #-----------------------------------
        # Monthly Demand and Remaining stock
        tot_demand = round(sum(demand))
        diff = round(tot_demand + stock)

        print('Month Stock: {}'.format(stock))
        print('Current Month Demand: {}'.format(tot_demand))

        if diff > 0:
            print('Excess before PO adjustment: {}'.format(diff))
        elif diff == 0:
            print('Demand met requirement before PO: {}'.format(diff))
        elif diff < 0:
            print('Shortfall before PO adjustment: {}'.format(diff))

        ############## ADJUSTMENT WITH  PO  ##############
        # If no PO exists
        if po_dff.empty:
            print('No Purchase Order')
            amount = diff * price
            return ('Stock {}'.format(stock), 'Demand {}'.format(tot_demand), 'Difference {}'.format(diff), 'Amount: ₹ {}'.format(amount), '', '', '', '', '', '', 'Total POs = {}'.format(po_len))


        # If PO exists
        else:
            c = 0  # Counting  POs
            temp = 0
            for po in po_dff['Rec./reqd qty']:

                c += 1
                print('\nPO{}'.format(c))
                bal1 = diff + po
                bal2 = temp + po

                if (bal1 > 0 and c == 1):
                    po1 = po                                                  # PO 1
                    po2 = 0
                    temp = bal1
                    amount = round((temp * price), 2)
                    resc_date1 = dff.loc[dff['Plus/minus'] == '+', 'Resch.date'].iloc[0]
                    print('New PO: {}'.format(po))
                    print('..adjusting')
                    print('Push {} to date {}'.format(temp, resc_date1))
                    print('Amount: ₹ {} '.format(amount))

                elif (bal1 < 0 and c == 1):
                    po1 = po                                                  # PO 1
                    po2 = 0
                    temp = bal1
                    amount = round((temp * price), 2)
                    print('New PO: {}'.format(po))
                    print('   ..adjusting')
                    print('Shortfall after PO adjustment: {}'.format(temp))
                    print('Amount: ₹ {} '.format(amount))

                elif (bal2 < 0 and c == 2):
                    po2 = po                                                  # PO 2
                    amount = round((bal2 * price), 2)
                    print('New PO: {}'.format(po))
                    print('   ..adjusting')
                    print('Shortfall after PO adjustment: {}'.format(bal2))
                    print('Amount: ₹ {} '.format(amount))



                elif (bal2 > 0 and c == 2):
                    po2 = po                                                # PO 2
                    amount = round((bal2 * price), 2)
                    print('New PO: {}'.format(po))
                    print('..adjusting')
                    print('Push {}'.format(bal2))
                    print('Amount: ₹ {} '.format(amount))



        if c > 1:
            return ('Stock {}'.format(stock), 'Demand {}'.format(tot_demand), 'Difference {}'.format(diff),
                'PO1 adjustment {}'.format(temp), 'PO2 adjustment {}'.format(bal2),
                'PO1 {}'.format(po1), 'PO2 {}'.format(po2),
                '', 'Amount: ₹ {} '.format(amount), alert, 'Total POs = {}'.format(po_len))

        if c <= 1:
            return ('Stock {}'.format(stock), 'Demand {}'.format(tot_demand), 'Difference {}'.format(diff),
                'PO1 adjustment {}'.format(temp), '',
                'PO1 {}'.format(po1), '',
                'Amount: ₹ {} '.format(amount), '', '', 'Total POs = {}'.format(po_len))


###############################################################################################################################################################################################################
# Connecting the Dropdown values to the dashdatable
@app.callback(
    Output('output-data-upload2', 'children'),

    [Input("upload-data", "contents"),
     Input("upload-data", "filename"),
     Input('material-dpdn', 'value')]
)
def build_graph(contents, filename,chosen_material):
    if contents is None or filename is None:  # Prevent callback trigger when not needed #
        raise PreventUpdate
    elif contents:
        contents = contents[0]
        filename = filename[0]
        df = parse_data(contents, filename)

        ##################### FILTERING DF  #######################
        # Material df
        dff = df[df['Material'] == chosen_material]
        # Current Month
        cur_month = dff.loc[dff['Plus/minus'] == 'B', 'month_year'].iloc[0]
        # Current month dff + Overdue Demand
        dff = dff[dff['month_year'] <= cur_month]
        # Dropping PO history
        i = dff[((dff['Plus/minus'] == '+') & (dff['month_year'] < cur_month))].index
        dff = dff.drop(i)
        # Available Stock
        stock = dff.loc[dff['Plus/minus'] == 'B', 'Rec./reqd qty'].iloc[0]
        # price
        price = dff.loc[dff['Plus/minus'] == 'B', 'price'].iloc[0]
        # Exception Code
        exp = dff['Exc.'].max()
        # PO df
        po_dff = dff[dff['Plus/minus'] == '+']

        # If no PO
        if po_dff.empty:
             print('No Purchase Order')

        ########## MONTHLY DEMAND AND REMAINING STOCK   ##########
        # loop for to calculate monthly demand
        demand = []
        for req in dff['Rec./reqd qty']:
            if req < 0:
                demand.append(req)
        # ------------------------------------
        # Monthly Demand and Remaining stock
        tot_demand = round(sum(demand))
        diff = round(tot_demand + stock)
        #
        # print('Month Stock: {}'.format(stock))
        # print('Current Month Demand: {}'.format(tot_demand))
        if diff > 0:
            print('Excess before PO adjustment: {}'.format(diff))
        elif diff == 0:
            print('Demand met requirement before PO: {}'.format(diff))
        elif diff < 0:
            print('Shortfall before PO adjustment: {}'.format(diff))

        ################ ADJUSTMENT WITH  PO  ###############

        # If no PO exists
        if po_dff.empty:
            print('No Purchase Order')
        # If PO exists
        else:
            c = 0  # Counter for PO
            temp = 0

            for po in po_dff['Rec./reqd qty']:
                c += 1
                print('\nPO{}'.format(c))

                bal1 = diff + po
                bal2 = temp + po

                if (bal1 > 0 and c == 1):
                    po1 = po
                    temp2 = bal1
                    resc_date1 = dff.loc[dff['Plus/minus'] == '+', 'Resch.date'].iloc[0]
                    print('New PO: {}'.format(po))
                    print('..adjusting')
                    print('Push {} to date {}'.format(temp2, resc_date1))

                elif (bal1 < 0 and c == 1):
                    po1 = po
                    temp = bal1
                    print('New PO: {}'.format(po))
                    print('   ..adjusting')
                    print('Shortfall after PO adjustment: {}'.format(temp))

                elif (bal2 < 0 and c == 2):
                    po2 = po
                    print('New PO: {}'.format(po))
                    print('   ..adjusting')
                    print('Shortfall after PO adjustment: {}'.format(bal2))


                elif (bal2 > 0 and c == 2):
                    po2 = po
                    print('New PO: {}'.format(po))
                    print('..adjusting')
                    print('Push {}'.format(bal2))

        table = html.Div(
            [
                dash_table.DataTable(
                    id='datatable_id',
                    data=dff.to_dict("records"),
                    columns=[
                        {"name": i, "id": i, "deletable": True, "selectable": True, "hideable": True}
                        if i == "Material" or i == "Date" or i == "MRP segmt" or i == "Planning segment" or i == "month_year" or i == "month" or i == "year"
                        else {"name": i, "id": i, "deletable": True, "selectable": True}
                        for i in df.columns
                    ],

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
                    style_data_conditional=(
                        [
                            # Format empty cell ***********************************
                            {
                                'if': {  # Vendor code
                                    'filter_query': '{Vendor} = 0',
                                    'column_id': 'Vendor'
                                },
                                'backgroundColor': 'gray',
                            },
                            {
                                'if': {  # Vendor name
                                    'filter_query': '{Vendor.1} = 0',
                                    'column_id': 'Vendor.1'
                                },
                                'backgroundColor': 'gray',
                            },
                            {
                                'if': {  # Exception code
                                    'filter_query': '{Exc.} = 0',
                                    'column_id': 'Exc.'
                                },
                                'backgroundColor': 'gray',
                            },
                            # Format cell ***********************************
                            {
                                'if': {  # Purchase Order
                                    'filter_query': '{Plus/minus} = +',
                                    # 'column_id': 'Plus/minus'
                                },
                                'fontWeight': 'bold',
                                'color': 'blue',
                            },

                            {
                                'if': {  # Stock
                                    'filter_query': '{Plus/minus} = B',
                                    # 'column_id': 'Plus/minus'
                                },
                                # 'backgroundColor': 'red',
                                'fontWeight': 'bold',
                                'color': 'green'
                            },

                            {
                                'if': {  # Demand
                                    'filter_query': '{Plus/minus} = -',
                                    'column_id': 'Plus/minus'
                                },
                                'fontWeight': 'bold',
                                'color': 'red',
                            },

                            {
                                'if': {  # MRP Element
                                    'filter_query': '{MRP elemnt} = Stock',
                                    'column_id': 'MRP elemnt'
                                },
                                'fontWeight': 'bold',
                                'color': 'green',
                            },

                            {
                                'if': {  # MRP Element
                                    'filter_query': '{MRP elemnt} = POitem || {MRP elemnt} = ShpgNt',
                                    'column_id': 'MRP elemnt'
                                },
                                'fontWeight': 'bold',
                                'color': 'blue',
                            }
                        ]
                    )
                ),
            ]
        )

        return table
# ----------------------------------------------------