import qrcode
import pandas as pd

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
import numpy as np
from datetime import date, timedelta
import dash_auth
import dash_bootstrap_components as dbc
import dash_extensions as de
from dash import no_update

from app import app



qr=qrcode.QRCode(version=1,
                  box_size=10,
                  border=5)

colors = {"graphBackground": "#F5F5F5", "background": "#ffffff", "text": "#000000"}

url = "https://assets1.lottiefiles.com/packages/lf20_jQajQi.json"
options = dict(loop=True, autoplay=True, rendererSettings=dict(preserveAspectRatio='xMidYMid slice'))

# ---------------------------------------------------------------------------------------
layout = dbc.Container([

    # 1
    dbc.Row([
        dbc.Col([
            dcc.Markdown(""" ### 
Generate Invoice QR Code""",
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

    #4 DASH DATATABLE
    dcc.Loading(children=[html.Div(id="qrdatatable_id", style={'width': '200vh', 'height': '80vh'})],
                                        color="#119DFF", type="cube", fullscreen=False),


], fluid= True)

# ---------------------------------------------------------------------------------------

#parse data into df
def parse_data(contents, filename):
    content_type, content_string = contents.split(",")

    decoded = base64.b64decode(content_string)
    try:
        if "csv" in filename:
            # Assume that the user uploaded a CSV or TXT file
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
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
#---------------------------------------------------------------------------------------

# Datatable callback
@app.callback(
    [Output("qrdatatable_id", "children")],

     [Input("upload-data", "contents"),
     Input("upload-data", "filename")],
)
# Update datable
def update_table(contents, filename):

    if contents is None or filename is None:  # Prevent callback trigger when not needed #
        raise PreventUpdate
    elif contents:
        contents = contents[0]
        filename = filename[0]

        df = parse_data(contents, filename)
        dff= df
        t=  [dash_table.DataTable(
                id='qrdatatable_id',
                columns=[{"name": i, "id": i} for i in dff.columns],
#                 columns=[
#                     {'name': 'PO#', 'id': 'PO#', 'type': 'numeric', 'editable': False, 'selectable': True},
#                     {'name': 'ITEM#', 'id': 'ITEM#', 'type': 'numeric', 'editable': False, "hideable": True, "deletable": False, 'selectable': True},
#                     {'name': 'Document date', 'id': 'Document date', 'type': 'text', 'editable': False, 'selectable': True},
#                     {'name': 'Delivery Note/Invoice Reference', 'id': 'Delivery Note/Invoice Reference', 'type': 'text', 'editable': False, 'selectable': True},
#                     {'name': 'Bill of Lading', 'id': 'Bill of Lading', 'type': 'text', 'editable': False, "hideable": True, 'selectable': True},
#                     {'name': 'HEADER TEXT', 'id': 'HEADER TEXT', 'type': 'text', 'editable': False, "hideable": True, 'selectable': True},
#                     {'name': 'Qty in Delivery Note', 'id': 'Qty in Delivery Note', 'type': 'text', 'editable': False, "hideable": True, 'selectable': True},
#                     {'name': 'Qty in Unit of Entry', 'id': 'Qty in Unit of Entry', 'type': 'text', 'editable': False, "hideable": True, 'selectable': True},
#                     {'name': 'Text  in Where Tab', 'id': 'Text  in Where Tab', 'type': 'text', 'editable': False, 'selectable': True},
#                     {'name': 'STORAGE LOCATION', 'id': 'STORAGE LOCATION', 'type': 'text', 'editable': False, 'selectable': True},
#                     {'name': 'PLANT', 'id': 'PLANT', 'type': 'text', 'editable': False, 'selectable': True},
#                     {'name': 'Attachment Path', 'id': 'Attachment Path', 'type': 'datetime', 'editable': False, "hideable": True, "deletable": True, 'selectable': True},
#                     {'name': 'Create Note', 'id': 'Create Note', 'type': 'text', 'editable': False, "hideable": True, "deletable": True, 'selectable': True},
#                 ],
                data=dff.to_dict('records'),
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
            )],
        
        data = dff
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        # img.save('Desktop\\1.png')
        # img.save('invoice_QR.png')
        img.show()
        
        return  t
      

