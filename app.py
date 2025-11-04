# app.py
from flask import Flask, redirect, url_for, request, render_template, session, flash
from models import db, Usuario
from flask_dance.contrib.google import make_google_blueprint, google
from routes import routes
from flask_cors import CORS
from api_estudiantes import api_estudiantes

import os

# Obtén la ruta absoluta de la raíz del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=[
    "http://localhost:5173",  # React (desarrollo)
    "http://127.0.0.1:5173"   # por si acaso
])
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'usuarios.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'sgaabs123'

db.init_app(app)
app.register_blueprint(routes)
# Registrar el blueprint del API de estudiantes
app.register_blueprint(api_estudiantes)

# Permitir OAuth en HTTP (solo en desarrollo)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Configuración de Google OAuth
# Configurar el blueprint correctamente

google_bp = make_google_blueprint(
    client_id='699371939814-lu4n3gkei4ms8uad4922rhrne2241avt.apps.googleusercontent.com',
    client_secret='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',
    redirect_to = 'routes.google_login_callback',
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
    ], # Google ahora requiere valores exactos
)

app.register_blueprint(google_bp, url_prefix="/login")

if __name__ == '__main__':
    app.run(debug=True)
