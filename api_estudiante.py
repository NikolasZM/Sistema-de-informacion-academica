from flask import Blueprint, jsonify, session, request, abort, current_app, send_from_directory
# Importamos TODOS los modelos necesarios para las nuevas consultas
from models import *
from sqlalchemy import distinct, func, text, desc, case, and_
from sqlalchemy.orm import joinedload, aliased
from math import floor
import datetime
import os

api_estudiante = Blueprint('api_estudiante', __name__)

# --- Constante para Regla de Aprobación ---
NOTA_MINIMA_APROBATORIA = 12.5 

# ====================================================================
# 1. INFO BÁSICA Y ACTUALIZACIÓN
# ====================================================================

@api_estudiante.route('/api/estudiante/info', methods=['GET', 'POST'])
def handle_estudiante_info():
    """
    Obtiene (GET) o actualiza (POST) la información personal y de contacto
    del estudiante autenticado. Actualizado para el nuevo modelo de Matrícula.
    """
    user_id = session.get('user_id')
    rol = session.get('rol')

    if not user_id or rol != 'estudiante':
        return jsonify({"error": "No autenticado"}), 401

    estudiante = db.session.get(Estudiante, user_id)
    if not estudiante:
        return jsonify({"error": "Estudiante no encontrado"}), 404
        
    estudiante_info = db.session.query(EstudianteInfo).filter_by(estudiante_id=user_id).first()

    # --- MÉTODO POST: Actualizar datos ---
    if request.method == 'POST':
        data = request.json
        if not estudiante_info:
            estudiante_info = EstudianteInfo(estudiante_id=user_id)
            db.session.add(estudiante_info)

        try:
            # Actualizar campos de Domicilio y Contactos
            estudiante_info.direccion = data.get('direccion')
            estudiante_info.departamento = data.get('departamento')
            estudiante_info.provincia = data.get('provincia')
            estudiante_info.distrito = data.get('distrito')
            estudiante_info.celular = data.get('celular')
            
            # Contacto 1
            estudiante_info.contacto_nombre = data.get('c1_nombre')
            estudiante_info.contacto_parentesco = data.get('c1_parentesco')
            estudiante_info.contacto_telefono = data.get('c1_celular')
            
            # Contacto 2
            estudiante_info.contacto_nombre_2 = data.get('c2_nombre')
            estudiante_info.contacto_parentesco_2 = data.get('c2_parentesco')
            estudiante_info.contacto_telefono_2 = data.get('c2_celular')

            db.session.commit()
            return jsonify({"message": "Información de contacto actualizada exitosamente"}), 200
            
        except Exception as e:
            db.session.rollback()
            print(f"Error en POST /info: {e}")
            return jsonify({"error": f"Error al guardar los datos: {str(e)}"}), 500

    # --- MÉTODO GET: Obtener datos ---
    
    # 1. Obtener Programa de Estudio (Lógica actualizada)
    programa_string = estudiante.programa_estudio # Usar el campo estático como fallback
    
    # Buscar la matrícula más reciente basada en la fecha de inicio de la oferta
    matricula_reciente = db.session.query(Matricula).join(
        ModuloActivo, Matricula.modulo_activo_id == ModuloActivo.id
    ).filter(
        Matricula.estudiante_id == user_id
    ).order_by(
        desc(ModuloActivo.fecha_inicio) # Ordenar por la fecha de inicio de la oferta
    ).options(
        joinedload(Matricula.modulo_activo).joinedload(ModuloActivo.programa) # Carga ansiosa
    ).first()
    
    if matricula_reciente and matricula_reciente.modulo_activo and matricula_reciente.modulo_activo.programa:
        programa_string = matricula_reciente.modulo_activo.programa.nombre
    
    # 2. Construir el objeto JSON de respuesta
    # (Asegúrate de que los campos coincidan con tu modelo Estudiante)
    data = {
        "id": estudiante.id,
        "dni": estudiante.dni,
        "apellidos": estudiante.apellidos,
        "nombre_completo": estudiante.nombre_completo,
        "sexo": estudiante.sexo,
        "fecha_nacimiento": estudiante.fecha_nacimiento.strftime("%Y-%m-%d") if estudiante.fecha_nacimiento else None,
        "correo": estudiante.correo,
        "pais_nacimiento": estudiante.pais_nacimiento,
        "departamento_nacimiento": estudiante.departamento_nacimiento,
        "provincia_nacimiento": estudiante.provincia_nacimiento,
        "distrito_nacimiento": estudiante.distrito_nacimiento,
        "programa_estudio": programa_string, # El programa dinámico
        "esta_trabajando": estudiante.esta_trabajando,
        "centro_trabajo": estudiante.centro_trabajo,
        "puesto_trabajo": estudiante.puesto_trabajo,
        "nivel_educacion": estudiante.nivel_educacion,
        "nombre_colegio": estudiante.nombre_colegio,
        "estado_civil": estudiante.estado_civil,
        "numero_hijos": estudiante.numero_hijos,
        "celular": estudiante_info.celular if estudiante_info and estudiante_info.celular else estudiante.celular,
        "domicilio": estudiante_info.direccion if estudiante_info and estudiante_info.direccion else estudiante.domicilio,
        "celular_familiar_contacto": estudiante.celular_familiar_contacto,
        "link_foto_dni": estudiante.link_foto_dni,
        "medio_conocimiento": estudiante.medio_conocimiento,
        
        # --- Datos de EstudianteInfo (Editables via POST) ---
        "direccion": estudiante_info.direccion if estudiante_info else "",
        "departamento": estudiante_info.departamento if estudiante_info else "",
        "provincia": estudiante_info.provincia if estudiante_info else "",
        "distrito": estudiante_info.distrito if estudiante_info else "",
        
        "c1_nombre": estudiante_info.contacto_nombre if estudiante_info else "",
        "c1_parentesco": estudiante_info.contacto_parentesco if estudiante_info else "",
        "c1_celular": estudiante_info.contacto_telefono if estudiante_info else "",
        
        "c2_nombre": estudiante_info.contacto_nombre_2 if estudiante_info else "",
        "c2_parentesco": estudiante_info.contacto_parentesco_2 if estudiante_info else "",
        "c2_celular": estudiante_info.contacto_telefono_2 if estudiante_info else "",
    }
    return jsonify(data), 200

