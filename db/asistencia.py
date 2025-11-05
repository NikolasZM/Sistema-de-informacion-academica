import sys
import os
from datetime import date
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import (
    Asistencia,
    Estudiante,
    Curso,
    CursoActivo,
    MatriculaCurso,
    Matricula
)

with app.app_context():
    curso_id = 1  # Cambia por el ID real del curso
    fecha_clase = date(2025, 10, 6)  # Fecha de la clase

    # Obtener curso y su información base
    curso = Curso.query.get(curso_id)
    if not curso:
        print(f"❌ No se encontró el curso con ID {curso_id}.")
        exit()

    # Buscar el curso activo correspondiente (puede haber varios, elegimos el primero activo)
    curso_activo = CursoActivo.query.filter_by(curso_id=curso_id).first()
    if not curso_activo:
        print(f"❌ No se encontró un curso activo asociado al curso '{curso.nombre}'.")
        exit()

    # Determinar el programa asociado al curso (a través del módulo)
    programa_curso = curso.modulo.programa.nombre
    print(f"🧩 Curso: {curso.nombre} | Programa: {programa_curso}")

    # Obtener las matrículas relacionadas al módulo activo
    matriculas = Matricula.query.filter_by(modulo_activo_id=curso_activo.modulo_activo_id, estado='activa').all()
    if not matriculas:
        print("⚠️ No hay estudiantes matriculados en este curso activo.")
        exit()

    count = 0
    for matricula in matriculas:
        estudiante = matricula.estudiante
        if not estudiante:
            continue

        # Filtrar solo estudiantes que pertenecen al mismo programa
        if estudiante.programa_estudio != programa_curso:
            continue

        # Buscar el detalle de matrícula para este curso activo
        matricula_curso = MatriculaCurso.query.filter_by(
            matricula_id=matricula.id,
            curso_activo_id=curso_activo.id
        ).first()

        if not matricula_curso:
            print(f"⚠️ El estudiante {estudiante.nombre_completo} no tiene registro para este curso activo.")
            continue

        # Evitamos duplicar asistencias para esa fecha
        asistencia_existente = Asistencia.query.filter_by(
            matricula_curso_id=matricula_curso.id,
            fecha=fecha_clase
        ).first()
        if asistencia_existente:
            continue

        # Crear el registro de asistencia
        nueva_asistencia = Asistencia(
            matricula_curso_id=matricula_curso.id,
            fecha=fecha_clase,
            estado='asistio',  # o 'falta', según corresponda
            justificada=False,
            observacion=""
        )
        db.session.add(nueva_asistencia)
        count += 1

    db.session.commit()
    print(f"✅ {count} asistencias registradas exitosamente para el curso '{curso.nombre}' ({programa_curso}).")
