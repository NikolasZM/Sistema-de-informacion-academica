import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from app import app, db
from models import Usuario, Estudiante, EstudianteInfo
from werkzeug.security import generate_password_hash
from datetime import datetime

# Datos de los estudiantes
estudiantes_data = [
    {
        "programa": "Estilismo",
        "apellidos": "Huisa Achinquipa",
        "nombres": "Lizbeth Milagros",
        "sexo": "FEMENINO",
        "fecha_nacimiento": "1/06/1997",
        "dni": "70583779",
        "departamento": "Madre de Dios",
        "provincia": "Madre de Dios",
        "distrito": "Manu",
        "celular": "921208426",
        "direccion": "Asoc. Jorge Chávez Mz.M Lte.9",
    },
    {
        "programa": "Estilismo",
        "apellidos": "Urbina Panta",
        "nombres": "Maria Fernanda",
        "sexo": "FEMENINO",
        "fecha_nacimiento": "1/07/2006",
        "dni": "63444151",
        "departamento": "Arequipa",
        "provincia": "Arequipa",
        "distrito": "Arequipa",
        "celular": "936939668",
        "direccion": "Perú Arequipa Yura",
    },
    {
        "programa": "Estilismo",
        "apellidos": "Gutierrez Gutierrez",
        "nombres": "Luz Yamela",
        "sexo": "FEMENINO",
        "fecha_nacimiento": "26/09/2006",
        "dni": "60452966",
        "departamento": "Arequipa",
        "provincia": "Puno",
        "distrito": "Nuñoa",
        "celular": "926728477",
        "direccion": "Apipa sec 10 mzB2 Lt15",
    },
    {
        "programa": "Estilismo",
        "apellidos": "Quispe Carrasco",
        "nombres": "Tania Andrea",
        "sexo": "FEMENINO",
        "fecha_nacimiento": "22/11/2007",
        "dni": "62652714",
        "departamento": "Arequipa",
        "provincia": "Arequipa",
        "distrito": "Cercado",
        "celular": "967945417",
        "direccion": "Arequipa, Yura, ciudad de Dios manzana W lote 4 comité 5",
    },
    {
        "programa": "Estilismo",
        "apellidos": "Merma Chipa",
        "nombres": "Marisol Gianinna",
        "sexo": "FEMENINO",
        "fecha_nacimiento": "10/11/2006",
        "dni": "76741525",
        "departamento": "Arequipa",
        "provincia": "Caylloma",
        "distrito": "Caylloma",
        "celular": "920218225",
        "direccion": "Asoc. de vivienda Utupara Avanza zona D mz D LT 15",
    },
    {
        "programa": "Estilismo",
        "apellidos": "Quispe Lima",
        "nombres": "Karolina Irma",
        "sexo": "FEMENINO",
        "fecha_nacimiento": "21/12/1994",
        "dni": "48575089",
        "departamento": "Arequipa",
        "provincia": "Arequipa",
        "distrito": "Arequipa",
        "celular": "990113172",
        "direccion": "Pueblo joven Juan Pablo II MZ:k lt:3",
    },
    {
        "programa": "Computación e Informática (Plataformas y Servicios de TI)",
        "apellidos": "Salas Eguiluz",
        "nombres": "Alisson Cristhya",
        "sexo": "FEMENINO",
        "fecha_nacimiento": "1/04/1995",
        "dni": "71334625",
        "departamento": "Arequipa",
        "provincia": "Arequipa",
        "distrito": "Arequipa",
        "celular": "914136798",
        "direccion": "Asoc. Vic. Transoceanica F-16 Cerro Colorado",
    },
    {
        "programa": "Estilismo",
        "apellidos": "Ttupa Huaman",
        "nombres": "Elizabeth Charo",
        "sexo": "FEMENINO",
        "fecha_nacimiento": "4/08/2004",
        "dni": "76361311",
        "departamento": "Cusco",
        "provincia": "Cusco",
        "distrito": "Santiago",
        "celular": "900560044",
        "direccion": "Apipa sector 6",
    },
    {
        "programa": "Computación e Informática (Plataformas y Servicios de TI)",
        "apellidos": "Ramírez Cruz",
        "nombres": "Jaime",
        "sexo": "MASCULINO",
        "fecha_nacimiento": "3/09/2001",
        "dni": "76880525",
        "departamento": "Puno",
        "provincia": "Azángaro",
        "distrito": "Azángaro",
        "celular": "900333261",
        "direccion": "Villa San Juan G-11 - Cerro Colorado",
    },
    {
        "programa": "Estilismo",
        "apellidos": "Pari Huayta",
        "nombres": "Rubí",
        "sexo": "FEMENINO",
        "fecha_nacimiento": "18/09/2004",
        "dni": "74062682",
        "departamento": "Arequipa",
        "provincia": "Arequipa",
        "distrito": "Yanahuara",
        "celular": "942198193",
        "direccion": "Asoc. Ciudad de Dios M.A Lt.2 Cm17 Zona2 Yura",
    },
    {
        "programa": "Estilismo",
        "apellidos": "Pacompia Mamani",
        "nombres": "Magaly",
        "sexo": "FEMENINO",
        "fecha_nacimiento": "25/12/1998",
        "dni": "77687098",
        "departamento": "Arequipa",
        "provincia": "Arequipa",
        "distrito": "Jacobo Hunter",
        "celular": "914703009",
        "direccion": "Ampliación pampa del Cuzco AV. Tahuantinsuyo p-9",
    },
    {
        "programa": "Estilismo",
        "apellidos": "Cayllahua Quenta",
        "nombres": "Monica Lizbeth",
        "sexo": "FEMENINO",
        "fecha_nacimiento": "16/06/2007",
        "dni": "60177573",
        "departamento": "Puno",
        "provincia": "Melgar",
        "distrito": "Orurillo",
        "celular": "927968800",
        "direccion": "Asociación vivienda taller nueva estrella",
    },
    {
        "programa": "Computación e Informática (Plataformas y Servicios de TI)",
        "apellidos": "Pacheco Huaira",
        "nombres": "Kelly Isabel",
        "sexo": "FEMENINO",
        "fecha_nacimiento": "3/08/2004",
        "dni": "75223692",
        "departamento": "Arequipa",
        "provincia": "Arequipa",
        "distrito": "Hunter",
        "celular": "946482605",
        "direccion": "Prq. Tupac Amaru mz.56 lt.13 Simón Bolivar - José Luis Bustamante y Rivero",
    },
]