# ====================================================================
# 2. CURSOS, ASISTENCIA Y HORARIO (AHORA VINCULADOS A MODULOACTIVO)
# ====================================================================

@api_estudiante.route('/api/estudiante/cursos_actuales', methods=['GET'])
def get_cursos_actuales():
    """Obtiene los cursos activos y su horario para el estudiante."""
    estudiante_id = session.get('user_id')
    if not estudiante_id:
        return jsonify({"error": "No autenticado"}), 401

    try:
        # 1. Obtener todos los Cursos Activos donde el estudiante tiene una matrícula de módulo activa
        cursos_inscritos = db.session.query(MatriculaCurso).join(
            Matricula, MatriculaCurso.matricula_id == Matricula.id
        ).filter(
            Matricula.estudiante_id == estudiante_id,
            Matricula.estado == 'activa' # La matrícula (cabecera) está activa
        ).options(
            joinedload(MatriculaCurso.curso_activo).joinedload(CursoActivo.curso), # Catálogo de Curso
            joinedload(MatriculaCurso.curso_activo).joinedload(CursoActivo.modulo_activo).joinedload(ModuloActivo.periodo), # Periodo
            joinedload(MatriculaCurso.curso_activo).joinedload(CursoActivo.programaciones).joinedload(ProgramacionClase.salon), # Horario
            joinedload(MatriculaCurso.curso_activo).joinedload(CursoActivo.docente) # Docente
        ).all()

        if not cursos_inscritos:
            return jsonify({"periodo_codigo": None, "cursos": []}), 200
        
        resultado = []
        periodo_codigo_actual = "Varios Períodos"
        if cursos_inscritos:
             # Toma el código del período de la primera matrícula como referencia
            periodo_codigo_actual = cursos_inscritos[0].curso_activo.modulo_activo.periodo.codigo

        for mc in cursos_inscritos:
            ca = mc.curso_activo # CursoActivo
            curso = ca.curso # Curso (catálogo)
            
            prog_list = []
            for p in ca.programaciones:
                prog_list.append({
                    "dia_semana": p.dia_semana,
                    "hora_inicio": p.hora_inicio.strftime('%H:%M'),
                    "hora_fin": p.hora_fin.strftime('%H:%M'),
                    "salon": p.salon.nombre if p.salon else "Sin aula",
                    "docente": p.docente.nombre_completo if p.docente else "Sin asignar",
                })
            
            resultado.append({
                "id": curso.id, # ID del curso catálogo
                "curso_activo_id": ca.id, # ID de la instancia
                "nombre": curso.nombre,
                "modulo_id": ca.modulo_activo.modulo_id,
                "modulo_nombre": ca.modulo_activo.modulo.nombre,
                "programaciones": prog_list
            })

        return jsonify({"periodo_codigo": periodo_codigo_actual, "cursos": resultado}), 200
    
    except Exception as e:
        print(f"Error en /cursos_actuales: {e}")
        db.session.rollback()
        return jsonify({"error": f"Error interno: {e}"}), 500


