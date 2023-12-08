import requests
from bs4 import BeautifulSoup
import pandas as pd
from dash import dcc, html
import plotly.express as px
import mysql.connector
from datetime import datetime
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from dash import Dash
import threading
import plotly.graph_objects as go
from CONSTANTES import URL,CSV_FILE_PATH,HOSTB,USERB,DATABASEB,PASSWORDB
import calendar

def scrape_data(URL):
    try:
        response = requests.get(URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        data_list = []

        rows = soup.select('body > div.dialog-off-canvas-main-canvas > div.main-container.container.js-quickedit-main-content > div > section > div > article > div > div:nth-child(3) > div.col-sm-12 table tr')

        for row in rows[1:]:
            columns = row.find_all('td')
            if len(columns) >= 5:
                fecha_str = columns[0].get_text().strip()
                fecha = datetime.strptime(fecha_str, '%d/%m/%Y').strftime('%Y-%m-%d')
                dosis_administradas = int(columns[1].get_text().replace('.', '').replace(',', '')) if columns[1].get_text().strip() else 0
                personas_vacunadas = int(columns[2].get_text().replace('.', '').replace(',', '')) if columns[2].get_text().strip() else 0
                complet_vacunadas = int(columns[3].get_text().replace('.', '').replace(',', '')) if columns[3].get_text().strip() else 0
                porcentaje_completas = float(columns[4].get_text().replace('%', '').replace(',', '')) if columns[4].get_text().strip() else 0

                data_list.append({
                    'Fecha': fecha,
                    'Dosis administradas': dosis_administradas,
                    'Personas vacunadas': personas_vacunadas,
                    'Completamente vacunadas': complet_vacunadas,
                    'Porcentaje completamente vacunadas': porcentaje_completas
                })
            else:
                print("Número insuficiente de columnas en una fila.")

        df = pd.DataFrame(data_list)
        return df

    except requests.exceptions.RequestException as e:
        print(f'Error en la solicitud HTTP: {e}')
        return None
    except Exception as e:
        print(f'Error: {e}')
        return None

def guardar_datos_en_csv(df, CSV_FILE_PATH):
    try:
        df.to_csv(CSV_FILE_PATH, index=False)
        print(f'Datos guardados en {CSV_FILE_PATH}')
    except Exception as e:
        print(f'Error al guardar en CSV: {e}')

class MySQLConnect:
    def __init__(self, host, user, password, database):
        self._host = host
        self._user = user
        self._password = password
        self._database = database
        self._connection = None

    @property
    def host(self):
        return self._host

    @property
    def user(self):
        return self._user

    @property
    def password(self):
        return self._password

    @property
    def database(self):
        return self._database

    def conectar(self):
        try:
            self._connection = mysql.connector.connect(
                host=self._host,
                user=self._user,
                password=self._password,
                database=self._database
            )
            return self._connection
        except mysql.connector.Error as err:
            print(f"Error al conectar a la base de datos: {err}")
            return None

    def desconectar(self):
        if self._connection:
            self._connection.close()
            self._connection = None
            
    def insert_vacunas(self, fecha, dosis_administradas):
        try:
            connection = self.conectar()
            cursor = connection.cursor()

            cursor.execute(
                """INSERT INTO Vacunas(Fecha, Dosis_administradas)
                VALUES (%s, %s)""",
                (fecha, dosis_administradas)
            )
            connection.commit()
        except mysql.connector.Error as err:
            print(f"Error al insertar datos en Vacunas: {err}")
        finally:
            if cursor:
                cursor.close()
            self.desconectar()

    def insert_personas_vacunadas(self, vacuna_id,fecha, personas_vacunadas):
        try:
            connection = self.conectar()
            cursor = connection.cursor()

            cursor.execute(
                """INSERT INTO PersonasVacunadas(Vacuna_id,Fecha, Personas_vacunadas)
                VALUES (%s, %s,%s)""",
                (vacuna_id,fecha, personas_vacunadas)
            )
            connection.commit()
        except mysql.connector.Error as err:
            print(f"Error al insertar datos en PersonasVacunadas: {err}")
        finally:
            if cursor:
                cursor.close()
            self.desconectar()

    def insert_completamente_vacunadas(self, persona_vacunada_id,fecha, complet_vacunadas, porcentaje_completas):
        try:
            connection = self.conectar()
            cursor = connection.cursor()

            cursor.execute(
                """INSERT INTO CompletamenteVacunadas(PersonaVacunada_id,Fecha, Completamente_vacunadas, Porcentaje_completamente_vacunadas)
                VALUES (%s, %s, %s,%s)""",
                (persona_vacunada_id,fecha, complet_vacunadas, porcentaje_completas)
            )
            connection.commit()
        except mysql.connector.Error as err:
            print(f"Error al insertar datos en CompletamenteVacunadas: {err}")
        finally:
            if cursor:
                cursor.close()
            self.desconectar()

db_connection = MySQLConnect(HOSTB, USERB, PASSWORDB, DATABASEB)

def get_data_from_database(db_connection):
    try:
        connection = db_connection.conectar()
        cursor = connection.cursor()


        query_vacunas = "SELECT Fecha, Dosis_administradas FROM Vacunas"
        cursor.execute(query_vacunas)
        data_vacunas = cursor.fetchall()  # Obtiene todos los datos de Vacunas
        df_dosis = pd.DataFrame(data_vacunas, columns=['Fecha', 'Dosis_administradas'])


        query_personas = "SELECT Fecha, Personas_vacunadas FROM PersonasVacunadas"
        cursor.execute(query_personas)
        data_personas = cursor.fetchall()  # Obtiene todos los datos de PersonasVacunadas
        df_personas = pd.DataFrame(data_personas, columns=['Fecha', 'Personas_vacunadas'])


        query_completamente = "SELECT Fecha, Completamente_vacunadas, Porcentaje_completamente_vacunadas FROM CompletamenteVacunadas"
        cursor.execute(query_completamente)
        data_completamente = cursor.fetchall()
        df_completamente = pd.DataFrame(data_completamente, columns=['Fecha', 'Completamente_vacunadas', 'Porcentaje_completamente_vacunadas'])

        cursor.close()
        connection.close()

        return df_dosis, df_personas, df_completamente

    except mysql.connector.Error as e:
        print(f"Error al obtener datos de la base de datos: {e}")
        return None, None, None
        
def procesar_datos(df, db_connection):
    try:
        df_dosis = df[['Fecha', 'Dosis administradas']].copy()
        df_personas = df[['Fecha', 'Personas vacunadas']].copy()
        df_completamente = df[['Fecha', 'Completamente vacunadas', 'Porcentaje completamente vacunadas']].copy()

        for index, row in df_dosis.iterrows():
            fecha = row['Fecha']
            dosis_administradas = row['Dosis administradas']
            db_connection.insert_vacunas(fecha, dosis_administradas)

        for index, row in df_personas.iterrows():
            vacuna_id = index + 1
            fecha = row['Fecha']
            personas_vacunadas = row['Personas vacunadas']
            db_connection.insert_personas_vacunadas(vacuna_id, fecha, personas_vacunadas)

        for index, row in df_completamente.iterrows():
            persona_vacunada_id = index + 1
            fecha = row['Fecha']
            complet_vacunadas = row['Completamente vacunadas']
            porcentaje_completas = row['Porcentaje completamente vacunadas']
            db_connection.insert_completamente_vacunadas(persona_vacunada_id, fecha, complet_vacunadas, porcentaje_completas)

    except Exception as e:
        print(f'Error al procesar datos: {e}')


df_dosis, df_personas, df_completamente = get_data_from_database(db_connection)
Integrantes = ["Nirvana Conde Lopez", "Maria Jose Rojas Sañudo", "Laura Vega Hernandez", "Jamie Mota Parra", "Francisco Lagunes Lopez"]
months = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]
months = list(calendar.month_name)[1:]


