from flask import Blueprint, jsonify, session
from models import *
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

api_estudiantes = Blueprint('api_estudiantes', __name__)

@api_estudiantes.route('/api/estudiante/info', methods=['GET'])
def get_estudiante_info():
    print("user_id en sesión:", session.get('user_id'))
    user_id = session.get('user_id')
    rol = session.get('rol')

    if not user_id or rol != 'estudiante':
        return jsonify({"error": "No autenticado"}), 401

    estudiante = Estudiante.query.filter_by(id=user_id).first()
    if not estudiante:
        return jsonify({"error": "Estudiante no encontrado"}), 404

    print("Estudiante encontrado:", estudiante.nombre_completo)
    # Si tiene datos adicionales (EstudianteInfo), los traemos
    info = estudiante.info
    info_data = {
        # --- Domicilio ---
        "direccion": info.direccion if info else None,
        "departamento": info.departamento if info else None,
        "provincia": info.provincia if info else None,
        "distrito": info.distrito if info else None,
        "celular": info.celular if info else None, # Celular del estudiante
        
        # --- Contacto 1 (¡NUEVOS CAMPOS!) ---
        "c1_nombre": info.contacto_nombre if info else None,
        "c1_parentesco": info.contacto_parentesco if info else None,
        "c1_celular": info.contacto_telefono if info else None,
        
        # --- Contacto 2 (¡NUEVOS CAMPOS!) ---
        "c2_nombre": info.contacto_nombre_2 if info else None,
        "c2_parentesco": info.contacto_parentesco_2 if info else None,
        "c2_celular": info.contacto_telefono_2 if info else None,
    }

    return jsonify({
        "id": estudiante.id,
        "nombre_completo": estudiante.nombre_completo,
        "programa_estudio": estudiante.programa_estudio,
        "codigo": estudiante.codigo,
        "dni": estudiante.dni,
        "sexo": estudiante.sexo,
        "fecha_nacimiento": estudiante.fecha_nacimiento.strftime("%Y-%m-%d") if estudiante.fecha_nacimiento else None,
        "info": info_data
    })



@api_estudiantes.route('/api/estudiante/cursos', methods=['GET'])
def get_estudiante_cursos():
    user_id = session.get('user_id')
    rol = session.get('rol')

    if not user_id or rol != 'estudiante':
        return jsonify({"error": "No autenticado"}), 401

    # 1. Obtener al estudiante y sus matrículas activas
    estudiante = Estudiante.query.get(user_id)
    if not estudiante:
        return jsonify({"error": "Estudiante no encontrado"}), 404

    # 2. Asumir un período académico actual (o obtenerlo de un parámetro o de la DB)
    # Por ahora, usamos un valor fijo para la consulta.
    PERIODO_ACTUAL = "2024-II" 

    # 3. Consulta Principal: Encontrar todos los cursos y sus programaciones de clase
    #    a través de las matrículas del estudiante en el período actual.

    # Esta consulta es compleja y requiere unir varias tablas. 
    # Usaremos una consulta de cursos directamente y filtraremos.
    
    # NOTA: Para obtener los cursos de un estudiante matriculado a través del MÓDULO:
    # 1. Matricula -> Modulo
    # 2. Modulo -> Cursos
    
    # Obtener los IDs de los módulos en los que el estudiante está matriculado y activo
    modulos_ids = [
        m.modulo_id for m in estudiante.matriculas 
        if m.estado == 'activa' and m.modulo.periodo_academico == PERIODO_ACTUAL
    ]

    if not modulos_ids:
         return jsonify([]), 200 # No hay cursos activos

    # Obtener todos los cursos asociados a esos módulos
    cursos_actuales = Curso.query.filter(Curso.modulo_id.in_(modulos_ids)).all()
    
    cursos_data = []

    for idx, curso in enumerate(cursos_actuales):
        # Encontrar todas las sesiones de clase para este curso en el período
        sesiones = ProgramacionClase.query.filter(
            ProgramacionClase.curso_id == curso.id,
            ProgramacionClase.periodo_academico == PERIODO_ACTUAL
        ).all()
        
        # Agrupar sesiones y docentes
        sessions_list = []
        teacher_name = "No Asignado"

        for session in sesiones:
            # Encuentra el docente de la sesión (si existe)
            docente = Docente.query.get(session.docente_id)
            if docente:
                teacher_name = docente.nombre_completo

            # Encuentra el salón (room)
            salon = Salon.query.get(session.salon_id)
            room_name = salon.nombre if salon else "Virtual/Por Definir"

            # Formato de la hora: HH:MM-HH:MM
            # Usamos strftime para formatear los objetos time de Python
            time_format = "%H:%M"
            time_str = f"{session.hora_inicio.strftime(time_format)}-{session.hora_fin.strftime(time_format)}"

            sessions_list.append({
                "day": session.dia_semana,
                "time": time_str,
                "room": room_name
            })
        
        # Si un curso tiene múltiples programaciones (como Contabilidad), 
        # el nombre del docente será el último asignado. Esto es una simplificación.
        
        cursos_data.append({
            "code": curso.id, # Usamos el ID como código de curso o buscar el campo código real
            "name": curso.nombre,
            "teacher": teacher_name,
            "sessions": sessions_list
        })

    return jsonify(cursos_data)