@api_estudiante.route('/api/estudiante/periodos', methods=['GET'])
def get_estudiante_periodos():
    """
    Obtiene la lista de períodos en los que el estudiante ha estado matriculado.
    (Ahora filtra por ModuloActivo y Periodo).
    """
    estudiante_id = session.get('user_id')
    if not estudiante_id:
        return jsonify({"error": "No autorizado"}), 401

    try:
        # Consulta los Periodos a través de ModuloActivo que tienen una Matrícula (cabecera) asociada
        periodos = db.session.query(
            Periodo.id.label('periodo_id'),
            Periodo.codigo
        ).select_from(Periodo).join(
            ModuloActivo, Periodo.id == ModuloActivo.periodo_id
        ).join(
            Matricula, ModuloActivo.id == Matricula.modulo_activo_id
        ).filter(
            Matricula.estudiante_id == estudiante_id
        ).distinct().order_by(desc(Periodo.codigo)).all()
        
        return jsonify([p._asdict() for p in periodos])

    except Exception as e:
        print(f"Error al obtener períodos: {e}")
        db.session.rollback()
        return jsonify({"error": "Error interno al consultar períodos"}), 500


@api_estudiante.route('/api/estudiante/periodo/<int:periodo_id>/calificaciones', methods=['GET'])
def get_periodo_calificaciones(periodo_id):
    """Obtiene el resumen y detalle de calificaciones para un período dado."""
    estudiante_id = session.get('user_id')
    if not estudiante_id:
        return jsonify({"error": "No autorizado"}), 401

    try:
        # 1. Obtener TODOS los registros de MatriculaCurso para este estudiante en este periodo
        # La forma más limpia es ir: MatriculaCurso -> Matricula -> ModuloActivo -> Periodo
        matricula_cursos = db.session.query(MatriculaCurso).join(
            Matricula, MatriculaCurso.matricula_id == Matricula.id
        ).join(
            CursoActivo, MatriculaCurso.curso_activo_id == CursoActivo.id
        ).join(
            ModuloActivo, CursoActivo.modulo_activo_id == ModuloActivo.id
        ).filter(
            Matricula.estudiante_id == estudiante_id,
            ModuloActivo.periodo_id == periodo_id
        ).options(
            joinedload(MatriculaCurso.calificaciones), # Carga las notas
            joinedload(MatriculaCurso.curso_activo).joinedload(CursoActivo.curso) # Carga el nombre del curso
        ).all()
        
        if not matricula_cursos:
            return jsonify({"error": "No se encontraron cursos matriculados para este período."}), 404

        # 2. Procesar y calcular estados
        resultados_cursos = []
        notas_finales_validas = []
        conteo_aprobados = 0
        conteo_desaprobados = 0
        conteo_pendientes = 0

        for mc in matricula_cursos:
            # Buscar PROMEDIO_FINAL en la lista ya cargada (Calificacion)
            promedio_final_obj = next((c for c in mc.calificaciones if c.tipo_evaluacion == 'PROMEDIO_FINAL'), None)
            
            promedio_valor = None
            estado = "Pendiente"
            
            if promedio_final_obj:
                promedio_valor = promedio_final_obj.valor
                notas_finales_validas.append(promedio_valor)
                if promedio_valor >= NOTA_MINIMA_APROBATORIA:
                    estado = "Aprobado"
                    conteo_aprobados += 1
                else:
                    estado = "Desaprobado"
                    conteo_desaprobados += 1
            else:
                conteo_pendientes += 1
            
            # 3. Formatear la salida
            resultados_cursos.append({
                "curso_id": mc.curso_activo.curso.id, # ID del catálogo
                "codigo": f"C-{mc.curso_activo.curso.id:03d}",
                "nombre": mc.curso_activo.curso.nombre,
                "promedio_final": promedio_valor, 
                "estado": estado, 
                "notas_detalle": [
                    {
                        "id": n.id,
                        "tipo": n.tipo_evaluacion,
                        "valor": n.valor,
                        "fecha": n.fecha_registro.isoformat()
                    } for n in mc.calificaciones
                ]
            })

        # 4. Calcular el resumen final
        promedio_simple = 0
        if notas_finales_validas:
            promedio_simple = round(sum(notas_finales_validas) / len(notas_finales_validas), 2)

        resumen = {
            "total_cursos": len(matricula_cursos),
            "aprobados": conteo_aprobados,
            "desaprobados": conteo_desaprobados,
            "pendientes": conteo_pendientes,
            "promedio_simple": promedio_simple if promedio_simple > 0 else None
        }
        
        return jsonify({"resumen": resumen, "cursos": resultados_cursos}), 200

    except Exception as e:
        print(f"Error al obtener calificaciones: {e}")
        db.session.rollback()
        return jsonify({"error": "Error interno al procesar calificaciones"}), 500


