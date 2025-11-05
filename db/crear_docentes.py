import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Usuario, Docente
from werkzeug.security import generate_password_hash
from datetime import datetime

docentes_data = [
    {
        "usuario": "jgonzalez",
        "password": "docente123",
        "email": "jcrespo@cedhinuevaarequipa.edu.pe",
        "rol": "docente",
        "nombre_completo": "Padre Jose Gonzalez Crespo",
        "dni": "00084560",
        "celular": "903366182",
        "correo_personal": "josegonzalezcrespo2021@gmail.com",
        "fecha_nacimiento": "1993-10-04"
    },
    {
        "usuario": "cramirez",
        "password": "docente123",
        "email": "cramirez@cedhinuevaarequipa.edu.pe",
        "rol": "docente",
        "nombre_completo": "César Mezzich Ramírez Vargas",
        "dni": "44379075",
        "celular": "959116855",
        "correo_personal": "cesar.ramirezva@gmail.com",
        "fecha_nacimiento": "1987-05-07"
    },
    {
        "usuario": "ediana",
        "password": "docente123",
        "email": "dnunnez@cedhinuevaarequipa.edu.pe",
        "rol": "docente",
        "nombre_completo": "Diana Elizabeth Núñez Linares",
        "dni": "46309146",
        "celular": "959481764",
        "correo_personal": "gloomy1989@gmail.com",
        "fecha_nacimiento": "1989-05-09"
    },
    {
        "usuario": "herbert1",
        "password": "docente123",
        "email": "hayala@cedhinuevaarequipa.edu.pe",
        "rol": "docente",
        "nombre_completo": "Herbert José Ayala Cervantes",
        "dni": "42327887",
        "celular": "974291497",
        "correo_personal": "herbertjoseayala@hotmail.com",
        "fecha_nacimiento": "1984-03-19"
    },
    {
        "usuario": "jesus1",
        "password": "docente123",
        "email": "jgonzales@cedhinuevaarequipa.edu.pe",
        "rol": "docente",
        "nombre_completo": "Jesús Alberto Gonzales Silva",
        "dni": "29596165",
        "celular": "939773508",
        "correo_personal": "jesusitodivino@hotmail.com",
        "fecha_nacimiento": "1971-07-29"
    },
    {
        "usuario": "yessy1",
        "password": "docente123",
        "email": "yrodriguez@cedhinuevaarequipa.edu.pe",
        "rol": "docente",
        "nombre_completo": "Yessy Elizabeth Rodriguez Rodriguez",
        "dni": "30675024",
        "celular": "959292712",
        "correo_personal": "Yesitarr_enyee@hotmail.com",
        "fecha_nacimiento": "1976-01-05"
    },
]

with app.app_context():
    for d in docentes_data:
        # Crear usuario si no existe
        usuario = Usuario.query.filter_by(email=d["email"]).first()
        if not usuario:
            usuario = Usuario(
                usuario=d["usuario"],
                password=generate_password_hash(d["password"]),
                email=d["email"],
                rol=d["rol"]
            )
            db.session.add(usuario)
            db.session.commit()
            print(f"Usuario {d['usuario']} creado.")
        # Crear docente si no existe
        docente = Docente.query.filter_by(id=usuario.id).first()
        if not docente:
            docente = Docente(
                id=usuario.id,
                nombre_completo=d["nombre_completo"],
                dni=d["dni"],
                celular=d["celular"],
                correo_personal=d["correo_personal"],
                fecha_nacimiento=datetime.strptime(d["fecha_nacimiento"], "%Y-%m-%d").date()
            )
            db.session.add(docente)
            db.session.commit()
            print(f"Docente {d['nombre_completo']} creado.")