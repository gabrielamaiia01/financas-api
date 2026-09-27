import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "cache_cambio.db")

MOEDA_PADRAO = "USD"

# API externa usada para consultar cotações (AwesomeAPI, gratuita, sem chave)
AWESOME_API_BASE_URL = "https://economia.awesomeapi.com.br"