@api_estudiante.route('/api/estudiante/periodo/<int:periodo_id>/asistencias', methods=['GET'])
def get_periodo_asistencias(periodo_id):
    """Obtiene el resumen y detalle de asistencias para un período dado."""
    estudiante_id = session.get('user_id')
    if not estudiante_id:
        return jsonify({"error": "No autorizado"}), 401

    try:
        # 1. Obtener los MatriculaCurso (igual que en calificaciones)
        matricula_cursos = db.session.query(MatriculaCurso).join(
            Matricula, MatriculaCurso.matricula_id == Matricula.id
        ).join(
            CursoActivo, MatriculaCurso.curso_activo_id == CursoActivo.id
        ).join(
            ModuloActivo, CursoActivo.modulo_activo_id == ModuloActivo.id
        ).filter(
            Matricula.estudiante_id == estudiante_id,
            ModuloActivo.periodo_id == periodo_id
        ).options(
            joinedload(MatriculaCurso.asistencias),
            joinedload(MatriculaCurso.curso_activo).joinedload(CursoActivo.curso)
        ).all()

        if not matricula_cursos:
            return jsonify({"error": "No se encontraron cursos matriculados para este período."}), 404

        RETIRO_PERCENT = 30
        resultado_cursos = []

        for mc in matricula_cursos:
            # 2. Obtener sesiones programadas del catálogo
            total_sesiones = mc.curso_activo.curso.sesiones_programadas if mc.curso_activo.curso.sesiones_programadas else 0
            
            # 3. Contar faltas (cargadas desde la relación)
            faltas_reales = 0
            asistencias_detalle_json = []
            for a in mc.asistencias:
                if a.estado == 'falta' and not a.justificada:
                    faltas_reales += 1
                asistencias_detalle_json.append({
                    "fecha": a.fecha.isoformat(),
                    "estado": a.estado,
                    "justificada": a.justificada,
                    "observacion": a.observacion
                })

            # 4. Calcular porcentajes
            max_faltas_permitidas = floor(total_sesiones * (RETIRO_PERCENT / 100))
            porcentaje_inasistencia = 0
            if total_sesiones > 0:
                porcentaje_inasistencia = round((faltas_reales / total_sesiones) * 100, 1)
            retirado = porcentaje_inasistencia > RETIRO_PERCENT

            # 5. Formatear
            resultado_cursos.append({
                "curso_id": mc.curso_activo.curso.id,
                "codigo": f"C-{mc.curso_activo.curso.id:03d}",
                "nombre": mc.curso_activo.curso.nombre,
                "sesiones_totales": total_sesiones,
                "faltas_contadas": faltas_reales,
                "max_faltas_permitidas": max_faltas_permitidas,
                "porcentaje_inasistencia": porcentaje_inasistencia,
                "retirado": retirado,
                "asistencias_detalle": asistencias_detalle_json
            })

        return jsonify({"cursos": resultado_cursos})

    except Exception as e:
        print(f"Error al obtener asistencias: {e}")
        db.session.rollback()
        return jsonify({"error": "Error interno al procesar asistencias"}), 500
        

# ====================================================================
# 3. AVANCE CURRICULAR Y TRÁMITES
# ====================================================================

