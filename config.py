import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.environ.get("FINANCAS_DATABASE_PATH", os.path.join(BASE_DIR, "financas.db"))

# Endereço do módulo proxy/cache de câmbio (serviço em cambio/)
CAMBIO_SERVICE_URL = os.environ.get("CAMBIO_SERVICE_URL", "http://localhost:5001")
CAMBIO_TIMEOUT_SEGUNDOS = 15

PORTA = 5000
