import sys
import os
import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import ProgramacionClase, Curso, Salon, Docente, Modulo

with app.app_context():
    curso = Curso.query.first()  # Elige el curso que quieras asignar
    salon = Salon.query.first()
    docente = Docente.query.first()  # Elige el docente que quieras asignar
    modulo = Modulo.query.get(curso.modulo_id)

    prog = ProgramacionClase(
        dia_semana="Lunes",
        hora_inicio=datetime.time(8, 0),
        hora_fin=datetime.time(10, 0),
        periodo_academico=modulo.periodo_academico,
        curso_id=curso.id,
        salon_id=salon.id,
        docente_id=docente.id
    )
    db.session.add(prog)
    db.session.commit()
    print(f"¡Curso '{curso.nombre}' asignado al docente '{docente.nombre_completo}' en el salón '{salon.nombre}'!")