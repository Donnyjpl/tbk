import os
from django.core.wsgi import get_wsgi_application
import environ

# Inicializar el entorno de django-environ
env = environ.Env()

# Obtener la ruta al archivo .env
env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')

# Leer el archivo .env
env.read_env(env_file)

# Configurar la clave secreta desde las variables de entorno (si es necesario)
os.environ['SECRET_KEY'] = env('SECRET_KEY')

# Establecer el módulo de configuración de Django (asegúrate de tener este archivo de settings correcto)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tbk.settings")

# Inicializar la aplicación WSGI
application = get_wsgi_application()

