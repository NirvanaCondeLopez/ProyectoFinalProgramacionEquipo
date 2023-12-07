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


