import sys
import os
from datetime import date
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Asistencia, Estudiante, Curso

with app.app_context():
    curso_id = 1  # Cambia por el ID real del curso
    fecha_clase = date(2025, 10, 6)  # Fecha de la clase

    curso = Curso.query.get(curso_id)
    programa_curso = curso.modulo.programa.nombre  # Obtén el nombre del programa del curso
    matriculas = curso.modulo.matriculas  # Ajusta según tu modelo

    for matricula in matriculas:
        estudiante = Estudiante.query.get(matricula.estudiante_id)
        if not estudiante:
            continue
        if estudiante.programa_estudio != programa_curso:
            continue
        asistencia = Asistencia(
            estudiante_id=matricula.estudiante_id,
            curso_id=curso_id,
            fecha=fecha_clase,
            estado='asistio',  # o 'falta'
            justificada=False,
            observacion=""
        )
        db.session.add(asistencia)

    db.session.commit()
    print("¡Asistencias registradas exitosamente solo para estudiantes del programa correcto!")