import environ
import os

# Inicializar el objeto de entorno
env = environ.Env()

# Especificar explícitamente la ruta al archivo .env
env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')

# Leer el archivo .env
env.read_env(env_file)

# Verificar que la variable SECRET_KEY está cargada
print("SECRET_KEY:", env('SECRET_KEY'))