# Inserción de datos
with app.app_context():
    for d in estudiantes_data:
        nombre_completo = f"{d['apellidos']} {d['nombres']}".strip()
        codigo = f"EST-{d['dni']}"
        usuario_nombre = d['nombres'].split()[0].lower() + d['dni'][-3:]
        email_institucional = f"{usuario_nombre}@cedhi.edu.pe"
        password_hash = generate_password_hash("123456")

        # Convertir fecha de nacimiento a formato correcto
        try:
            fecha_nac = datetime.strptime(d["fecha_nacimiento"], "%d/%m/%Y").date()
        except ValueError:
            # algunos formatos pueden venir con 1/06/1997 o 01/06/1997
            fecha_nac = datetime.strptime(d["fecha_nacimiento"].replace(" ", ""), "%d/%m/%Y").date()

        # Crear usuario
        usuario = Usuario(
            usuario=usuario_nombre,
            password=password_hash,
            email=email_institucional,
            rol="estudiante"
        )
        db.session.add(usuario)
        db.session.commit()

        # Crear estudiante
        estudiante = Estudiante(
            id=usuario.id,
            nombre_completo=nombre_completo,
            programa_estudio=d["programa"],
            codigo=codigo,
            dni=d["dni"],
            sexo=d["sexo"],
            fecha_nacimiento=fecha_nac
        )
        db.session.add(estudiante)
        db.session.commit()

        # Crear información adicional
        info = EstudianteInfo(
            estudiante_id=estudiante.id,
            direccion=d["direccion"],
            departamento=d["departamento"],
            provincia=d["provincia"],
            distrito=d["distrito"],
            celular=d["celular"]
        )
        db.session.add(info)
        db.session.commit()

        print(f"✅ Estudiante {nombre_completo} creado con usuario {usuario_nombre} ({email_institucional})")

print("✅ Todos los estudiantes han sido insertados correctamente.")
