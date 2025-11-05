import sys
import os
import datetime
import random
from itertools import cycle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import (
    Salon, Docente, Curso, Modulo, Programa, ProgramacionClase, 
    Periodo, ModuloActivo, CursoActivo
)

def generar_horario_aleatorio():
    """Genera horarios aleatorios con duración mínima de 30 minutos"""
    # Horas disponibles de 7:00 AM a 9:00 PM
    hora_inicio = random.randint(7, 20)
    minuto_inicio = random.choice([0, 30])
    
    # Duración entre 30 minutos y 3 horas (en incrementos de 30 minutos)
    duraciones = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    duracion = random.choice(duraciones)
    
    # Calcular hora de fin
    hora_fin_decimal = hora_inicio + (minuto_inicio / 60) + duracion
    hora_fin = int(hora_fin_decimal)
    minuto_fin = int((hora_fin_decimal - hora_fin) * 60)
    
    # Asegurar que no pase de las 21:00 (9:00 PM)
    if hora_fin > 21 or (hora_fin == 21 and minuto_fin > 0):
        hora_fin = 21
        minuto_fin = 0
    
    return (
        datetime.time(hora_inicio, minuto_inicio),
        datetime.time(hora_fin, minuto_fin)
    )

def horario_superpuesto(existing_schedules, dia, nueva_hora_inicio, nueva_hora_fin):
    """Verifica si un nuevo horario se superpone con horarios existentes"""
    for schedule in existing_schedules:
        if schedule.dia_semana == dia:
            existente_inicio = datetime.datetime.combine(datetime.date.today(), schedule.hora_inicio)
            existente_fin = datetime.datetime.combine(datetime.date.today(), schedule.hora_fin)
            nuevo_inicio = datetime.datetime.combine(datetime.date.today(), nueva_hora_inicio)
            nuevo_fin = datetime.datetime.combine(datetime.date.today(), nueva_hora_fin)
            
            # Verificar superposición
            if (nuevo_inicio < existente_fin and nuevo_fin > existente_inicio):
                return True
    return False