def _verificar_modulo_aprobado(estudiante_id, modulo_id):
    """
    Verifica si un estudiante ha aprobado TODOS los cursos de un módulo de catálogo,
    buscando la mejor nota en el historial de matrículas (MatriculaCurso).
    """
    try:
        # 1. Encontrar todos los IDs de cursos del catálogo que componen el módulo
        cursos_del_modulo_ids = db.session.query(Curso.id).filter(
            Curso.modulo_id == modulo_id
        ).all()
        cursos_del_modulo_ids = {c[0] for c in cursos_del_modulo_ids}

        if not cursos_del_modulo_ids:
            return False # Un módulo sin cursos no se puede "aprobar"

        # 2. Encontrar todos los cursos que el estudiante ha aprobado (con nota >= 12.5)
        #    que pertenecen a este módulo.
        cursos_aprobados_ids = db.session.query(
            CursoActivo.curso_id # Obtenemos el ID del curso catálogo
        ).select_from(Calificacion).join(
            MatriculaCurso, Calificacion.matricula_curso_id == MatriculaCurso.id
        ).join(
            Matricula, MatriculaCurso.matricula_id == Matricula.id
        ).join(
            CursoActivo, MatriculaCurso.curso_activo_id == CursoActivo.id
        ).filter(
            Matricula.estudiante_id == estudiante_id,
            CursoActivo.curso_id.in_(cursos_del_modulo_ids),
            Calificacion.tipo_evaluacion == 'PROMEDIO_FINAL',
            Calificacion.valor >= NOTA_MINIMA_APROBATORIA
        ).distinct().all()
        
        cursos_aprobados_set = {c[0] for c in cursos_aprobados_ids}

        # 3. Comparar: El set de cursos aprobados debe ser igual al set de cursos del módulo
        return cursos_aprobados_set == cursos_del_modulo_ids

    except Exception as e:
        print(f"Error verificando aprobación de módulo: {e}")
        return False


# Función para api_estudiante.py

@api_estudiante.route('/api/estudiante/avance_curricular', methods=['GET'])
def get_avance_curricular():
    """
    Endpoint que construye la vista de Avance Curricular del estudiante,
    basado en el modelo de Matrícula Detallada (MatriculaCurso).
    """
    estudiante_id = session.get('user_id')
    if not estudiante_id:
        return jsonify({"error": "No autorizado"}), 401

    NOTA_MINIMA_APROBATORIA = 12.5 

    try:
        # 1. Obtener el programa del estudiante (Ruta Explícita)
        programa_est = db.session.query(Programa).select_from(Estudiante).join(
            Matricula, Estudiante.id == Matricula.estudiante_id
        ).join(
            ModuloActivo, Matricula.modulo_activo_id == ModuloActivo.id
        ).join(
            Programa, ModuloActivo.programa_id == Programa.id
        ).filter(
            Estudiante.id == estudiante_id
        ).distinct().first()

        if not programa_est:
             return jsonify({"error": "Estudiante no tiene un programa de estudio válido."}), 404
        
        # 2. Cargar todos los módulos del catálogo del programa
        todos_modulos = db.session.query(Modulo).filter_by(
            programa_id=programa_est.id
        ).options(
            joinedload(Modulo.cursos), 
            joinedload(Modulo.ofertas).joinedload(ModuloActivo.cursos_activos) 
        ).order_by(Modulo.num_modulo.asc()).all() # ✅ Ordenado por num_modulo

        # 3. Mapeo de la MEJOR Nota Final Aprobada (Historial)
        best_notes_query = db.session.query(
            Curso.id.label('curso_id'),
            func.max(Calificacion.valor).label('mejor_nota')
        ).select_from(Calificacion).join(
            MatriculaCurso, Calificacion.matricula_curso_id == MatriculaCurso.id
        ).join(
            Matricula, MatriculaCurso.matricula_id == Matricula.id
        ).join(
            CursoActivo, MatriculaCurso.curso_activo_id == CursoActivo.id
        ).join(
            Curso, CursoActivo.curso_id == Curso.id
        ).filter(
            Matricula.estudiante_id == estudiante_id,
            Calificacion.tipo_evaluacion == 'PROMEDIO_FINAL'
        ).group_by(Curso.id).subquery()
        
        best_notes_results = db.session.execute(db.select(best_notes_query)).all()
        notas_map = {n.curso_id: n.mejor_nota for n in best_notes_results}
        
        # 4. Mapeo de Matrículas Activas (para estado "En Curso")
        cursos_en_progreso_query = db.session.query(CursoActivo.curso_id).join(
            MatriculaCurso, CursoActivo.id == MatriculaCurso.curso_activo_id
        ).join(
            Matricula, MatriculaCurso.matricula_id == Matricula.id
        ).filter(
            Matricula.estudiante_id == estudiante_id,
            Matricula.estado == 'activa'
        ).distinct().all()
        cursos_en_progreso_set = {c[0] for c in cursos_en_progreso_query}
        
        # 5. Mapeo de Trámites
        tramites = db.session.query(SolicitudTramite).filter_by(estudiante_id=estudiante_id).all()
        tramites_map = {t.modulo_id: t.estado for t in tramites}

        # --- 6. Procesar y construir el JSON de respuesta ---
        json_modulos = []
        
        for modulo in todos_modulos:
            json_cursos = []
            cursos_aprobados_count = 0
            algun_curso_desaprobado = False
            algun_curso_en_progreso = False
            
            total_cursos_modulo = len(modulo.cursos)
            if total_cursos_modulo == 0:
                continue

            for curso in modulo.cursos:
                curso_estado = "Pendiente"
                nota_final = notas_map.get(curso.id)

                if nota_final is not None:
                    # ✅ Usa 12.5 para aprobación
                    if nota_final >= NOTA_MINIMA_APROBATORIA: 
                        curso_estado = "Aprobado"
                        cursos_aprobados_count += 1
                    else:
                        curso_estado = "Desaprobado"
                        algun_curso_desaprobado = True
                
                elif curso.id in cursos_en_progreso_set:
                    curso_estado = "En Curso"
                    algun_curso_en_progreso = True
                
                json_cursos.append({
                    "curso_id": curso.id,
                    "nombre": curso.nombre,
                    "estado": curso_estado,
                    "nota_final": nota_final,
                })
            
            # --- Determinar el estado general del Módulo (Lógica de Prioridad) ---
            estado_modulo = "Pendiente"
            
            if algun_curso_desaprobado:
                estado_modulo = "Desaprobado" 
            elif cursos_aprobados_count == total_cursos_modulo:
                estado_modulo = "Aprobado" 
            elif algun_curso_en_progreso:
                estado_modulo = "En Curso" 
            
            estado_tramite = tramites_map.get(modulo.id)
            puede_solicitar = (estado_modulo == "Aprobado") and (estado_tramite is None)
            
            json_modulos.append({
                "modulo_id": modulo.id,
                "num_modulo": modulo.num_modulo, # ✅ Dato añadido
                "nombre": modulo.nombre,
                "estado_modulo": estado_modulo,
                "estado_tramite": estado_tramite,
                "puede_solicitar_tramite": puede_solicitar,
                "cursos": json_cursos
            })

        respuesta_final = {
            "programa_nombre": programa_est.nombre,
            "modulos": json_modulos
        }
        
        return jsonify(respuesta_final), 200

    except Exception as e:
        print(f"Error en /avance_curricular: {e}")
        db.session.rollback()
        return jsonify({"error": f"Error interno al procesar el avance: {e}"}), 500

