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