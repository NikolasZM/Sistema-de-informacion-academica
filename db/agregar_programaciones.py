import sys
import os
import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Salon, Docente, Curso, Modulo, Programa, ProgramacionClase

with app.app_context():
    # Crear un salón si no existe
    salon = Salon.query.first()
    if not salon:
        salon = Salon(nombre="Aula 101", capacidad=30, caracteristicas="Proyector, Pizarra")
        db.session.add(salon)
        db.session.commit()

    docente = Docente.query.first()
    if not docente:
        print("No hay docentes en la base de datos.")
        exit()

    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
    horas = [(8, 10), (10, 12), (12, 14), (14, 16), (16, 18)]
    idx = 0

    programas = Programa.query.all()
    for programa in programas:
        print(f"Procesando programa: {programa.nombre}")
        modulos = Modulo.query.filter_by(programa_id=programa.id).all()
        for modulo in modulos:
            cursos = Curso.query.filter_by(modulo_id=modulo.id).all()
            for curso in cursos:
                dia = dias[idx % len(dias)]
                h_inicio, h_fin = horas[idx % len(horas)]
                existe = ProgramacionClase.query.filter_by(
                    salon_id=salon.id,
                    dia_semana=dia,
                    hora_inicio=datetime.time(h_inicio, 0),
                    hora_fin=datetime.time(h_fin, 0),
                    periodo_academico=modulo.periodo_academico
                ).first()
                if existe:
                    print(f"Ya existe programación para el salón {salon.nombre} en ese horario.")
                    idx += 1
                    continue
                nueva_programacion = ProgramacionClase(
                    dia_semana=dia,
                    hora_inicio=datetime.time(h_inicio, 0),
                    hora_fin=datetime.time(h_fin, 0),
                    periodo_academico=modulo.periodo_academico,
                    curso_id=curso.id,
                    salon_id=salon.id,
                    docente_id=docente.id
                )
                db.session.add(nueva_programacion)
                print(f"Programación creada para curso: {curso.nombre} (Programa: {programa.nombre}) en {dia} de {h_inicio}:00 a {h_fin}:00")
                idx += 1
    db.session.commit()
    print("¡Programaciones creadas para todos los cursos de ambos programas!")