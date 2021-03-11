from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import dash_extensions as de

from app import app,dbc

url = "https://assets1.lottiefiles.com/packages/lf20_q56zavhf.json"
options = dict(loop=True, autoplay=True, rendererSettings=dict(preserveAspectRatio='xMidYMid slice'))

layout = [
        dcc.Markdown(""" ### Intro
    This web application helps the management to analyze advance payment alerts and  project inventory!! """,
                     className="text-left font-weight-normal text-primary"),


        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Div(de.Lottie(options=options, width="25%", height="15%", url=url)),

        #html.Br(),
        # dbc.Row([
        #     dbc.Col([
        #         html.Img(src='https://raw.githubusercontent.com/ianuvrat/datasets/main/new.jpg',),
        #
        #             ],className="text-center",width={'size':12, 'offset':0, 'order':1}),
        #         ]),

        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),


        dcc.Markdown("""Created by Anuvrat Shukla""",
                     className="text-left font-weight-normal text-primary")
        ]

