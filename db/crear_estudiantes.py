import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Usuario, Estudiante, EstudianteInfo
from werkzeug.security import generate_password_hash
from datetime import datetime

# --- Datos completos de los estudiantes ---
estudiantes_data = [
    {
        "programa": "Estilismo",
        "apellidos": "Huisa Achinquipa",
        "nombres": "Lizbeth Milagros",
        "sexo": "FEMENINO",
        "fecha_nacimiento": "1/6/1997",
        "dni": "70583779",
        "pais_nacimiento": "Perú",
        "departamento": "Madre de Dios",
        "provincia": "Madre de Dios",
        "distrito": "Manu",
        "esta_trabajando": "SI",
        "centro_trabajo": "Liv",
        "puesto_trabajo": "Operario de limpieza",
        "estado_civil": "SOLTERO",
        "numero_hijos": 2,
        "celular": "921208426",
        "direccion": "Asoc. Jorge Chávez Mz.M Lte.9",
        "nivel_educacion": "Secundaria Completa",
        "nombre_colegio": "Metropolitano",
        "celular_familiar_contacto": "996192886",
        "link_foto_dni": "https://drive.google.com/open?id=1XRzavnsRvPjll9eeZDxLLNmb7Atzv6Tj",
        "medio_conocimiento": "OTROS",
        "correo": "lizbeth.huisa@cedhinuevaarequipa.edu.pe"
        
    },
    {
        "programa": "Estilismo",
        "apellidos": "Urbina Panta",
        "nombres": "Maria Fernanda",
        "sexo": "FEMENINO",
        "fecha_nacimiento": "1/7/2006",
        "dni": "63444151",
        "pais_nacimiento": "Perú",
        "departamento": "Arequipa",
        "provincia": "Arequipa",
        "distrito": "Arequipa",
        "esta_trabajando": "SI",
        "centro_trabajo": "Valerianos",
        "puesto_trabajo": "Pastelería",
        "estado_civil": "SOLTERO",
        "numero_hijos": 0,
        "celular": "936939668",
        "direccion": "Perú Arequipa Yura",
        "nivel_educacion": "Secundaria Completa",
        "nombre_colegio": "Altiplano",
        "celular_familiar_contacto": "932511560",
        "link_foto_dni": "https://drive.google.com/open?id=1kst1tm705D9FKMByXq1ggBToNrJyVrH6",
        "medio_conocimiento": "FACEBOOK",
        "correo": "maria.urbina@cedhinuevaarequipa.edu.pe"
    },
    {
        "programa": "Estilismo",
        "apellidos": "Gutierrez Gutierrez",
        "nombres": "Luz Yamela",
        "sexo": "FEMENINO",
        "fecha_nacimiento": "26/9/2006",
        "dni": "60452966",
        "pais_nacimiento": "Perú",
        "departamento": "Arequipa",
        "provincia": "Puno",
        "distrito": "Nuñoa",
        "esta_trabajando": "NO",
        "centro_trabajo": None,
        "puesto_trabajo": None,
        "estado_civil": "SOLTERO",
        "numero_hijos": 0,
        "celular": "926728477",
        "direccion": "Apipa sec 10 mzB2 Lt15",
        "nivel_educacion": "Secundaria Completa",
        "nombre_colegio": "José Luis Bustamante y Rivero",
        "celular_familiar_contacto": "973115869",
        "link_foto_dni": "https://drive.google.com/open?id=1AV7DmahR82Ams_8zZdq87XCJnqmN5NYp",
        "medio_conocimiento": "FACEBOOK",
        "correo": "luz.gutierrez@cedhinuevaarequipa.edu.pe"
    }
]

# --- Inserción de datos ---
with app.app_context():
    for d in estudiantes_data:
        nombre_completo = f"{d['apellidos']} {d['nombres']}".strip()
        codigo = f"EST-{d['dni']}"
        password_hash = generate_password_hash("123456")

        # Parsear fecha de nacimiento (acepta formatos 1/6/1997 o 01/06/1997)
        fecha_nac = datetime.strptime(d["fecha_nacimiento"].replace(" ", ""), "%d/%m/%Y").date()

        # Crear usuario base
        usuario = Usuario(
            usuario=d["dni"],  
            password=password_hash,
            email=d["correo"],  # correo institucional
            rol="estudiante"
        )
        db.session.add(usuario)
        db.session.commit()

        # Crear estudiante
        estudiante = Estudiante(
            id=usuario.id,
            apellidos=d["apellidos"],
            nombre_completo=nombre_completo,
            programa_estudio=d["programa"],
            dni=d["dni"],
            sexo=d["sexo"],
            fecha_nacimiento=fecha_nac,
            correo=d["correo"],
            pais_nacimiento=d["pais_nacimiento"],
            departamento_nacimiento=d["departamento"],
            provincia_nacimiento=d["provincia"],
            distrito_nacimiento=d["distrito"],
            esta_trabajando=(d["esta_trabajando"].upper() == "SI"),
            centro_trabajo=d.get("centro_trabajo"),
            puesto_trabajo=d.get("puesto_trabajo"),
            nivel_educacion=d["nivel_educacion"],
            nombre_colegio=d["nombre_colegio"],
            estado_civil=d["estado_civil"],
            numero_hijos=d["numero_hijos"],
            celular=d["celular"],
            domicilio=d["direccion"],
            celular_familiar_contacto=d["celular_familiar_contacto"],
            link_foto_dni=d["link_foto_dni"],
            medio_conocimiento=d["medio_conocimiento"]
        )

        db.session.add(estudiante)
        db.session.commit()

        print(f"✅ Estudiante {nombre_completo} creado con correo institucional {d['correo']}")

print("✅ Todos los estudiantes han sido insertados correctamente.")