@api_estudiante.route('/api/estudiante/tramites/disponibles', methods=['GET'])
def get_tramites_disponibles():
    """
    Devuelve una lista de módulos (catálogo) que el estudiante ha aprobado
    y para los cuales NO ha solicitado aún un trámite.
    """
    estudiante_id = session.get('user_id')
    if not estudiante_id:
        return jsonify({"error": "No autorizado"}), 401

    try:
        # 1. Obtener todos los módulos (catálogo) donde el estudiante estuvo matriculado
        modulos_matriculados = db.session.query(Modulo).join(
            ModuloActivo, Modulo.id == ModuloActivo.modulo_id
        ).join(
            Matricula, ModuloActivo.id == Matricula.modulo_activo_id
        ).filter(
            Matricula.estudiante_id == estudiante_id
        ).distinct().all()

        # 2. Obtener trámites que ya existen (apuntando al módulo de catálogo)
        modulos_ya_solicitados_ids = {
            t[0] for t in db.session.query(SolicitudTramite.modulo_id).filter(
                SolicitudTramite.estudiante_id == estudiante_id,
                SolicitudTramite.modulo_id.isnot(None)
            ).all()
        }

        modulos_disponibles = []
        for modulo in modulos_matriculados:
            if modulo.id in modulos_ya_solicitados_ids:
                continue 
            
            # 4. Verificar si está aprobado (usando la función helper actualizada)
            if _verificar_modulo_aprobado(estudiante_id, modulo.id):
                modulos_disponibles.append({
                    "modulo_id": modulo.id,
                    "nombre": modulo.nombre
                })
        
        return jsonify(modulos_disponibles)

    except Exception as e:
        print(f"Error en /tramites/disponibles: {e}")
        db.session.rollback()
        return jsonify({"error": "Error interno del servidor"}), 500


