# app.py
from flask import Flask, redirect, url_for, request, render_template, session, flash
from models import *
from flask_dance.contrib.google import make_google_blueprint, google
from routes import routes
from api_estudiante import api_estudiante
from dotenv import load_dotenv
# Migraciones
from flask_migrate import Migrate
import os

load_dotenv()

# Obtén la ruta absoluta de la raíz del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__)

app.config['CERTIFICADOS_DIR'] = os.path.join(app.root_path, 'uploads', 'certificados')

# --- CONFIGURACIÓN DE LA BASE DE DATOS  PRODUCCION RENDER---
# Lee la variable de entorno que le diremos más adelante
DATABASE_URL = os.environ.get('DATABASE_URI')
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URI no está configurada.")

# USAR DB LOCAL ------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'usuarios.db')
print("SQLALCHEMY_DATABASE_URI:", app.config['SQLALCHEMY_DATABASE_URI'])

#---------------------------------------
# USAR DB RENDER ONLINE ----------------
#app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
#app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
#---------------------------------------
# --- FIN CONFIGURACIÓN BASE DE DATOS ---
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'sgaabs123'
migrate = Migrate(app, db) # Migracion DB

db.init_app(app)
app.register_blueprint(routes)
# Registrar el blueprint del API de estudiantes
app.register_blueprint(api_estudiante)

# Permitir OAuth en HTTP (solo en desarrollo)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Configuración de Google OAuth
# Configurar el blueprint correctamente

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')

google_bp = make_google_blueprint(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    redirect_to='routes.google_login_callback',  # tu callback
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
    ],
)

# registrar con el prefijo que coincide con tu redirect URI en Google:
app.register_blueprint(google_bp, url_prefix="/google_login")

# imprimir URIs dentro de un contexto de prueba (usa la base_url que registraste en Google)
with app.test_request_context(base_url='http://127.0.0.1:5000'):
    print("Google login URI:", url_for('google.login', _external=True))
    print("Google authorized URI:", url_for('google.authorized', _external=True))
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
