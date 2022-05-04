import sys
import dash
import flask
from dash import dcc
from dash import html
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.express as px

class Parrainage():

    def __init__(self, application = None):
        self.df = pd.read_csv("parrainage/data/parrainagestotal.csv", sep=";")
        self.candidats_occurences = self.df['Candidat'].value_counts()
        self.candidats_list = self.candidats_occurences[self.candidats_occurences > 500].keys()
        
        self.main_layout = html.Div(children=[
            html.H3(children='Évolution du nombre de parrainages par candidat à la présidentielle'),

            html.Div([
                    html.Div([ dcc.Graph(id='par-main-graph'), ], style={'width':'80%', }),
                    html.Div([
                        html.Br(),
                        html.Br(),
                        html.Div('Candidat'),
                        dcc.RadioItems(
                            id='par-candidat',
                            options=[{'label': candidat, 'value': candidat} for candidat in self.candidats_list],
                            value=self.candidats_list[0],
                            labelStyle={'display':'block'},
                        ),
                        html.Br()
                    ], style={'margin-left':'15px', 'width': '15em', 'float':'right'}),
                ], style={
                    'padding': '10px 50px', 
                    'display':'flex',
                    'justifyContent':'center'
                }),            
            
            html.Br(),
            dcc.Markdown("""
            #### À propos

            * Inspiration initiale : [conférence de Hans Rosling](https://www.ted.com/talks/hans_rosling_new_insights_on_poverty)
            * [Version Plotly](https://plotly.com/python/v3/gapminder-example/)
            * Données : [Banque mondiale](https://databank.worldbank.org/source/world-development-indicators)
            * (c) 2022 Olivier Ricou
            """),
           

        ], style={
                #'backgroundColor': 'rgb(240, 240, 240)',
                 'padding': '10px 50px 10px 50px',
                 }
        )
        
        if application:
            self.app = application
            # application should have its own layout and use self.main_layout as a page or in a component
        else:
            self.app = dash.Dash(__name__)
            self.app.layout = self.main_layout

        # I link callbacks here since @app decorator does not work inside a class
        # (somhow it is more clear to have here all interaction between functions and components)
        self.app.callback(
            dash.dependencies.Output('par-main-graph', 'figure'),
            [dash.dependencies.Input('par-candidat', 'value')])(self.update_graph)


    def update_graph(self, candidat):
        # Select candidate
        parrainages = self.df[self.df['Candidat'] == candidat]

        count_by_date = parrainages.groupby(["Date de publication"]).size()

        index = count_by_date.index
        index.name = 'date'

        df_count_by_date = pd.DataFrame(
            {"Parrainages": count_by_date, "Parrainages total": count_by_date.cumsum()}, index=index)

        df_count_by_date = df_count_by_date.reset_index().melt('date', var_name="Catégorie", value_name="y")

        fig = px.line(df_count_by_date, template='plotly_white', x='date', y='y', color='Catégorie')
        fig.update_traces(hovertemplate='%{y} parrainages le %{x:%d/%m/%y}')
        fig.update_layout(hovermode="x unified")
        fig.update_layout(
            xaxis = dict(title="Date de publication"),
            yaxis = dict(title="Nombre parrainages"), 
            height=450,
            showlegend=True,
        )
        return fig

    def create_time_series(self, country, what, axis_type, title):
        return {
            'data': [go.Scatter(
                x = self.years,
                y = self.df[self.df["Country Name"] == country][what],
                mode = 'lines+markers',
            )],
            'layout': {
                'height': 225,
                'margin': {'l': 50, 'b': 20, 'r': 10, 't': 20},
                'yaxis': {'title':title,
                          'type': 'linear' if axis_type == 'Linéaire' else 'log'},
                'xaxis': {'showgrid': False}
            }
        }


    def get_country(self, hoverData):
        if hoverData == None:  # init value
            return self.df['Country Name'].iloc[np.random.randint(len(self.df))]
        return hoverData['points'][0]['hovertext']

    def country_chosen(self, hoverData):
        return self.get_country(hoverData)

    # graph incomes vs years
    def update_income_timeseries(self, hoverData, xaxis_type):
        country = self.get_country(hoverData)
        return self.create_time_series(country, 'incomes', xaxis_type, 'PIB par personne (US $)')

    # graph children vs years
    def update_fertility_timeseries(self, hoverData, xaxis_type):
        country = self.get_country(hoverData)
        return self.create_time_series(country, 'fertility', xaxis_type, "Nombre d'enfants par femme")

    # graph population vs years
    def update_pop_timeseries(self, hoverData, xaxis_type):
        country = self.get_country(hoverData)
        return self.create_time_series(country, 'population', xaxis_type, 'Population')

    # start and stop the movie
    def button_on_click(self, n_clicks, text):
        if text == self.START:
            return self.STOP
        else:
            return self.START

    # this one is triggered by the previous one because we cannot have 2 outputs
    # in the same callback
    def run_movie(self, text):
        if text == self.START:    # then it means we are stopped
            return 0 
        else:
            return -1

    # see if it should move the slider for simulating a movie
    def on_interval(self, n_intervals, year, text):
        if text == self.STOP:  # then we are running
            if year == self.years[-1]:
                return self.years[0]
            else:
                return year + 1
        else:
            return year  # nothing changes

    def run(self, debug=False, port=8050):
        self.app.run_server(host="0.0.0.0", debug=debug, port=port)


if __name__ == '__main__':
    ws = Parrainage()
    ws.run(port=8055)