@api_estudiante.route('/api/estudiante/tramites/historial', methods=['GET'])
def get_tramites_historial():
    """
    Devuelve todas las solicitudes de trámite (pendientes y completas)
    del estudiante logueado.
    """
    estudiante_id = session.get('user_id')
    if not estudiante_id:
        return jsonify({"error": "No autorizado"}), 401

    try:
        solicitudes = db.session.query(
            SolicitudTramite,
            Modulo.nombre.label('modulo_nombre')
        ).join(
            Modulo, SolicitudTramite.modulo_id == Modulo.id, isouter=True # Left Join por si modulo_id es null
        ).filter(
            SolicitudTramite.estudiante_id == estudiante_id
        ).order_by(
            desc(SolicitudTramite.fecha_solicitud)
        ).all()

        resultado_historial = []
        for solicitud, modulo_nombre in solicitudes:
            resultado_historial.append({
                "tramite_id": solicitud.id,
                "modulo_id": solicitud.modulo_id,
                "modulo_nombre": modulo_nombre if modulo_nombre else "Trámite General",
                "tipo_tramite": solicitud.tipo_tramite,
                "fecha_solicitud": solicitud.fecha_solicitud.isoformat(),
                "estado": solicitud.estado,
                "observaciones_admin": solicitud.observaciones_admin,
                "ruta_archivo": solicitud.ruta_archivo
            })
        
        return jsonify(resultado_historial)

    except Exception as e:
        print(f"Error en /tramites/historial: {e}")
        db.session.rollback()
        return jsonify({"error": "Error interno del servidor"}), 500


@api_estudiante.route('/api/estudiante/tramites/solicitar', methods=['POST'])
def post_solicitar_tramite():
    """
    Crea una nueva solicitud de trámite.
    Recibe: { "modulo_id": 123 }
    """
    estudiante_id = session.get('user_id')
    if not estudiante_id:
        return jsonify({"error": "No autorizado"}), 401

    data = request.json
    modulo_id = data.get('modulo_id')

    if not modulo_id:
        return jsonify({"error": "Falta el ID del módulo"}), 400

    # 1. Re-verificar que el módulo esté aprobado (con la nueva lógica)
    if not _verificar_modulo_aprobado(estudiante_id, modulo_id):
        return jsonify({"error": "Acción no permitida. El módulo (catálogo) no está aprobado."}), 403
    
    # 2. Verificar duplicados
    existe = db.session.query(SolicitudTramite).filter_by(
        estudiante_id=estudiante_id,
        modulo_id=modulo_id
    ).first()

    if existe:
        return jsonify({"error": "Ya existe una solicitud para este módulo."}), 409

    try:
        nueva_solicitud = SolicitudTramite(
            estudiante_id=estudiante_id,
            modulo_id=modulo_id,
            tipo_tramite="Certificado de Módulo",
            estado="Solicitado",
            fecha_solicitud = datetime.datetime.now(datetime.timezone.utc)
        )
        db.session.add(nueva_solicitud)
        db.session.commit()

        return jsonify({"mensaje": "Solicitud enviada correctamente"}), 201

    except Exception as e:
        db.session.rollback()
        print(f"Error en /tramites/solicitar: {e}")
        return jsonify({"error": "Error interno al guardar la solicitud"}), 500


@api_estudiante.route('/api/estudiante/descargar_tramite/<int:tramite_id>')
def descargar_tramite(tramite_id):
    """
    Descarga segura del archivo de trámite (certificado).
    """
    estudiante_id = session.get('user_id')
    if not estudiante_id:
        return jsonify({"error": "No autorizado"}), 401

    tramite = db.session.get(SolicitudTramite, tramite_id)
    if not tramite:
        return jsonify({"error": "Trámite no encontrado"}), 404

    if tramite.estudiante_id != estudiante_id:
        return jsonify({"error": "Acceso denegado"}), 403

    if not tramite.ruta_archivo or tramite.estado != 'Aprobado':
        return jsonify({"error": "Archivo no disponible o trámite no aprobado"}), 404

    try:
        # Asumimos que la carpeta está configurada en app.config
        cert_dir = current_app.config.get('CERTIFICADOS_DIR', os.path.join(current_app.root_path, 'uploads', 'certificados'))
        
        return send_from_directory(
            cert_dir,
            tramite.ruta_archivo,
            as_attachment=True
        )
    except FileNotFoundError:
        print(f"Error: Archivo no encontrado en disco: {tramite.ruta_archivo}")
        return jsonify({"error": "Archivo no encontrado en el servidor."}), 404

