from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app, send_from_directory, make_response, jsonify, send_file
from flask_dance.contrib.google import make_google_blueprint, google
from werkzeug.security import generate_password_hash, check_password_hash
from models import *
from datetime import datetime, date
import os
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

try:
    from weasyprint import HTML
except Exception:
    HTML = None

routes = Blueprint('routes', __name__)

def calcular_edad(fecha_nac):
    if not fecha_nac:
        return None
    today = date.today()
    return today.year - fecha_nac.year - ((today.month, today.day) < (fecha_nac.month, fecha_nac.day))


@routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']
        user = Usuario.query.filter_by(usuario=usuario).first()
        if user and user.password and check_password_hash(user.password, password):
            print("Usuario autenticado:", user.usuario)
            session['usuario'] = user.email
            session['rol'] = user.rol
            session['user_id'] = user.id  # <-- agrega esto si lo necesitas en otras rutas
            if user.rol == 'docente':
                docente = Docente.query.filter_by(id=user.id).first()
                session['nombre_docente'] = docente.nombre_completo if docente and docente.nombre_completo else user.usuario
            flash('Inicio de sesión exitoso', 'success')
            if user.rol == 'docente':
                return redirect(url_for('routes.inicio_docente'))
            elif user.rol == 'estudiante':
                usuario = session.get('usuario')
                print("Sesión iniciada para estudiante:", usuario)
                print("user_id en sesión:", session.get('user_id'))
                print(f"Usuario estudiante en sesión: {usuario}")
                print("Redirigiendo a la app de React en producción...")
                return redirect(url_for('routes.serve_react_app'))
                #  redirige al frontend React (en desarrollo) CAMBIO AQUI
                #return redirect("http://localhost:5173/")
            else:
                return redirect(url_for('routes.inicio_admin'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    return render_template('login.html')


# Esta es la ruta "catch-all". Maneja:
# 1. La entrada principal ('/app_estudiante')
# 2. Las rutas de React Router ('/app_estudiante/cursos', '/app_estudiante/perfil')
# 3. Los archivos estáticos que React solicita ('/app_estudiante/assets/index.js')
# ...existing code...
@routes.route('/app_estudiante')
@routes.route('/app_estudiante/<path:path>')
def serve_react_app(path=None):
    import os
    # ruta esperada al build de React
    dist_dir = os.path.join(current_app.root_path, 'react-client', 'dist')
    dist_dir_abs = os.path.abspath(dist_dir)
    print("Buscando en dist_dir:", dist_dir_abs, " requested path:", path)

    if path:
        candidate = os.path.abspath(os.path.join(dist_dir_abs, path))
        # asegurar que está dentro de dist y que es un archivo regular
        if os.path.commonpath([dist_dir_abs, candidate]) == dist_dir_abs and os.path.isfile(candidate):
            return send_from_directory(dist_dir, path)
        else:
            print("Archivo no encontrado o fuera de dist:", candidate)

    # fallback: servir index si existe, sino devolver 404 para detectar problema
    index_file = os.path.join(dist_dir_abs, 'index.html')
    if os.path.isfile(index_file):
        return send_from_directory(dist_dir, 'index.html')
    else:
        print("index.html no encontrado en:", index_file)
        return ("Frontend build no encontrado. Ejecuta 'npm run build' y coloca el resultado en react-client/dist", 404)
# ...existing code...
# ---------------------------------------------

@routes.route('/pagina_principal')
def pagina_principal():
    if 'usuario' in session:
        return f"Bienvenido {session['usuario']} ({session['rol']})"
    return redirect(url_for('login'))


@routes.route('/login_google')
def login_google():
    # Redirige a Google para la autenticación
    return redirect(url_for('google.login'))

@routes.route('/google_login/callback')
def google_login_callback():
    from flask import flash, redirect, session, current_app
    from flask_dance.contrib.google import google
    from models import Usuario, Docente, Estudiante
    try:
        from models import db
    except Exception:
        try:
            from app import db
        except Exception:
            db = None

    current_app.logger.info("google_login_callback inicio")
    resp = google.get("/oauth2/v3/userinfo")
    if not resp or not resp.ok:
        flash("Error obteniendo información de Google.", "danger")
        return redirect('/login')

    info = resp.json()
    email = (info.get('email') or '').lower()
    hd = (info.get('hd') or '').lower()
    allowed = 'cedhinuevaarequipa.edu.pe'
    if not email or not (hd == allowed or email.endswith(f"@{allowed}")):
        flash("Acceso restringido al dominio cedhinuevaarequipa.edu.pe", "warning")
        return redirect('/login')

    # buscar o crear Usuario
    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario:
        if db is None:
            flash("Error interno.", "danger")
            return redirect('/login')
        import secrets
        from werkzeug.security import generate_password_hash
        nuevo = Usuario()
        base = email.split('@')[0]
        candidate = base
        i = 1
        while Usuario.query.filter_by(usuario=candidate).first():
            candidate = f"{base}{i}"; i += 1
        nuevo.usuario = candidate
        nuevo.password = generate_password_hash(secrets.token_urlsafe(16))
        if hasattr(nuevo, 'email'): nuevo.email = email
        if hasattr(nuevo, 'rol'): nuevo.rol = 'estudiante'
        if hasattr(nuevo, 'nombre'): nuevo.nombre = info.get('name') or candidate
        db.session.add(nuevo); db.session.commit()
        usuario = nuevo
        current_app.logger.info("Usuario creado id=%s", usuario.id)

    # asegurar/crear registro en Estudiante y usar su id si /app_estudiante lo requiere
    estudiante = None
    try:
        from sqlalchemy import inspect
        mapper = inspect(Estudiante)
        cols = list(mapper.columns)

        # detectar columna que vincula (usuario_id o id) y columnas obligatorias sin default
        link_col = None
        for c in cols:
            if c.name == 'usuario_id':
                link_col = 'usuario_id'
                break
        if not link_col:
            # fallback: asumir id compartido
            link_col = 'id'

        # buscar existente
        if link_col == 'usuario_id':
            estudiante = Estudiante.query.filter_by(usuario_id=usuario.id).first()
        else:
            estudiante = Estudiante.query.filter_by(id=usuario.id).first()

        # si no existe, construir kwargs validos y crear
        if not estudiante and db is not None:
            create_kwargs = {}
            # siempre asignar el link (usuario_id o id)
            create_kwargs[link_col] = usuario.id

            # nombre/display si hay campo apropiado
            display_name = getattr(usuario, 'nombre', None) or usuario.email.split('@')[0]
            # rellenar otros campos obligatorios (NOT NULL) con defaults por tipo
            for c in cols:
                if c.name == link_col or c.primary_key:
                    continue
                # saltar si tiene default o es nullable
                if c.nullable:
                    continue
                if c.default is not None:
                    continue
                # si ya asignamos algo para este campo, skip
                if c.name in create_kwargs:
                    continue
                # inferir tipo y asignar valor por defecto
                default_value = None
                try:
                    pytype = c.type.python_type
                    if pytype is str:
                        # para campos texto obligatorios usar nombre o cadena vacía
                        if c.name.lower() in ('nombre','nombre_completo','nombres'):
                            default_value = display_name
                        elif 'programa' in c.name.lower():
                            default_value = 'Sin programa'
                        else:
                            default_value = ''
                    elif pytype is int:
                        default_value = 0
                    elif pytype is float:
                        default_value = 0.0
                    elif pytype is bool:
                        default_value = False
                    else:
                        default_value = None
                except Exception:
                    # fallback a cadena vacía para evitar NOT NULL
                    default_value = ''
                create_kwargs[c.name] = default_value

            current_app.logger.info("Creando Estudiante con campos: %s", create_kwargs)
            estudiante = Estudiante(**create_kwargs)
            db.session.add(estudiante)
            db.session.commit()
    except Exception as e:
        if db:
            db.session.rollback()
        current_app.logger.exception("Error con tabla Estudiante: %s", e)
        estudiante = None

    # fijar session usando el id que /app_estudiante espera
    if estudiante:
        session['user_id'] = estudiante.id
    else:
        session['user_id'] = usuario.id
    session['rol'] = 'estudiante'
    session['usuario'] = email
    current_app.logger.info("Sesion seteada user_id=%s rol=estudiante", session['user_id'])

    # redirigir al panel de estudiante
    return redirect('/app_estudiante')

@routes.route('/docente/perfil', methods=['GET','POST'])
def perfil_docente():
    if 'usuario' not in session or session.get('rol') != 'docente':
        return redirect(url_for('routes.login'))

    usuario = Usuario.query.filter_by(email=session['usuario']).first()
    docente = Docente.query.filter_by(id=usuario.id).first()
    correo_institucional = docente.usuario.email

    if request.method == 'POST':
        # Solo actualiza los campos editables por el docente
        docente.celular = request.form.get('celular')
        docente.correo_personal = request.form.get('correo_personal')
        db.session.commit()
        flash('Datos actualizados correctamente', 'success')

    return render_template('perfil_docente.html', docente=docente, usuario=usuario, correo_institucional=correo_institucional)

@routes.route('/docente/inicio')
def inicio_docente():
    if 'usuario' not in session or session.get('rol') != 'docente':
        return redirect(url_for('routes.login'))
    return render_template('inicio_docente.html')

@routes.route('/docente/cursos')
def cursos_docente():
    from models import Docente, ProgramacionClase, Curso, Modulo, Programa, Salon, Periodo

    docente_id = session.get('user_id')
    if not docente_id:
        return redirect(url_for('routes.login'))

    # obtener periodo pedido por query string (puede ser id o codigo)
    periodo_param = request.args.get('periodo')  # ej. "2025-I" o "1"
    selected_period = None
    if periodo_param:
        # intentar por id primero
        try:
            pid = int(periodo_param)
            selected_period = Periodo.query.get(pid)
        except (ValueError, TypeError):
            selected_period = Periodo.query.filter_by(codigo=periodo_param).first()

    # si no se especifica, elegir el período activo más reciente
    if not selected_period:
        selected_period = Periodo.query.filter_by(estado='activo').order_by(Periodo.id.desc()).first()
        if not selected_period:
            selected_period = Periodo.query.order_by(Periodo.id.desc()).first()

    # obtener programaciones solo del periodo seleccionado (si hay)
    if selected_period:
        programaciones = ProgramacionClase.query.filter_by(docente_id=docente_id, periodo_id=selected_period.id).all()
    else:
        programaciones = []

    # lista de periodos para el selector
    periodos = Periodo.query.order_by(Periodo.id.desc()).all()

    cargas = []
    for prog in programaciones:
        curso = Curso.query.get(prog.curso_id)
        if not curso:
            continue
        modulo = Modulo.query.get(curso.modulo_id) if curso else None
        programa = Programa.query.get(modulo.programa_id) if modulo else None
        salon = Salon.query.get(prog.salon_id) if prog.salon_id else None
        
        # obtener número del módulo (fallback a id si no existe atributo 'numero')
        modulo_num = None
        if modulo:
            modulo_num = getattr(modulo, 'numero', None) or getattr(modulo, 'id', None)


        cargas.append({
            "codigo": curso.id,
            "nombre": curso.nombre,
            "modulo": modulo.nombre if modulo else "",
            "modulo_num": modulo_num,
            "programa": programa.nombre if programa else "",
            "periodo": getattr(selected_period, 'codigo', 'N/A'),
            "dia": prog.dia_semana,
            "hora": f"{prog.hora_inicio.strftime('%H:%M')} - {prog.hora_fin.strftime('%H:%M')}",
            "salon": salon.nombre if salon else "",
        })

    return render_template(
        'cursos_docente.html',
        cargas=cargas,
        periodos=periodos,
        periodo_seleccionado=getattr(selected_period, 'id', None)
    )

@routes.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente', 'success')
    return redirect(url_for('routes.login'))


@routes.route('/docente/evaluaciones')
def evaluaciones_docente():
    from models import Docente, ProgramacionClase, Curso, Matricula, Estudiante, Calificacion, Periodo, Modulo, Programa

    docente_id = session.get('user_id')
    if not docente_id:
        return redirect(url_for('routes.login'))

    # periodo (id o codigo)
    periodo_param = request.args.get('periodo')
    selected_period = None
    if periodo_param:
        try:
            pid = int(periodo_param)
            selected_period = Periodo.query.get(pid)
        except (ValueError, TypeError):
            selected_period = Periodo.query.filter_by(codigo=periodo_param).first()

    if not selected_period:
        selected_period = Periodo.query.filter_by(estado='activo').order_by(Periodo.id.desc()).first()
        if not selected_period:
            selected_period = Periodo.query.order_by(Periodo.id.desc()).first()

    # obtener programaciones del docente y (si aplica) del periodo
    query = ProgramacionClase.query.filter_by(docente_id=docente_id)
    if selected_period:
        query = query.filter_by(periodo_id=selected_period.id)
    programaciones = query.all()

    # construir lista única de cursos presentes en esas programaciones (para el selector)
    cursos_selector = []
    seen = set()
    for p in programaciones:
        if not p.curso_id or p.curso_id in seen:
            continue
        seen.add(p.curso_id)
        c = Curso.query.get(p.curso_id)
        if c:
            cursos_selector.append(c)

    # filtro por curso si se pasa ?curso=<id>
    curso_param = request.args.get('curso')
    selected_curso = None
    if curso_param:
        try:
            cid = int(curso_param)
            selected_curso = Curso.query.get(cid)
        except (ValueError, TypeError):
            selected_curso = None

    # si hay curso seleccionado, limitar programaciones a ese curso
    if selected_curso:
        programaciones = [p for p in programaciones if p.curso_id == selected_curso.id]
        # opcional: reducir el selector para mostrar solo ese curso como seleccionado
        # cursos_for_display = [selected_curso]
    else:
        # cursos_for_display = cursos_selector
        pass

    # ahora obtener cursos únicos finales a mostrar (los que provienen de programaciones filtradas)
    cursos = []
    seen = set()
    for p in programaciones:
        if not p.curso_id or p.curso_id in seen:
            continue
        seen.add(p.curso_id)
        curso = Curso.query.get(p.curso_id)
        if curso:
            cursos.append(curso)

    alumnos = []
    notas_alumnos = []
    for curso in cursos:
        matriculas = Matricula.query.filter_by(modulo_id=curso.modulo_id).all()
        for m in matriculas:
            estudiante = Estudiante.query.get(m.estudiante_id)
            if not estudiante:
                continue
            try:
                if estudiante.programa_estudio != curso.modulo.programa.nombre:
                    continue
            except Exception:
                pass
            notas = []
            for i in range(1, 7):
                cal = Calificacion.query.filter_by(
                    estudiante_id=estudiante.id,
                    curso_id=curso.id,
                    tipo_evaluacion=f"Nota {i}"
                ).first()
                notas.append(cal.valor if cal else "")
            alumnos.append({
                "codigo": estudiante.codigo,
                "curso": curso.nombre,
                "seccion": "", 
                "nombre": estudiante.nombre_completo,
                "notas": notas
            })
            notas_alumnos.append(notas)

    periodos = Periodo.query.order_by(Periodo.id.desc()).all()

    return render_template(
        'evaluaciones_docente.html',
        alumnos=alumnos,
        notas_alumnos=notas_alumnos,
        periodos=periodos,
        periodo_seleccionado=getattr(selected_period, 'id', None),
        cursos_selector=cursos_selector,
        curso_seleccionado=getattr(selected_curso, 'id', None)
    )


@routes.route('/docente/asistencia')
def asistencia_docente():
    from models import ProgramacionClase, Curso, Salon, Programa, Modulo, Periodo

    docente_id = session.get('user_id')
    if not docente_id:
        return redirect(url_for('routes.login'))

    # obtener periodo pedido por query string (puede ser id o codigo)
    periodo_param = request.args.get('periodo')  # ej. "2025-I" o "1"
    selected_period = None
    if periodo_param:
        try:
            pid = int(periodo_param)
            selected_period = Periodo.query.get(pid)
        except (ValueError, TypeError):
            selected_period = Periodo.query.filter_by(codigo=periodo_param).first()

    # si no se especifica, elegir el período activo más reciente
    if not selected_period:
        selected_period = Periodo.query.filter_by(estado='activo').order_by(Periodo.id.desc()).first()
        if not selected_period:
            selected_period = Periodo.query.order_by(Periodo.id.desc()).first()

    # obtener programaciones solo del periodo seleccionado (si hay)
    if selected_period:
        programaciones = ProgramacionClase.query.filter_by(docente_id=docente_id, periodo_id=selected_period.id).all()
    else:
        programaciones = []

    # lista de periodos para el selector
    periodos = Periodo.query.order_by(Periodo.id.desc()).all()

    cargas = []
    for prog in programaciones:
        curso = Curso.query.get(prog.curso_id)
        if not curso:
            continue
        modulo = Modulo.query.get(curso.modulo_id) if curso else None
        programa = Programa.query.get(modulo.programa_id) if modulo else None
        salon = Salon.query.get(prog.salon_id) if prog.salon_id else None
        
        modulo_num = None
        if modulo:
            modulo_num = getattr(modulo, 'numero', None ) or getattr(modulo, 'id', None)

        cargas.append({
            "codigo": curso.id,
            "nombre": curso.nombre,
            "modulo": modulo.nombre if modulo else "",
            "modulo_num": modulo_num,
            "programa": programa.nombre if programa else "",
            "periodo": getattr(selected_period, 'codigo', 'N/A'),
            "dia": prog.dia_semana,
            "hora": f"{prog.hora_inicio.strftime('%H:%M')} - {prog.hora_fin.strftime('%H:%M')}",
            "salon": salon.nombre if salon else "",
        })

    return render_template(
        'asistencia_docente.html',
        cargas=cargas,
        periodos=periodos,
        periodo_seleccionado=getattr(selected_period, 'id', None)
    )
# ...existing code...


@routes.route('/docente/curso/<int:codigo>/evaluaciones', methods=['GET', 'POST'])
def ingresar_notas(codigo):
    from models import Calificacion, Estudiante, Matricula, Curso
    from datetime import datetime

    curso = Curso.query.get(codigo)
    modulo_id = curso.modulo_id
    matriculas = Matricula.query.filter_by(modulo_id=modulo_id).all()

    # Determina la evaluación seleccionada
    if request.method == 'POST':
        evaluacion_actual = int(request.form.get("evaluacion", 1))
    else:
        evaluacion_actual = int(request.args.get("evaluacion", 1))

    estudiantes = []
    for m in matriculas:
        estudiante = Estudiante.query.get(m.estudiante_id)
        if not estudiante:
            continue
        if estudiante.programa_estudio != curso.modulo.programa.nombre:
            continue
        notas = {}
        for i in range(1, 7):
            cal = Calificacion.query.filter_by(
                estudiante_id=estudiante.id,  # Usar id numérico
                curso_id=codigo,
                tipo_evaluacion=f"Nota {i}"
            ).first()
            notas[f"nota_{i}"] = cal.valor if cal else ""
        estudiantes.append({
            "codigo": estudiante.codigo,
            "nombre": estudiante.nombre_completo,
            **notas
        })

    if request.method == 'POST':
        for est in estudiantes:
            nota = request.form.get(f"nota_{est['codigo']}")
            if nota is not None and nota != "":
                # Buscar el estudiante por código para obtener su ID
                estudiante_obj = Estudiante.query.filter_by(codigo=est['codigo']).first()
                if estudiante_obj:
                    calificacion = Calificacion.query.filter_by(
                        estudiante_id=estudiante_obj.id,  # Usar id numérico
                        curso_id=codigo,
                        tipo_evaluacion=f"Nota {evaluacion_actual}"
                    ).first()
                    if not calificacion:
                        calificacion = Calificacion(
                            estudiante_id=estudiante_obj.id,  # Usar id numérico
                            curso_id=codigo,
                            valor=float(nota),
                            tipo_evaluacion=f"Nota {evaluacion_actual}",
                            fecha_registro=datetime.now().date()
                        )
                        db.session.add(calificacion)
                    else:
                        calificacion.valor = float(nota)
                        calificacion.fecha_registro = datetime.now().date()
        db.session.commit()
        flash("Notas guardadas correctamente", "success")
        return redirect(url_for('routes.ingresar_notas', codigo=codigo, evaluacion=evaluacion_actual))

    return render_template('ingresar_notas.html', estudiantes=estudiantes, codigo=codigo, evaluacion_actual=evaluacion_actual)


@routes.route('/docente/curso/<int:codigo>/consolidado')
def consolidado_notas(codigo):
    from models import Calificacion, Estudiante, Matricula, Curso

    curso = Curso.query.get(codigo)
    modulo_id = curso.modulo_id
    matriculas = Matricula.query.filter_by(modulo_id=modulo_id).all()
    estudiantes = []
    for m in matriculas:
        estudiante = Estudiante.query.get(m.estudiante_id)
        if not estudiante:
            continue
        if estudiante.programa_estudio != curso.modulo.programa.nombre:
            continue
            
        indicadores = []
        suma = 0
        count = 0
        for i in range(1, 9):
            cal = Calificacion.query.filter_by(
                estudiante_id=estudiante.id,  # Usar id numérico
                curso_id=codigo,
                tipo_evaluacion=f"Nota {i}"
            ).first()
            valor = cal.valor if cal else ""
            indicadores.append(valor)
            if valor != "":
                suma += valor
                count += 1
        promedio = round(suma / count, 2) if count else ""
        estudiantes.append({
            "nombre": estudiante.nombre_completo,
            "indicadores": indicadores,
            "promedio": promedio,
            "recuperacion": "",  # Puedes calcularlo si tienes ese dato
            "nota_final": promedio  # O ajusta según tu lógica
        })

    docente = session.get('nombre_docente', 'Nombre Docente')
    return render_template('consolidado_notas.html', estudiantes=estudiantes, unidad=curso.nombre if curso else "Unidad Desconocida", docente=docente)


@routes.route('/docente/curso/<int:codigo>/estudiantes')
def ver_estudiantes(codigo):
    from models import Estudiante, Matricula, Curso

    curso = Curso.query.get(codigo)
    if not curso:
        flash("Curso no encontrado", "danger")
        return redirect(url_for('routes.cursos_docente'))

    modulo_id = curso.modulo_id
    matriculas = Matricula.query.filter_by(modulo_id=modulo_id).all()
    estudiantes = []
    for m in matriculas:
        estudiante = Estudiante.query.get(m.estudiante_id)
        if not estudiante:
            continue
        if estudiante.programa_estudio != curso.modulo.programa.nombre:
            continue
    
        estudiantes.append({
            "codigo": estudiante.codigo,
            "nombre": estudiante.nombre_completo,
            "programa": estudiante.programa_estudio,
        })
    return render_template('ver_estudiantes.html', estudiantes=estudiantes, codigo=codigo, curso_nombre=curso.nombre)


@routes.route('/docente/curso/<int:codigo>/registrar_asistencia', methods=['GET', 'POST'])
def registrar_asistencia(codigo):
    from models import Curso, Matricula, Estudiante, Asistencia
    from datetime import datetime, date

    curso = Curso.query.get(codigo)
    modulo_id = curso.modulo_id
    matriculas = Matricula.query.filter_by(modulo_id=modulo_id).all()
    estudiantes = []
    for m in matriculas:
        estudiante = Estudiante.query.get(m.estudiante_id)
        if not estudiante:
            continue
        if estudiante.programa_estudio != curso.modulo.programa.nombre:
            continue
        estudiantes.append(estudiante)

    if request.method == 'POST':
        fecha_str = request.form.get('fecha')
    else:
        fecha_str = request.args.get('fecha') or date.today().isoformat()
    fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    hoy = date.today()

    # Validación: no permitir fechas futuras
    if fecha > hoy:
        flash("No puedes registrar asistencia para fechas futuras.", "danger")
        #return redirect(url_for('routes.registrar_asistencia', codigo=codigo, fecha=hoy.isoformat()))

    # Diccionario para saber el estado actual de cada estudiante en esa fecha
    asistencias_dict = {}
    for estudiante in estudiantes:
        asistencia = Asistencia.query.filter_by(
            estudiante_id=estudiante.id,
            curso_id=curso.id,
            fecha=fecha
        ).first()
        asistencias_dict[estudiante.id] = asistencia.estado if asistencia else None

    # Registrar asistencia si es POST
    if request.method == 'POST':
        for estudiante in estudiantes:
            estado = request.form.get(f"asistencia_{estudiante.id}", "falta")
            asistencia = Asistencia.query.filter_by(
                estudiante_id=estudiante.id,
                curso_id=curso.id,
                fecha=fecha
            ).first()
            if asistencia:
                asistencia.estado = estado
                asistencia.justificada = False
            else:
                asistencia = Asistencia(
                    estudiante_id=estudiante.id,
                    curso_id=curso.id,
                    fecha=fecha,
                    estado=estado,
                    justificada=False
                )
                db.session.add(asistencia)
        db.session.commit()
        flash("Asistencia registrada correctamente", "success")
        return redirect(url_for('routes.registrar_asistencia', codigo=codigo, fecha=fecha_str))

    return render_template(
        'registrar_asistencia.html',
        estudiantes=estudiantes,
        codigo=codigo,
        curso_nombre=curso.nombre,
        fecha_actual=fecha_str,
        hoy=hoy.isoformat(),
        asistencias_dict=asistencias_dict
    )
    
    
@routes.route('/docente/curso/<int:codigo>/registrar_justificacion', methods=['GET', 'POST'])
def registrar_justificacion(codigo):
    from models import Asistencia, Estudiante, Curso
    from datetime import datetime

    curso = Curso.query.get(codigo)
    fecha_str = request.args.get('fecha')
    fecha = None
    faltas_info = []

    if fecha_str:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        # Solo busca faltas de esa fecha
        faltas = Asistencia.query.filter_by(
            curso_id=curso.id,
            estado='falta',
            justificada=False,
            fecha=fecha
        ).all()
        for f in faltas:
            estudiante = Estudiante.query.get(f.estudiante_id)
            if estudiante:
                faltas_info.append({
                    "asistencia_id": f.id,
                    "codigo": estudiante.codigo,
                    "nombre": estudiante.nombre_completo,
                    "fecha": f.fecha,
                    "observacion": f.observacion or ""
                })

    if request.method == 'POST':
        codigo_estudiante = request.form.get('codigo_estudiante')
        fecha_str = request.form.get('fecha')
        observacion = request.form.get('observacion', '')

        estudiante = Estudiante.query.filter_by(codigo=codigo_estudiante).first()
        if estudiante:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            asistencia = Asistencia.query.filter_by(
                estudiante_id=estudiante.id,
                curso_id=curso.id,
                fecha=fecha,
                estado='falta',
                justificada=False
            ).first()
            if asistencia:
                asistencia.justificada = True
                asistencia.observacion = observacion
                db.session.commit()
                flash("Falta justificada correctamente", "success")
            else:
                flash("No se encontró la falta para justificar.", "danger")
        else:
            flash("No se encontró el estudiante con ese código.", "danger")
        return redirect(url_for('routes.registrar_justificacion', codigo=codigo, fecha=fecha_str))

    return render_template(
        'registrar_justificacion.html',
        faltas=faltas_info,
        codigo=codigo,
        cursos_nombre=curso.nombre,
        fecha=fecha_str
    )

@routes.route('/docente/curso/<int:codigo>/reporte_asistencia')
def reporte_asistencia(codigo):
    from models import Curso, Estudiante, Matricula, Asistencia
    from datetime import datetime

    curso = Curso.query.get(codigo)
    modulo_id = curso.modulo_id
    matriculas = Matricula.query.filter_by(modulo_id=modulo_id).all()
    estudiantes = [
        Estudiante.query.get(m.estudiante_id)
        for m in matriculas
        if Estudiante.query.get(m.estudiante_id) and Estudiante.query.get(m.estudiante_id).programa_estudio == curso.modulo.programa.nombre
    ]

    # Obtener fechas filtradas
    fecha_inicio_str = request.args.get('fecha_inicio')
    fecha_fin_str = request.args.get('fecha_fin')
    asistencias_query = Asistencia.query.filter_by(curso_id=curso.id)
    if fecha_inicio_str:
        fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
        asistencias_query = asistencias_query.filter(Asistencia.fecha >= fecha_inicio)
    if fecha_fin_str:
        fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
        asistencias_query = asistencias_query.filter(Asistencia.fecha <= fecha_fin)

    asistencias = asistencias_query.all() if (fecha_inicio_str or fecha_fin_str) else []
    fechas = sorted(list({a.fecha for a in asistencias}))

    asistencia_dict = {e.id: {} for e in estudiantes}
    for a in asistencias:
        asistencia_dict[a.estudiante_id][a.fecha] = a.estado
        est_id = getattr(a, 'estudiante_id', None)
        fecha = getattr(a, 'fecha', None)
        estado = getattr(a, 'estado', None)
        # intentar obtener campo de justificación/observación si existe
        try:
            just = getattr(a, 'observacion', None) or getattr(a, 'justificacion', None) or ''
        except Exception:
            just = ''
        if est_id is not None:
            asistencia_dict.setdefault(est_id, {})[fecha] = {'estado': estado, 'justificacion': just}
            
    return render_template(
        'reporte_asis.html',
        estudiantes=estudiantes,
        fechas=fechas,
        asistencia_dict=asistencia_dict,
        curso_nombre=curso.nombre,
        codigo=codigo,
        fecha_inicio=fecha_inicio_str or "",
        fecha_fin=fecha_fin_str or ""
    )
    

@routes.route('/docente/material_academico', methods=['GET', 'POST'])
def material_academico():
    UPLOAD_ROOT = os.path.join(current_app.root_path, 'static', 'uploads', 'material_academico')
    ALLOWED_EXTENSIONS = {'pdf', 'xls', 'xlsx', 'csv', 'doc', 'docx', 'ppt', 'pptx'}

    periodo = request.form.get('periodo') or request.args.get('periodo') or 'general'
    curso = request.form.get('curso') or request.args.get('curso') or 'general'

    # crear carpeta por periodo/curso
    safe_periodo = secure_filename(str(periodo))
    safe_curso = secure_filename(str(curso))
    UPLOAD_FOLDER = os.path.join(UPLOAD_ROOT, safe_periodo, safe_curso)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    if request.method == 'POST':
        archivo = request.files.get('archivo')
        if archivo and '.' in archivo.filename and archivo.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
            filename = secure_filename(archivo.filename)
            ruta = os.path.join(UPLOAD_FOLDER, filename)
            archivo.save(ruta)
            flash("Archivo subido correctamente", "success")
        else:
            flash("Archivo no permitido", "danger")
        return redirect(url_for('routes.material_academico', periodo=periodo, curso=curso))

    # listar archivos del periodo/curso seleccionado
    archivos = []
    if os.path.exists(UPLOAD_FOLDER):
        archivos = os.listdir(UPLOAD_FOLDER)

    # además pasar listas de periodos y cursos para el selector en la plantilla
    # puedes obtenerlos desde la BD si tienes modelo Periodo/Curso:
    from models import Periodo, Curso as CursoModel
    periodos = Periodo.query.order_by(Periodo.id.desc()).all() if 'Periodo' in globals() or 'Periodo' in dir() else []
    cursos = CursoModel.query.order_by(CursoModel.id).all() if CursoModel else []

    return render_template(
        'material_academico.html',
        archivos=archivos,
        periodo_seleccionado=periodo,
        curso_seleccionado=curso,
        periodos=periodos,
        cursos=cursos
    )
    
    
@routes.route('/docente/horario')
def horario_docente():
    from models import ProgramacionClase, Curso, Salon
    docente_id = session.get('user_id')
    programaciones = ProgramacionClase.query.filter_by(docente_id=docente_id).all()
    horario = []
    for prog in programaciones:
        curso = Curso.query.get(prog.curso_id)
        salon = Salon.query.get(prog.salon_id) if prog.salon_id else None
        horario.append({
            "curso": curso.nombre if curso else "",
            "dia": prog.dia_semana,
            "hora_inicio": prog.hora_inicio.strftime('%H:%M'),
            "hora_fin": prog.hora_fin.strftime('%H:%M'),
            "salon": salon.nombre if salon else "",
            "periodo": getattr(prog.periodo, 'codigo', '2024-II') if hasattr(prog, 'periodo') and prog.periodo else '2024-II'
        })
    return render_template('horario_docente.html', horario=horario)

from flask import request, url_for, render_template, make_response
try:
    from weasyprint import HTML
except Exception:
    HTML = None

def _pdf_response_from_html(html, filename, inline=False):
    if HTML is None:
        return ("WeasyPrint no está instalado en el servidor", 500)
    pdf = HTML(string=html, base_url=request.base_url).write_pdf()
    resp = make_response(pdf)
    resp.headers['Content-Type'] = 'application/pdf'
    disposition = 'inline' if inline else 'attachment'
    resp.headers['Content-Disposition'] = f'{disposition}; filename={filename}'
    return resp

@routes.route('/docente/curso/<int:codigo>/reporte_curso_pdf_inline')
def reporte_curso_pdf_inline(codigo):
    try:
        from models import Curso, ProgramacionClase, Docente, Matricula, Estudiante, Modulo, Programa, Calificacion
    except Exception:
        Curso = ProgramacionClase = Docente = Matricula = Estudiante = Modulo = Programa = Calificacion = None

    curso = Curso.query.get(codigo) if Curso else None
    prog = ProgramacionClase.query.filter_by(curso_id=getattr(curso, 'id', None)).first() if ProgramacionClase and curso else None
    docente = Docente.query.get(getattr(prog, 'docente_id', None)) if prog and Docente else None
    modulo = Modulo.query.get(getattr(curso, 'modulo_id', None)) if Modulo and curso else None
    programa = None
    try:
        programa = Programa.query.get(getattr(modulo, 'programa_id', None)) if modulo and Programa else None
    except Exception:
        programa = None

    # Obtener matriculas del curso (prefiere curso_id, sino modulo_id)
    matriculas = []
    if Matricula and curso:
        try:
            if hasattr(Matricula, 'curso_id'):
                matriculas = Matricula.query.filter_by(curso_id=getattr(curso, 'id', None)).all()
            elif hasattr(Matricula, 'modulo_id'):
                matriculas = Matricula.query.filter_by(modulo_id=getattr(curso, 'modulo_id', None)).all()
            else:
                matriculas = []
        except Exception:
            matriculas = []

    # Forzar 6 notas visibles
    MAX_NOTAS = 6

    alumnos = []
    if Matricula and Estudiante and curso:
        for m in matriculas:
            est = Estudiante.query.get(getattr(m, 'estudiante_id', None))
            if not est:
                continue

            # filtrar por programa si corresponde
            try:
                if modulo and programa and hasattr(est, 'programa_estudio'):
                    if (getattr(est, 'programa_estudio', '') or '') != (getattr(programa, 'nombre', '') or ''):
                        continue
            except Exception:
                pass

            # obtener teléfono (varios posibles campos)
            telefono = ''
            try:
                telefono = (getattr(est, 'telefono', None) or
                            getattr(est, 'celular', None) or
                            (getattr(est, 'info', None) and getattr(est.info, 'celular', None)) or
                            '')
            except Exception:
                telefono = ''

            notas_list = []
            promedio = ""
            if Calificacion:
                cals = Calificacion.query.filter_by(estudiante_id=getattr(est, 'id', None), curso_id=getattr(curso, 'id', None)).all()
                cal_map = { (getattr(c, 'tipo_evaluacion', '') or ''): getattr(c, 'valor', '') for c in (cals or []) }
                for i in range(1, MAX_NOTAS + 1):
                    key = f"Nota {i}"
                    val = cal_map.get(key, "")
                    notas_list.append(val)
                valores = []
                for v in notas_list:
                    try:
                        if v is not None and v != "":
                            valores.append(float(v))
                    except Exception:
                        pass
                promedio = round(sum(valores) / len(valores), 2) if valores else ""

            alumnos.append({
                'codigo': getattr(est, 'codigo', ''),
                'nombre': getattr(est, 'nombre_completo', getattr(est, 'nombre', '')),
                'telefono': telefono,
                'notas': notas_list,
                'promedio': promedio
            })

    fecha = request.args.get('fecha') or ''
    html = render_template('reporte_curso.html',
                           curso=curso, docente=docente, modulo=modulo, programa=programa,
                           alumnos=alumnos, fecha=fecha, notas_count=MAX_NOTAS)
    return _pdf_response_from_html(html, f'reporte_curso_{codigo}.pdf', inline=True)

@routes.route('/docente/curso/<int:codigo>/reporte_asistencia_pdf_inline')
def reporte_asistencia_pdf_inline(codigo):
    try:
        from models import Curso, Matricula, Estudiante, Asistencia, Modulo, Programa, Docente, ProgramacionClase
    except Exception:
        Curso = Matricula = Estudiante = Asistencia = Modulo = Programa = Docente = ProgramacionClase = None

    curso = Curso.query.get(codigo) if Curso else None
    prog = ProgramacionClase.query.filter_by(curso_id=getattr(curso, 'id', None)).first() if ProgramacionClase and curso else None
    docente = Docente.query.get(getattr(prog, 'docente_id', None)) if prog and Docente else None
    modulo = Modulo.query.get(getattr(curso, 'modulo_id', None)) if Modulo and curso else None
    programa = None
    try:
        programa = Programa.query.get(getattr(modulo, 'programa_id', None)) if modulo and Programa else None
    except Exception:
        programa = None

    # Obtener matriculas del curso (prefiere curso_id)
    matriculas = []
    if Matricula and curso:
        try:
            if hasattr(Matricula, 'curso_id'):
                matriculas = Matricula.query.filter_by(curso_id=getattr(curso, 'id', None)).all()
            elif hasattr(Matricula, 'modulo_id'):
                matriculas = Matricula.query.filter_by(modulo_id=getattr(curso, 'modulo_id', None)).all()
            else:
                matriculas = []
        except Exception:
            matriculas = []

    # recopilar fechas globales del curso (para %)
    fechas = set()
    alumnos = []
    if Matricula and Estudiante and Asistencia and curso:
        # recopilar fechas solo entre matriculas válidas
        for m in matriculas:
            est_tmp = Estudiante.query.get(getattr(m, 'estudiante_id', None))
            if not est_tmp:
                continue
            # filtrar por programa si corresponde
            try:
                if modulo and programa and hasattr(est_tmp, 'programa_estudio'):
                    if (getattr(est_tmp, 'programa_estudio', '') or '') != (getattr(programa, 'nombre', '') or ''):
                        continue
            except Exception:
                pass
            rows = Asistencia.query.filter_by(estudiante_id=getattr(est_tmp, 'id', None), curso_id=getattr(curso, 'id', None)).all()
            for r in (rows or []):
                fechas.add(getattr(r, 'fecha', None))

        # luego crear la lista de alumnos a mostrar (solo matriculados y del programa)
        for m in matriculas:
            est = Estudiante.query.get(getattr(m, 'estudiante_id', None))
            if not est:
                continue
            try:
                if modulo and programa and hasattr(est, 'programa_estudio'):
                    if (getattr(est, 'programa_estudio', '') or '') != (getattr(programa, 'nombre', '') or ''):
                        continue
            except Exception:
                pass

            asistencias = Asistencia.query.filter_by(estudiante_id=getattr(est, 'id', None), curso_id=getattr(curso, 'id', None)).all()
            faltas = sum(1 for a in (asistencias or []) if (getattr(a, 'estado', '') or '').lower() in ('falta', 'absent', 'absente', 'no', 'n'))
            telefono = ''
            try:
                telefono = (getattr(est, 'telefono', None) or getattr(est, 'celular', None) or (getattr(est, 'info', None) and getattr(est.info, 'celular', None)) or '')
            except Exception:
                telefono = ''
            alumnos.append({
                'nombre': getattr(est, 'nombre_completo', getattr(est, 'nombre', '')),
                'codigo': getattr(est, 'codigo', ''),
                'faltas': faltas,
                'telefono': telefono
            })

    fechas = sorted([f for f in fechas if f is not None])
    total_sesiones_global = len(fechas) or 0
    for a in alumnos:
        a['porcentaje'] = round((a.get('faltas', 0) / total_sesiones_global) * 100, 2) if total_sesiones_global else 0.0
        a['excede_30'] = a['porcentaje'] > 30.0

    html = render_template('reporte_asistencia.html',
                           curso=curso, docente=docente, modulo=modulo, programa=programa,
                           alumnos=alumnos, fechas=fechas, fecha=request.args.get('fecha') or '')
    return _pdf_response_from_html(html, f'reporte_asistencia_{codigo}.pdf', inline=True)


@routes.route('/administrador/inicio')
def inicio_admin():
    if 'rol' in session and session['rol'] == 'administrador':
        return render_template('inicio_admin.html')
    else:
        flash('Acceso no autorizado', 'error')
        return redirect(url_for('routes.login'))

@routes.route('/administrador/dashboard')
def dashboard():
    return render_template('dashboard.html')

@routes.route('/administrador/estudiantes')
def estudiantes_admin():

    # importamos aquí para evitar ciclos al inicializar la app

    estudiantes = Estudiante.query.all()
    students_for_template = []

    for e in estudiantes:
        # datos básicos
        dni = getattr(e, 'dni', '') or ''
        nombre = getattr(e, 'nombre_completo', '') or ''
        programa = getattr(e, 'programa_estudio', '') or ''
        sexo = getattr(e, 'sexo', '') or ''
        edad = calcular_edad(getattr(e, 'fecha_nacimiento', None))
        celular = getattr(e, 'celular','') or ''
        # teléfono desde EstudianteInfo si existe


        # trabaja: por ahora no existe ese campo en tu modelo, dejar False
        trabaja = False

        # módulo: intentar sacar la matrícula más reciente y su módulo
        modulo_nombre = ''
        if getattr(e, 'matriculas', None):
            try:
                ultima = max(e.matriculas, key=lambda m: (getattr(m, 'fecha_matricula', None) or date.min, getattr(m, 'id', 0)))
            except Exception:
                ultima = e.matriculas[-1]
            if getattr(ultima, 'modulo', None):
                modulo_nombre = getattr(ultima.modulo, 'nombre', '') or ''

        students_for_template.append({
            "dni": dni,
            "nombre": nombre,
            "programa": programa,
            "sexo": sexo,
            "edad": edad,
            "telefono": celular,
            "trabaja": trabaja,
            "modulo": modulo_nombre,
        })

    return render_template('estudiantes_admin.html', students=students_for_template)

@routes.route('/administrador/programas')
def gestion_programas():


    # traer todas las ofertas (modulos activos) — puedes filtrar por estado si quieres
    modulos_activos = ModuloActivo.query.all()

    programas_activos = []
    count_activos = count_proximos = count_finalizados = 0
    hoy = date.today()

    for ma in modulos_activos:
        # fechas y estado
        inicio = ma.fecha_inicio
        fin = ma.fecha_fin
        estado = (ma.estado or "").lower()

        # estadísticas por fecha si quieres sobreescribir estado
        if estado == "activo" or (inicio and fin and inicio <= hoy <= fin):
            count_activos += 1
        elif inicio and inicio > hoy:
            count_proximos += 1
        else:
            count_finalizados += 1

        # docente asignado: si tienes ese campo en ModuloActivo, úsalo; si no, mostramos vacío
        docente_nombre = ""
        if hasattr(ma, 'docente') and ma.docente:
            # si añadiste relación docente en ModuloActivo
            docente_nombre = getattr(ma.docente, 'nombre_completo', '') or ''

        # contar estudiantes matriculados en esta oferta
        estudiantes_count = 0
        try:
            # intentamos contar matriculas relacionadas por modulo_activo_id
            estudiantes_count = Matricula.query.filter_by(modulo_activo_id=ma.id).count()
        except Exception:
            # si la tabla Matricula no tiene modulo_activo_id, fallback seguro a 0
            estudiantes_count = 0

        programas_activos.append({
            "id": ma.id,
            "programa_id": ma.programa_id,
            "programa_nombre": getattr(ma.programa, "nombre", "") if getattr(ma, "programa", None) else ma.programa_id,
            "modulo_id": ma.modulo_id,
            "modulo": getattr(ma.modulo, "nombre", "") if getattr(ma, "modulo", None) else "",
            "docente": docente_nombre,
            "inicio": inicio.strftime("%d/%m/%Y") if inicio else "",
            "fin": fin.strftime("%d/%m/%Y") if fin else "",
            "estudiantes": estudiantes_count,
            "estado": estado or "activo",
        })

    stats = {
        "activos": count_activos,
        "proximos": count_proximos,
        "finalizados": count_finalizados
    }

    return render_template('programas_admin.html',
                           stats=stats,
                           programas_activos=programas_activos)

@routes.route('/administrador/crear_estudiante', methods=['GET', 'POST'])
def crear_estudiante():
    if request.method == 'POST':
        # 1️⃣ Obtener datos del formulario
        dni = request.form.get('dni', '').strip()
        apellidos = request.form.get('apellidos', '').strip()
        nombres = request.form.get('nombres', '').strip()
        sexo = request.form.get('sexo', '').strip()
        fecha_nacimiento_raw = request.form.get('fecha_nacimiento', '').strip()
        pais = request.form.get('pais', '').strip()
        departamento = request.form.get('departamento', '').strip()
        provincia = request.form.get('provincia', '').strip()
        distrito = request.form.get('distrito', '').strip()
        programa = request.form.get('programa', '').strip()
        esta_trabajando = request.form.get('esta_trabajando') == 'on'
        centro_trabajo = request.form.get('centro_trabajo', '').strip()
        puesto_trabajo = request.form.get('puesto_trabajo', '').strip()
        estado_civil = request.form.get('estado_civil', '').strip()
        numero_hijos = request.form.get('numero_hijos', '').strip()
        celular = request.form.get('celular', '').strip()
        domicilio = request.form.get('domicilio', '').strip()
        nivel_educacion = request.form.get('nivel_educacion', '').strip()
        nombre_colegio = request.form.get('nombre_colegio', '').strip()
        celular_familiar_contacto = request.form.get('celular_familiar_contacto', '').strip()
        link_foto_dni = request.form.get('link_foto_dni', '').strip()
        medio_conocimiento = request.form.get('medio_conocimiento', '').strip()

        # 2️⃣ Validaciones básicas
        if not (dni and apellidos and nombres and sexo):
            flash("Por favor completa los campos obligatorios: DNI, apellidos, nombres y sexo.", "error")
            return render_template('crear_estudiante.html', form=request.form)

        # 3️⃣ Parsear fecha
        fecha_nacimiento = None
        if fecha_nacimiento_raw:
            for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
                try:
                    fecha_nacimiento = datetime.strptime(fecha_nacimiento_raw, fmt).date()
                    break
                except ValueError:
                    continue
            if not fecha_nacimiento:
                flash("Formato de fecha inválido. Usa DD/MM/AAAA.", "error")
                return render_template('crear_estudiante.html', form=request.form)

        # 4️⃣ Generar datos automáticos de usuario
        usuario_nombre = (nombres.split()[0].lower() if nombres else 'user') + dni[-3:]
        email_institucional = f"{usuario_nombre}@cedhi.edu.pe"
        codigo = f"EST-{dni}"

        # 5️⃣ Crear registros
        try:
            usuario = Usuario(
                usuario=usuario_nombre,
                password=generate_password_hash("123456"),
                email=email_institucional,
                rol="estudiante"
            )
            db.session.add(usuario)
            db.session.flush()

            estudiante = Estudiante(
                id=usuario.id,
                dni=dni,
                apellidos=apellidos,
                nombres=nombres,
                sexo=sexo,
                fecha_nacimiento=fecha_nacimiento,
                pais_nacimiento=pais or None,
                departamento_nacimiento=departamento or None,
                provincia_nacimiento=provincia or None,
                distrito_nacimiento=distrito or None,
                programa_estudio=programa or None,
                esta_trabajando=esta_trabajando,
                centro_trabajo=centro_trabajo or None,
                puesto_trabajo=puesto_trabajo or None,
                estado_civil=estado_civil or None,
                numero_hijos=int(numero_hijos) if numero_hijos else None,
                celular=celular or None,
                domicilio=domicilio or None,
                nivel_educacion=nivel_educacion or None,
                nombre_colegio=nombre_colegio or None,
                celular_familiar_contacto=celular_familiar_contacto or None,
                link_foto_dni=link_foto_dni or None,
                medio_conocimiento=medio_conocimiento or None,
            )

            db.session.add(estudiante)
            db.session.commit()

        except IntegrityError:
            db.session.rollback()
            flash("Error: ya existe un estudiante con ese DNI o usuario.", "error")
            return render_template('crear_estudiante.html', form=request.form)
        except Exception as e:
            db.session.rollback()
            flash("Error al crear el estudiante.", "error")
            print("Error:", e)
            return render_template('crear_estudiante.html', form=request.form)

        flash(f"Estudiante {apellidos} {nombres} creado correctamente.", "success")
        return redirect(url_for('routes.estudiantes_admin'))

    # GET -> renderizar formulario vacío
    return render_template('crear_estudiante.html', form={})

@routes.route('/administrador/programas/new', methods=['GET', 'POST'])
def abrir_programa():
    # Ya no necesitamos 'periodos' aquí
    programas = Programa.query.all()

    if request.method == 'POST':
        programa_id = request.form.get('programa_id')
        modulo_id = request.form.get('modulo_id')
        inicio_raw = request.form.get('fecha_inicio')
        fin_raw = request.form.get('fecha_fin')
        
        # 1. MODIFICAMOS LA VALIDACIÓN: Ya no buscamos 'periodo_id'
        if not (programa_id and modulo_id and inicio_raw and fin_raw):
            flash("Completa todos los campos obligatorios.", "error")
            return render_template('programa_new.html', programas=programas, form=request.form)

        # 2. PARSEAMOS LAS FECHAS (Tu código existente)
        fecha_inicio = None
        fecha_fin = None
        for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                fecha_inicio = datetime.strptime(inicio_raw, fmt).date()
                break
            except ValueError:
                pass
        for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                fecha_fin = datetime.strptime(fin_raw, fmt).date()
                break
            except ValueError:
                pass

        if not fecha_inicio or not fecha_fin or fecha_fin < fecha_inicio:
            flash("Fechas inválidas. Asegúrate que la fecha de fin sea posterior a la de inicio.", "error")
            return render_template('programa_new.html', programas=programas, form=request.form)

        # ==========================================================
        # 3. 🚀 LÓGICA AUTOMÁTICA DEL PERÍODO (AÑADE ESTO)
        # ==========================================================
        year = fecha_inicio.year
        month = fecha_inicio.month
        
        periodo_code = None
        
        if 3 <= month <= 7:  # De Marzo (3) a Julio (7)
            periodo_code = f"{year}-I"
        elif 8 <= month <= 12: # De Agosto (8) a Diciembre (12)
            periodo_code = f"{year}-II"
        else:
            # Caso de Enero (1) o Febrero (2)
            flash(f"La fecha de inicio '{inicio_raw}' no es válida. Los períodos solo pueden iniciar de Marzo a Diciembre.", "error")
            return render_template('programa_new.html', programas=programas, form=request.form)

        # Ahora, buscamos el ID de ese período en la DB
        periodo_obj = Periodo.query.filter_by(codigo=periodo_code).first()

        if not periodo_obj:
            # El período (ej. "2025-1") no existe. ¡Error crítico!
            flash(f"Error: El período académico '{periodo_code}' (requerido para esta fecha) no existe en la base de datos. Por favor, créelo primero en la sección de 'Períodos'.", "error")
            return render_template('programa_new.html', programas=programas, form=request.form)
        
        # ¡Éxito! Tenemos el ID
        periodo_id_encontrado = periodo_obj.id
        # ==========================================================
        # FIN DE LA LÓGICA DEL PERÍODO
        # ==========================================================

        # 4. crear ModuloActivo (MODIFICA ESTO)
        try:
            nuevo = ModuloActivo(
                programa_id=programa_id,
                modulo_id=int(modulo_id),
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                estado="activo",
                periodo_id=periodo_id_encontrado # <-- AÑADE ESTO
            )
            db.session.add(nuevo)
            db.session.flush()

            cursos_modulo = Curso.query.filter_by(modulo_id=modulo_id).all()
            for curso in cursos_modulo:
                ca = CursoActivo(
                    curso_id=curso.id,
                    modulo_activo_id=nuevo.id
                )
                db.session.add(ca)
                
            db.session.commit()
            flash("Módulo abierto correctamente.", "success")
            return redirect(url_for('routes.gestion_programas'))
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Error creando ModuloActivo:")
            flash("Ocurrió un error al crear la oferta del módulo.", "error")
            return render_template('programa_new.html', programas=programas, form=request.form)

    # 5. MODIFICA LA CARGA GET (Quita 'periodos')
    return render_template('programa_new.html', programas=programas, form={})



@routes.route('/_api/modulos/<programa_id>')
def api_modulos(programa_id):
    try:
        mods = Modulo.query.filter_by(programa_id=programa_id).all()
        return jsonify([
            {
                "id": m.id,
                "nombre": m.nombre,
                "periodo_academico": m.periodo_academico
            } for m in mods
        ])
    except Exception as e:
        routes.logger.exception("Error en /_api/modulos")
        return jsonify({"error": str(e)}), 500


@routes.route('/administrador/usuarios')
def gestion_usuarios():

    admins = Administrador.query.all()
    docentes = Docente.query.all()

    # Construir listas simples para la plantilla (evita pasar modelos crudos si prefieres)
    admins_list = []
    for a in admins:
        usuario = a.usuario if hasattr(a, 'usuario') and a.usuario else Usuario.query.get(a.id)
        admins_list.append({
            "id": a.id,
            "usuario": usuario.usuario if usuario else "",
            "email": usuario.email if usuario else "",
            "cargo": getattr(a, "cargo", ""),
        })

    docentes_list = []
    for d in docentes:
        usuario = d.usuario if hasattr(d, 'usuario') and d.usuario else Usuario.query.get(d.id)
        docentes_list.append({
            "id": d.id,
            "usuario": usuario.usuario if usuario else "",
            "email": usuario.email if usuario else "",
            "nombre_completo": getattr(d, "nombre_completo", "")
        })

    return render_template('usuarios_admin.html', admins=admins_list, docentes=docentes_list)

# CREAR DOCENTE
@routes.route('/administrador/usuarios/crear_docente', methods=['GET', 'POST'])
def crear_docente():

    if request.method == 'POST':
        usuario_nombre = request.form.get('usuario', '').strip()
        password = request.form.get('password', '').strip()
        email = request.form.get('email', '').strip()
        nombre_completo = request.form.get('nombre_completo', '').strip()
        dni = request.form.get('dni', '').strip()
        celular = request.form.get('celular', '').strip()
        correo_personal = request.form.get('correo_personal', '').strip()
        fecha_nacimiento_raw = request.form.get('fecha_nacimiento', '').strip()

        if not (usuario_nombre and password and email):
            flash("Completa usuario, contraseña y email.", "error")
            return render_template('crear_docente.html', form=request.form)

        # parseo de fecha opcional
        fecha_nacimiento = None
        if fecha_nacimiento_raw:
            try:
                fecha_nacimiento = datetime.strptime(fecha_nacimiento_raw, "%Y-%m-%d").date()
            except ValueError:
                flash("Fecha inválida. Usa formato YYYY-MM-DD.", "error")
                return render_template('crear_docente.html', form=request.form)

        try:
            usuario = Usuario(
                usuario=usuario_nombre,
                password=generate_password_hash(password),
                email=email,
                rol="docente"
            )
            db.session.add(usuario)
            db.session.flush()  # para obtener usuario.id

            docente = Docente(
                id=usuario.id,
                nombre_completo=nombre_completo or None,
                dni=dni or None,
                celular=celular or None,
                correo_personal=correo_personal or None,
                fecha_nacimiento=fecha_nacimiento
            )
            db.session.add(docente)
            db.session.commit()
            flash(f"Docente {nombre_completo or usuario_nombre} creado.", "success")
            return redirect(url_for('routes.gestion_usuarios'))

        except IntegrityError as ie:
            db.session.rollback()
            flash("Error: email o nombre de usuario ya existe.", "error")
            return render_template('crear_docente.html', form=request.form)
        except Exception as e:
            db.session.rollback()
            routes.logger.exception("Error creando docente:")
            flash("Ocurrió un error creando el docente.", "error")
            return render_template('crear_docente.html', form=request.form)

    # GET
    return render_template('crear_docente.html', form={})


# CREAR ADMINISTRADOR
@routes.route('/administrador/usuarios/crear_admin', methods=['GET', 'POST'])
def crear_admin():

    if request.method == 'POST':
        usuario_nombre = request.form.get('usuario', '').strip()
        password = request.form.get('password', '').strip()
        email = request.form.get('email', '').strip()
        cargo = request.form.get('cargo', '').strip()

        if not (usuario_nombre and password and email):
            flash("Completa usuario, contraseña y email.", "error")
            return render_template('crear_admin.html', form=request.form)

        try:
            usuario = Usuario(
                usuario=usuario_nombre,
                password=generate_password_hash(password),
                email=email,
                rol="administrador"
            )
            db.session.add(usuario)
            db.session.flush()

            admin = Administrador(
                id=usuario.id,
                cargo=cargo or None
            )
            db.session.add(admin)
            db.session.commit()
            flash(f"Administrador {usuario_nombre} creado.", "success")
            return redirect(url_for('routes.gestion_usuarios'))

        except IntegrityError:
            db.session.rollback()
            flash("Error: email o usuario ya existe.", "error")
            return render_template('crear_admin.html', form=request.form)
        except Exception:
            db.session.rollback()
            routes.logger.exception("Error creando administrador:")
            flash("Ocurrió un error creando el administrador.", "error")
            return render_template('crear_admin.html', form=request.form)

    return render_template('crear_admin.html', form={})

# ====== Asignar docentes a cada curso del módulo activo ======
@routes.route('/administrador/modulo_activo/<int:ma_id>/asignar_docentes', methods=['GET', 'POST'])
def asignar_docentes_modulo(ma_id):

    ma = ModuloActivo.query.get_or_404(ma_id)

    # Preferimos usar CursoActivo si existe (ofertas creadas al abrir módulo)
    cursos_activos = []
    if hasattr(ma, 'cursos_activos') and ma.cursos_activos:
        cursos_activos = ma.cursos_activos  # lista de CursoActivo
        use_curso_activo = True
    else:
        # fallback: usar lista de Cursos del módulo catálogo
        modulo_catalog = Modulo.query.get(ma.modulo_id)
        cursos_catalog = modulo_catalog.cursos if modulo_catalog else []
        cursos_activos = cursos_catalog
        use_curso_activo = False

    docentes = Docente.query.order_by(Docente.nombre_completo).all()

    if request.method == 'POST':
        try:
            # Esperamos inputs como "docente_for_<curso_or_curso_activo_id>"
            for item in request.form:
                if not item.startswith("docente_for_"):
                    continue
                pk = item.replace("docente_for_", "")
                docente_id = request.form.get(item) or None
                if not docente_id:
                    # si lo dejan vacío, desasignar
                    docente_id = None
                # localizar el objeto correspondiente
                if use_curso_activo:
                    ca = next((c for c in cursos_activos if str(c.id) == pk), None)
                    if ca:
                        # si CursoActivo tiene campo docente_id, asignar
                        if hasattr(ca, 'docente_id'):
                            ca.docente_id = int(docente_id) if docente_id else None
                        else:
                            # intentar asignar relación 'docente' si existe
                            if hasattr(ca, 'docente'):
                                # cargar docente y asociar vía atributo si existe
                                if docente_id:
                                    docobj = Docente.query.get(int(docente_id))
                                    if docobj:
                                        setattr(ca, 'docente', docobj)
                            else:
                                # no hay campo para guardar docente: ignorar/log
                                pass
                else:
                    # estamos usando catálogo Curso; puedes optar por crear CursoActivo aquí
                    curso_cat = next((c for c in cursos_activos if str(c.id) == pk), None)
                    if curso_cat:
                        # si quieres, crea un CursoActivo para esta oferta y asigna docente ahí
                        try:
                            nuevo = CursoActivo(
                                modulo_activo_id = ma.id,
                                programa_id = ma.programa_id,
                                modulo_id = ma.modulo_id,
                                curso_id = curso_cat.id,
                                fecha_inicio = ma.fecha_inicio,
                                fecha_fin = ma.fecha_fin,
                                estado = "activo"
                            )
                            db.session.add(nuevo)
                            db.session.flush()  # obtener id
                            if docente_id:
                                if hasattr(nuevo, 'docente_id'):
                                    nuevo.docente_id = int(docente_id)
                            # dejar que commit haga el resto
                        except Exception:
                            # si no existe CursoActivo en models, lo ignoramos
                            pass

            db.session.commit()
            flash("Asignaciones guardadas correctamente.", "success")
        except Exception:
            db.session.rollback()
            routes.logger.exception("Error asignando docentes:")
            flash("Ocurrió un error al guardar las asignaciones.", "error")
        return redirect(url_for('routes.gestion_programas'))

    # GET -> render
    return render_template('asignar_docentes.html',
                           modulo_activo=ma,
                           cursos=cursos_activos,
                           docentes=docentes,
                           use_curso_activo=use_curso_activo)

@routes.route('/administrador/modulo_activo/<int:ma_id>/matricular', methods=['GET', 'POST'])
def matricular_modulo(ma_id):
    ma = ModuloActivo.query.get_or_404(ma_id)

    if request.method == 'POST':
        estudiante_id = request.form.get('estudiante_id')
        curso_activo_id = request.form.get('curso_activo_id')  # Nuevo campo del formulario

        if not estudiante_id:
            flash("Selecciona un estudiante.", "error")
            return redirect(url_for('routes.matricular_modulo', ma_id=ma_id))

        try:
            nueva = Matricula(
                fecha_matricula=date.today(),
                estado="activa",
                estudiante_id=int(estudiante_id),
                modulo_id=ma.modulo_id,
                modulo_activo_id=ma.id
            )

            # Si seleccionó un curso específico (no vacío)
            if curso_activo_id and curso_activo_id != "modulo":
                nueva.curso_activo_id = int(curso_activo_id)

            db.session.add(nueva)
            db.session.commit()

            if nueva.curso_activo_id:
                flash("Estudiante matriculado en el curso correctamente.", "success")
            else:
                flash("Estudiante matriculado en todo el módulo correctamente.", "success")

        except Exception as e:
            db.session.rollback()
            routes.logger.exception("Error al matricular:")
            flash("Error al matricular al estudiante.", "error")

        return redirect(url_for('routes.matricular_modulo', ma_id=ma_id))

    # ==== GET ====
    from sqlalchemy import exists

    estudiantes_no = (Estudiante.query
                      .filter(~exists().where(Matricula.estudiante_id == Estudiante.id))
                      .all())

    # Soporte para búsqueda por DNI
    q = request.args.get('q') or request.form.get('q') if request.method == 'POST' else request.args.get('q')
    if q:
        q = q.strip()
        estudiantes_no = [e for e in estudiantes_no if q in (getattr(e, 'dni', '') or '')]

    # Pasamos también la lista de cursos activos del módulo para el <select>
    cursos_activos = ma.cursos_activos  # relación definida en ModuloActivo

    return render_template(
        'matricular_alumnos.html',
        modulo_activo=ma,
        estudiantes=estudiantes_no,
        cursos_activos=cursos_activos,
        query=q or ""
    )


@routes.route('/administrador/reportes')
def reportes_admin():
    programas = Programa.query.all()
    modulos = ["1","2","3","4"]
    periodos = ["2025-1", "2025-2"]
    return render_template('reportes.html', programas=programas, modulos=modulos, periodos=periodos)

@routes.route('/administrador/reportes/vista_previa', methods=['POST'])
def vista_previa_reporte():
    data = request.get_json()
    programa_id = data.get("programa_id")
    modulo = data.get("modulo")
    periodo = data.get("periodo")

    # Simulación: luego reemplaza con consultas reales
    reporte = [
        {"dni": "12345678", "nombre": "Juan Pérez", "asistencia": 95, "nota": 18, "estado": "Aprobado"},
        {"dni": "87654321", "nombre": "María González", "asistencia": 88, "nota": 16, "estado": "Aprobado"},
        {"dni": "11223344", "nombre": "Carlos Ruiz", "asistencia": 92, "nota": 14, "estado": "Aprobado"},
        {"dni": "55667788", "nombre": "Ana López", "asistencia": 75, "nota": 10, "estado": "Desaprobado"},
    ]

    return jsonify({"reporte": reporte})

@routes.route('/administrador/reportes/pdf', methods=['POST'])
def generar_pdf_reporte():
    data = request.get_json()
    reporte = data.get("reporte", [])
    programa = data.get("programa", "N/A")
    modulo = data.get("modulo", "N/A")
    periodo = data.get("periodo", "N/A")

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(100, 750, f"Reporte Académico - {programa}")
    p.setFont("Helvetica", 12)
    p.drawString(100, 730, f"Módulo: {modulo} | Periodo: {periodo}")
    p.drawString(100, 710, f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    y = 680
    p.setFont("Helvetica-Bold", 10)
    p.drawString(80, y, "DNI")
    p.drawString(160, y, "Nombre")
    p.drawString(300, y, "Asistencia")
    p.drawString(400, y, "Nota")
    p.drawString(470, y, "Estado")

    y -= 20
    p.setFont("Helvetica", 10)
    for est in reporte:
        p.drawString(80, y, est["dni"])
        p.drawString(160, y, est["nombre"])
        p.drawString(300, y, f"{est['asistencia']}%")
        p.drawString(400, y, str(est["nota"]))
        p.drawString(470, y, est["estado"])
        y -= 20
        if y < 100:
            p.showPage()
            y = 750

    p.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="reporte_academico.pdf", mimetype="application/pdf")



@routes.route('/')
def hello():
    return render_template('index.html')