@api_estudiantes.route('/api/estudiante/calificaciones', methods=['GET'])
def get_estudiante_calificaciones():
    # 1. Autenticación y obtención del ID de estudiante
    user_id = session.get('user_id')
    rol = session.get('rol')
    
    # Podrías pasar el periodo como query parameter: ?periodo=2024-II
    periodo_solicitado = request.args.get('periodo', '2024-II') # Asume un valor por defecto

    if not user_id or rol != 'estudiante':
        return jsonify({"error": "No autenticado"}), 401

    estudiante = Estudiante.query.get(user_id)
    if not estudiante:
        return jsonify({"error": "Estudiante no encontrado"}), 404

    # 2. Obtener los cursos en los que el estudiante está matriculado en el período
    #    Necesitamos cursos que estén asociados a módulos en el periodo solicitado.
    
    # IDs de módulos activos del estudiante en el periodo
    modulos_ids_activos = db.session.query(Matricula.modulo_id).join(Modulo).filter(
        Matricula.estudiante_id == user_id,
        Matricula.estado == 'activa',
        Modulo.periodo_academico == periodo_solicitado
    ).subquery()
    
    # Cursos asociados a esos módulos
    cursos_matriculados = Curso.query.filter(
        Curso.modulo_id.in_(modulos_ids_activos)
    ).all()
    
    cursos_data = []

    for curso in cursos_matriculados:
        
        # 3. Obtener todas las calificaciones del estudiante para este curso
        calificaciones_curso = Calificacion.query.filter(
            Calificacion.estudiante_id == user_id,
            Calificacion.curso_id == curso.id
        ).order_by(Calificacion.fecha_registro).all() # Ordenar para consistencia
        
        notes_list = []
        
        for nota in calificaciones_curso:
            notes_list.append({
                # Mapeo a las etiquetas que usa tu React App
                "label": nota.tipo_evaluacion, # Ejemplo: 'PERMANENTE 1'
                "value": "{:.2f}".format(nota.valor) # Formatear a dos decimales
            })
            
        # 4. Cálculo del promedio final (Opcional, pero esencial para la vista)
        # Esto requiere una lógica de negocio específica (ej: pesos). Aquí se hace un promedio simple.
        if calificaciones_curso:
            promedio_simple = db.session.query(func.avg(Calificacion.valor)).filter(
                Calificacion.estudiante_id == user_id,
                Calificacion.curso_id == curso.id
            ).scalar()
            
            notes_list.append({
                "label": "Promedio Final",
                "value": "{:.2f}".format(promedio_simple)
            })

        cursos_data.append({
            # Nota: Asumo que el campo `codigo` en tu DB es un string, sino usa el id o añádelo
            "code": curso.id, # Asumo que usarás el ID como código temporal o cambiarás el modelo
            "name": curso.nombre,
            "notes": notes_list
        })

    return jsonify(cursos_data)
