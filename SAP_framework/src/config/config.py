import os
from dotenv import load_dotenv

load_dotenv()

class SAPConfig:
    SAP_LOGON_PATH = os.getenv("SAP_LOGON_PATH", r"C:\Program Files (x86)\SAP\FrontEnd\SAPgui\saplogon.exe")
    CONNECTION_NAME = os.getenv("SAP_CONNECTION", "SAP EWM S/4 (PRE-PRODUCTIVO)")
    DEFAULT_CLIENT = os.getenv("SAP_CLIENT", "400")
    DEFAULT_LANGUAGE = os.getenv("SAP_LANGUAGE", "ES")

class Credentials:
    USERNAME = os.getenv("SAP_USERNAME", "camedinar")
    PASSWORD = os.getenv("SAP_PASSWORD", "Pruebas2025")