with app.app_context():
    # =======================
    # 1️⃣ CREAR SALÓN BASE
    # =======================
    salon = Salon.query.first()
    if not salon:
        salon = Salon(
            nombre="Aula 101",
            capacidad=30,
            caracteristicas="Proyector, Pizarra",
            fecha_registro=datetime.date.today()
        )
        db.session.add(salon)
        db.session.commit()
        print(f"✅ Salón creado: {salon.nombre}")
    else:
        print(f"✅ Salón existente: {salon.nombre}")

    # =======================
    # 2️⃣ VALIDAR DOCENTE BASE
    # =======================
    docente = Docente.query.first()
    if not docente:
        print("❌ No hay docentes en la base de datos. No se puede continuar.")
        exit()
    else:
        print(f"👨‍🏫 Docente asignado: {docente.nombre_completo}")

    # =======================
    # 3️⃣ VALIDAR PERIODOS
    # =======================
    periodos = Periodo.query.all()
    if not periodos:
        print("❌ No hay periodos creados. Crea los periodos antes de ejecutar este script.")
        exit()
    else:
        print(f"📅 Se encontraron {len(periodos)} periodos registrados.")

    # =======================
    # 4️⃣ DEFINIR DÍAS Y HORARIOS ALEATORIOS
    # =======================
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
    
    # Diccionario para llevar control de horarios por día y salón
    horarios_existentes = {}

    # =======================
    # 5️⃣ PROCESAR PROGRAMAS
    # =======================
    programas = Programa.query.all()
    if not programas:
        print("❌ No hay programas registrados en la base de datos.")
        exit()

    for programa in programas:
        print(f"\n==============================")
        print(f"📘 Procesando programa: {programa.nombre}")
        print(f"==============================")

        modulos = Modulo.query.filter_by(programa_id=programa.id).all()
        if not modulos:
            print(f"⚠️ No hay módulos para el programa {programa.nombre}.")
            continue

        for modulo in modulos:
            print(f"→ Módulo: {modulo.nombre}")

            # ===============================
            # Crear o recuperar MóduloActivo
            # ===============================
            periodo = periodos[(modulo.num_modulo - 1) % len(periodos)]

            modulo_activo = ModuloActivo.query.filter_by(
                programa_id=programa.id,
                modulo_id=modulo.id,
                periodo_id=periodo.id
            ).first()

            if not modulo_activo:
                fecha_inicio = periodo.fecha_inicio or datetime.date.today()
                fecha_fin = periodo.fecha_fin or (fecha_inicio + datetime.timedelta(days=120))

                modulo_activo = ModuloActivo(
                    programa_id=programa.id,
                    modulo_id=modulo.id,
                    periodo_id=periodo.id,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    estado="activo"
                )
                db.session.add(modulo_activo)
                db.session.commit()
                print(f"   ✅ MóduloActivo creado: {modulo.nombre} en periodo {periodo.codigo}")
            else:
                print(f"   ✅ MóduloActivo existente ({periodo.codigo})")

            # ===============================
            # Crear CursoActivo por cada Curso
            # ===============================
            cursos = Curso.query.filter_by(modulo_id=modulo.id).all()
            if not cursos:
                print(f"   ⚠️ No hay cursos en el módulo {modulo.nombre}.")
                continue

            for curso in cursos:
                curso_activo = CursoActivo.query.filter_by(
                    modulo_activo_id=modulo_activo.id,
                    curso_id=curso.id
                ).first()

                if not curso_activo:
                    curso_activo = CursoActivo(
                        modulo_activo_id=modulo_activo.id,
                        curso_id=curso.id,
                        docente_id=docente.id
                    )
                    db.session.add(curso_activo)
                    db.session.commit()
                    print(f"      ➕ CursoActivo creado: {curso.nombre}")
                else:
                    print(f"      ✅ CursoActivo existente: {curso.nombre}")

                # ===============================
                # Crear Programación de Clase
                # ===============================
                # Obtener horarios existentes para este salón
                if salon.id not in horarios_existentes:
                    horarios_existentes[salon.id] = ProgramacionClase.query.filter_by(
                        salon_id=salon.id
                    ).all()

                # Crear múltiples sesiones por curso (entre 1 y 3 sesiones semanales)
                num_sesiones = random.randint(1, 3)
                sesiones_creadas = 0
                intentos_maximos = 20  # Para evitar bucles infinitos
                intentos = 0

                while sesiones_creadas < num_sesiones and intentos < intentos_maximos:
                    intentos += 1
                    
                    # Seleccionar día aleatorio
                    dia = random.choice(dias)
                    
                    # Generar horario aleatorio
                    hora_inicio, hora_fin = generar_horario_aleatorio()
                    
                    # Verificar si ya existe esta programación exacta
                    existe = ProgramacionClase.query.filter_by(
                        curso_activo_id=curso_activo.id,
                        salon_id=salon.id,
                        dia_semana=dia,
                        hora_inicio=hora_inicio
                    ).first()

                    if existe:
                        continue

                    # Verificar superposición con otros horarios
                    if horario_superpuesto(horarios_existentes[salon.id], dia, hora_inicio, hora_fin):
                        continue

                    # Crear nueva programación
                    nueva_prog = ProgramacionClase(
                        dia_semana=dia,
                        hora_inicio=hora_inicio,
                        hora_fin=hora_fin,
                        curso_activo_id=curso_activo.id,
                        salon_id=salon.id,
                        docente_id=docente.id
                    )
                    db.session.add(nueva_prog)
                    db.session.commit()
                    
                    # Agregar a la lista de horarios existentes
                    horarios_existentes[salon.id].append(nueva_prog)
                    
                    duracion_minutos = (hora_fin.hour * 60 + hora_fin.minute) - (hora_inicio.hour * 60 + hora_inicio.minute)
                    print(f"         🕓 Programación creada para {curso.nombre} ({dia} de {hora_inicio.strftime('%H:%M')} a {hora_fin.strftime('%H:%M')}) - Duración: {duracion_minutos} min")
                    
                    sesiones_creadas += 1
                    intentos = 0  # Resetear intentos para la siguiente sesión

                if sesiones_creadas == 0:
                    print(f"         ⚠️ No se pudieron crear sesiones para {curso.nombre} (muchas superposiciones)")

    print("\n🎉 ¡Todas las programaciones se han creado correctamente!")
    print("📊 Resumen de características:")
    print("   • Horarios aleatorios entre 7:00 AM y 9:00 PM")
    print("   • Duración mínima de 30 minutos")
    print("   • Múltiples sesiones por curso (1-3 por semana)")
    print("   • Verificación de superposición de horarios")
    print("   • Incluye sábados como día disponible")