import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Usuario, Administrador
from werkzeug.security import generate_password_hash

admins_data = [
    {
        "usuario": "admin1",
        "password": "admin123",
        "email": "admin1@cedhinuevaarequipa.edu.pe",
        "rol": "administrador",
        "cargo": "Coordinador General"
    },
    {
        "usuario": "admin2",
        "password": "admin123",
        "email": "admin2@cedhinuevaarequipa.edu.pe",
        "rol": "administrador",
        "cargo": "Administrador Académico"
    },
]

with app.app_context():
    for a in admins_data:
        # Verificar si el usuario ya existe
        usuario = Usuario.query.filter_by(email=a["email"]).first()
        if not usuario:
            usuario = Usuario(
                usuario=a["usuario"],
                password=generate_password_hash(a["password"]),
                email=a["email"],
                rol=a["rol"]
            )
            db.session.add(usuario)
            db.session.commit()
            print(f"Usuario {a['usuario']} creado.")

        # Verificar si el administrador ya existe
        admin = Administrador.query.filter_by(id=usuario.id).first()
        if not admin:
            admin = Administrador(
                id=usuario.id,
                cargo=a["cargo"]
            )
            db.session.add(admin)
            db.session.commit()
            print(f"Administrador {a['usuario']} creado con cargo {a['cargo']}.")