# API INICIO
# En api_estudiante.py (Nueva Ruta)
@api_estudiante.route('/api/estudiante/dashboard_full', methods=['GET'])
def get_dashboard_full_data():
    estudiante_id = session.get('user_id')
    if not estudiante_id:
        return jsonify({"error": "No autenticado"}), 401

    try:
        # --- 1. Obtener Matrícula y Contexto (Cabecera) ---
        # Buscamos la matrícula MÁS RECIENTE (Cabecera) para obtener el contexto de Fechas y Programa.
        matricula_cabecera = db.session.query(Matricula).filter(
            Matricula.estudiante_id == estudiante_id
        ).options(
            joinedload(Matricula.modulo_activo).joinedload(ModuloActivo.periodo),
            joinedload(Matricula.modulo_activo).joinedload(ModuloActivo.programa),
            joinedload(Matricula.cursos_inscritos).joinedload(MatriculaCurso.curso_activo).joinedload(CursoActivo.curso),
            joinedload(Matricula.cursos_inscritos).joinedload(MatriculaCurso.curso_activo).joinedload(CursoActivo.programaciones).joinedload(ProgramacionClase.salon),
            joinedload(Matricula.cursos_inscritos).joinedload(MatriculaCurso.curso_activo).joinedload(CursoActivo.docente)
        ).order_by(desc(Matricula.fecha_matricula)).first()

        if not matricula_cabecera:
            return jsonify({"error": "No hay matrículas registradas para el estudiante."}), 404

        mod_activo = matricula_cabecera.modulo_activo
        
        # --- 2. CÁLCULOS TRANSACCIONALES (ASISTENCIA Y PROGRESO) ---
        
        total_sesiones_programadas = 0
        total_faltas_no_justificadas = 0
        total_cursos_inscritos = len(matricula_cabecera.cursos_inscritos)
        
        programaciones_activas = []
        
        for mc in matricula_cabecera.cursos_inscritos:
            curso_catalogo = mc.curso_activo.curso
            
            # CÁLCULO DE ASISTENCIA (por MatriculaCurso)
            sesiones_curso = curso_catalogo.sesiones_programadas or 0
            total_sesiones_programadas += sesiones_curso
            
            # Contamos faltas no justificadas (asumiendo que las asistencias están cargadas ansiosamente)
            faltas_reales = sum(1 for a in mc.asistencias if a.estado == 'falta' and not a.justificada)
            total_faltas_no_justificadas += faltas_reales
            
            # CONSOLIDACIÓN DEL HORARIO
            for prog in mc.curso_activo.programaciones:
                programaciones_activas.append({
                    "dia_semana": prog.dia_semana,
                    "hora_inicio": prog.hora_inicio.strftime('%H:%M'),
                    "hora_fin": prog.hora_fin.strftime('%H:%M'),
                    "curso_nombre": curso_catalogo.nombre,
                    "salon": prog.salon.nombre if prog.salon else "Sin aula",
                    "docente": prog.docente.nombre_completo if prog.docente else "Sin asignar",
                })
        
        # --- 3. Obtener Módulos Aprobados (Requiere lógica compleja) ---
        # Este dato es difícil de obtener con una sola consulta sin subqueries complejos.
        # Por simplicidad del dashboard, se obtiene un conteo simple de los módulos de catálogo del programa.
        
        # 4. Cálculo de Totales Finales
        porcentaje_inasistencia = round((total_faltas_no_justificadas / total_sesiones_programadas) * 100, 1) if total_sesiones_programadas > 0 else 0

        # 5. Formatear Respuesta
        response_data = {
            "programa_nombre": mod_activo.programa.nombre,
            "periodo_codigo": mod_activo.periodo.codigo,
            "fecha_matricula": matricula_cabecera.fecha_matricula.isoformat(),
            "cursos_activos_total": total_cursos_inscritos,
            "porcentaje_inasistencia": porcentaje_inasistencia,
            "faltas_no_justificadas": total_faltas_no_justificadas,
            "total_sesiones": total_sesiones_programadas,
            "horario_activo": programaciones_activas,
            
            # Datos Simples
            "modulos_aprobados_conteo": 0, # Se calcularía con la lógica de Avance Curricular
            "links_utiles": [
                {"nombre": "Reglamento", "url": "/docs/reglamento.pdf"},
                {"nombre": "Guía de Trámites", "url": "/tramites/guia"}
            ]
        }
        
        return jsonify(response_data), 200

    except Exception as e:
        print(f"Error al obtener datos del dashboard: {e}")
        db.session.rollback()
        return jsonify({"error": "Error interno al procesar el Dashboard"}), 500