kpi_style_dashboard1 = {
    'backgroundColor': '#343a40',
    'color': 'white',
    'padding': '20px',
    'borderRadius': '10px',
    'textAlign': 'center'
}
app1 = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], url_base_pathname='/dashboard1/')
app1.layout = dbc.Container(
    style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#007bff', 'padding': '20px'},
    children=[
        html.Div(
            style={'backgroundColor': '#343a40', 'color': 'white', 'padding': '20px', 'marginBottom': '20px'},
            children=[
                html.H1("Dashboard de Vacunación COVID-19 en México", style={'textAlign': 'center'}),
                html.P("Visualización de datos sobre la vacunación contra COVID-19 en México.", style={'textAlign': 'center'}),
            ]
        ),
        html.Div(
            style={'backgroundColor': 'white', 'padding': '20px', 'border': '1px solid #ddd', 'borderRadius': '10px',
                   'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'},
            children=[
                html.H3("Equipo de Desarrollo:", style={'color': '#333', 'marginBottom': '10px'}),
                html.Ol(
                    [html.Li(member, style={'fontSize': '16px', 'marginBottom': '8px', 'lineHeight': '1.6'}) for member in Integrantes]
                ),
            ]
        ),
        html.Div([
            html.P("La vacunación es una forma sencilla, inocua y eficaz de protegernos contra enfermedades dañinas antes de entrar en contacto con ellas. Las vacunas activan las defensas naturales del organismo para que aprendan a resistir a infecciones específicas, y fortalecen el sistema inmunitario.", style={'fontSize': '18px', 'fontWeight': 'bold', 'marginBottom': '10px','textAlign': 'center'}),
            dcc.Graph(
                id='graph-dosis-administradas1',
                figure={
                    'data': [
                        go.Scatter(
                            x=df_dosis['Fecha'].tolist(),
                            y=df_dosis['Dosis_administradas'].tolist(),
                            mode='lines+markers',
                            name='Dosis Administradas'
                        )
                    ],
                    'layout': {
                        'title': 'Dosis Administradas',
                        'xaxis': {'title': 'Fecha'},
                        'yaxis': {'title': 'Dosis administradas'},
                        'hovermode': 'closest'
                    }
                }
            ),
            html.Div(
                style=kpi_style_dashboard1,
                children=[
                    html.H3("Promedio de dosis administradas-KPI", style={'marginBottom': '10px'}),
                    daq.Gauge(
                        id='my-gauge1',
                        label='Dosis administradas',
                        value=df_dosis['Dosis_administradas'].mean(),
                        max=df_dosis['Dosis_administradas'].max(),
                        min=df_dosis['Dosis_administradas'].min(),
                        showCurrentValue=True,
                        units="Dosis"
                    ),
                    html.H2(f"{df_dosis['Dosis_administradas'].mean():.2f}",
                            style={'fontSize': '48px', 'fontWeight': 'bold', 'marginBottom': '0'})
                ]
            ),
            html.Div([
                dcc.Graph(
                    id='bar-chart1',
                    figure=px.bar(df_dosis.head(10), x='Fecha', y='Dosis_administradas', title='Últimas 10 Fechas - Dosis Administradas'),
                    style={'height': '400px'}
                )
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            html.H4("Maximo de Dosis administradas", className="card-title"),
                            html.P(df_dosis['Dosis_administradas'].max(), className="card-text",
                                   style={'fontSize': '15px'}),
                        ]),
                        className="mb-3 text-center",
                        color='Blue',
                        inverse=True,
                    ),
                ], width=4),
            ])
        ]),
    ]
)
