from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from flask_dance.contrib.google import make_google_blueprint, google
from werkzeug.security import generate_password_hash, check_password_hash
from models import *
from datetime import datetime, date
from sqlalchemy.exc import IntegrityError

routes = Blueprint('routes', __name__)

def calcular_edad(fecha_nac):
    if not fecha_nac:
        return None
    today = date.today()
    return today.year - fecha_nac.year - ((today.month, today.day) < (fecha_nac.month, fecha_nac.day))



def obtener_cursos_docente():
    docente_id = session.get('user_id')
    print("Docente ID:", docente_id)
    cursos = Curso.query.filter_by(docente_id=docente_id).all()
    print("Cursos encontrados:", cursos)
    return cursos

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
                print("Redirigiendo a React...")
                #  redirige al frontend React (en desarrollo)
                return redirect("http://localhost:5173/")
            else:
                return redirect(url_for('routes.inicio_admin'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    return render_template('login.html')

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
    #if 'usuario' in session:
    #    return redirect(url_for('routes.pagina_principal'))
    
    if not google.authorized:
        return redirect(url_for('google.login'))

    resp = google.get("https://www.googleapis.com/oauth2/v3/userinfo")

    if not resp.ok:
        flash("Error al obtener la información del usuario de Google.", "error")
        return redirect(url_for('routes.login'))

    user_info = resp.json()
    print("Response google: ", user_info)

    # Verificar que Google haya enviado un email
    if 'email' not in user_info:
        flash("Google no proporcionó una dirección de correo electrónico.", "error")
        return redirect(url_for('routes.login'))

    # Solo permitir correos institucionales
    if not user_info['email'].endswith('@ucsp.edu.pe'):
        flash("Solo se permite correos institucionales","error")
        return redirect(url_for('routes.login'))

    # Obtener ID Unico de google
    google_id = user_info.get("sub")

    # Verificar si el usuario ya esta registrado
    user = Usuario.query.filter_by(email=user_info['email']).first()
    if not user:
        user = Usuario(
            usuario=user_info.get("name", "Usuario sin nombre"),
            email=user_info['email'],
            password=None,
            rol='estudiante'
        )
        db.session.add(user)
        db.session.commit()

    session['usuario'] = user.usuario
    session['rol'] = user.rol
    return redirect(url_for('routes.pagina_principal'))

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
    if 'usuario' not in session or session.get('rol') != 'docente':
        return redirect(url_for('routes.login'))
    
    docente = Docente.query.filter_by(id=session['user_id']).first()
    cursos = []
    if docente:
        from models import ProgramacionClase, Curso, Modulo, Programa, Salon
        programaciones = ProgramacionClase.query.filter_by(docente_id=docente.id).all()
        for prog in programaciones:
            curso = Curso.query.get(prog.curso_id)
            modulo = Modulo.query.get(curso.modulo_id) if curso else None
            programa = Programa.query.get(modulo.programa_id) if modulo else None
            salon = Salon.query.get(prog.salon_id) if prog.salon_id else None
            if curso:
                cursos.append({
                    "codigo": curso.id,
                    "nombre": curso.nombre,
                    "modulo": modulo.nombre if modulo else "",
                    "programa": programa.nombre if programa else "",
                    "periodo": prog.periodo_academico,
                    "dia": prog.dia_semana,
                    "hora": f"{prog.hora_inicio.strftime('%H:%M')} - {prog.hora_fin.strftime('%H:%M')}",
                    "salon": salon.nombre if salon else "",
                })
    
    return render_template('cursos_docente.html', cargas=cursos)

@routes.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente', 'success')
    return redirect(url_for('routes.login'))

@routes.route('/docente/evaluaciones')
def evaluaciones_docente():
    from models import Docente, ProgramacionClase, Curso, Matricula, Estudiante, Calificacion

    docente_id = session.get('user_id')
    if not docente_id:
        return redirect(url_for('routes.login'))

    # Obtén los cursos asignados al docente
    programaciones = ProgramacionClase.query.filter_by(docente_id=docente_id).all()
    cursos = [Curso.query.get(p.curso_id) for p in programaciones]

    alumnos = []
    for curso in cursos:
        # Busca estudiantes matriculados en el módulo del curso
        matriculas = Matricula.query.filter_by(modulo_id=curso.modulo_id).all()
        for m in matriculas:
            estudiante = Estudiante.query.get(m.estudiante_id)
            if not estudiante:
                continue
            if estudiante.programa_estudio != curso.modulo.programa.nombre:
                continue
            notas = []
            for i in range(1, 9):
                cal = Calificacion.query.filter_by(
                    estudiante_id=estudiante.codigo,
                    curso_id=curso.id,
                    tipo_evaluacion=f"Nota {i}"
                ).first()
                notas.append(cal.valor if cal else "")
            alumnos.append({
                "codigo": estudiante.codigo,
                "curso": curso.nombre,
                "seccion": "",  # Si tienes sección, agrégala aquí
                "nombre": estudiante.nombre_completo,
                "notas": notas
            })

    return render_template('evaluaciones_docente.html', alumnos=alumnos)


@routes.route('/docente/asistencia')
def asistencia_docente():
    # Ejemplo: consulta real (ajusta según tus modelos)
    from models import ProgramacionClase, Curso, Salon, Programa, Modulo
    docente_id = session.get('user_id')
    programaciones = ProgramacionClase.query.filter_by(docente_id=docente_id).all()
    cargas = []
        
    for prog in programaciones:
        curso = Curso.query.get(prog.curso_id)
        modulo = Modulo.query.get(curso.modulo_id) if curso else None
        programa = Programa.query.get(modulo.programa_id) if modulo else None
        salon = Salon.query.get(prog.salon_id) if prog.salon_id else None

        cargas.append({
            "codigo": curso.id,
            "nombre": curso.nombre,
            "periodo": prog.periodo_academico,
            "modulo": modulo.nombre if modulo else "",
            "programa": programa.nombre if programa else "",
            "salon": salon.nombre if salon else "", 
        })
    return render_template('asistencia_docente.html', cargas=cargas)


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
        for i in range(1, 9):
            cal = Calificacion.query.filter_by(
                estudiante_id=estudiante.codigo,
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
                calificacion = Calificacion.query.filter_by(
                    estudiante_id=est['codigo'],
                    curso_id=codigo,
                    tipo_evaluacion=f"Nota {evaluacion_actual}"
                ).first()
                if not calificacion:
                    calificacion = Calificacion(
                        estudiante_id=est['codigo'],
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
                estudiante_id=estudiante.codigo,
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
    # Busca asistencias no justificadas y con estado 'falta'
    faltas = Asistencia.query.filter_by(curso_id=curso.id, estado='falta', justificada=False).all()
    # Relaciona cada falta con el estudiante y su código
    faltas_info = []
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
        return redirect(url_for('routes.registrar_justificacion', codigo=codigo))

    return render_template('registrar_justificacion.html', faltas=faltas_info, codigo=codigo, cursos_nombre=curso.nombre)


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

    asistencias = asistencias_query.all()
    fechas = sorted(list({a.fecha for a in asistencias}))

    asistencia_dict = {e.id: {} for e in estudiantes}
    for a in asistencias:
        asistencia_dict[a.estudiante_id][a.fecha] = a.estado

    return render_template(
        'reporte_asistencia.html',
        estudiantes=estudiantes,
        fechas=fechas,
        asistencia_dict=asistencia_dict,
        curso_nombre=curso.nombre,
        codigo=codigo,
        fecha_inicio=fecha_inicio_str or "",
        fecha_fin=fecha_fin_str or ""
    )
    
    
import os
from werkzeug.utils import secure_filename

@routes.route('/docente/material_academico', methods=['GET', 'POST'])
def material_academico():
    UPLOAD_FOLDER = 'static/uploads/material_academico'
    ALLOWED_EXTENSIONS = {'pdf', 'xls', 'xlsx', 'csv', 'doc', 'docx', 'ppt', 'pptx'}

    if request.method == 'POST':
        archivo = request.files.get('archivo')
        if archivo and '.' in archivo.filename and archivo.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
            filename = secure_filename(archivo.filename)
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            ruta = os.path.join(UPLOAD_FOLDER, filename)
            archivo.save(ruta)
            flash("Archivo subido correctamente", "success")
        else:
            flash("Archivo no permitido", "danger")
        return redirect(url_for('routes.material_academico'))

    archivos = []
    if os.path.exists(UPLOAD_FOLDER):
        archivos = os.listdir(UPLOAD_FOLDER)

    return render_template(
        'material_academico.html',
        archivos=archivos
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
            "periodo": prog.periodo_academico
        })
    return render_template('horario_docente.html', horario=horario)


@routes.route('/_api/modulos/<programa_id>')
def api_modulos(programa_id):
    from .models import Modulo
    mods = Modulo.query.filter_by(programa_id=programa_id).all()
    out = [{"id": m.id, "nombre": m.nombre, "periodo_academico": m.periodo_academico} for m in mods]
    return jsonify(out)

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

        # teléfono desde EstudianteInfo si existe
        telefono = ''
        if getattr(e, 'info', None):
            telefono = getattr(e.info, 'celular', '') or ''

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
            "telefono": telefono,
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
    
    # Import dinámico/relativo para evitar problemas de paquete
    from .models import Usuario, Estudiante, EstudianteInfo

    if request.method == 'POST':
        # Obtener campos del formulario
        apellidos = request.form.get('apellidos', '').strip()
        nombres = request.form.get('nombres', '').strip()
        nombre_completo = f"{apellidos} {nombres}".strip()
        programa = request.form.get('programa', '').strip()
        dni = request.form.get('dni', '').strip()
        sexo = request.form.get('sexo', '').strip()
        fecha_nacimiento_raw = request.form.get('fecha_nacimiento', '').strip()
        celular = request.form.get('celular', '').strip()
        direccion = request.form.get('direccion', '').strip()
        departamento = request.form.get('departamento', '').strip()
        provincia = request.form.get('provincia', '').strip()
        distrito = request.form.get('distrito', '').strip()

        # Validaciones mínimas
        if not (apellidos and nombres and programa and dni):
            flash("Por favor completa los campos obligatorios: apellidos, nombres, programa y DNI.", "error")
            return render_template('crear_estudiante.html', form=request.form)

        # Parsear fecha (acepta dd/mm/YYYY o d/m/YYYY)
        fecha_nacimiento = None
        if fecha_nacimiento_raw:
            for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
                try:
                    fecha_nacimiento = datetime.strptime(fecha_nacimiento_raw, fmt).date()
                    break
                except ValueError:
                    continue
            if not fecha_nacimiento:
                flash("Fecha de nacimiento inválida. Usa formato DD/MM/AAAA.", "error")
                return render_template('crear_estudiante.html', form=request.form)

        # Generar usuario/email/codigo por convención (puedes ajustar)
        usuario_nombre = (nombres.split()[0].lower() if nombres else 'user') + dni[-3:]
        email_institucional = f"{usuario_nombre}@cedhi.edu.pe"
        codigo = f"EST-{dni}"

        # Crear entradas en BD
        try:
            # 1) crear usuario
            usuario = Usuario(
                usuario=usuario_nombre,
                password=generate_password_hash("123456"),  # contraseña por defecto; pedir cambio luego
                email=email_institucional,
                rol="estudiante"
            )
            db.session.add(usuario)
            db.session.flush()  # obtener usuario.id sin commitear aún

            # 2) crear estudiante
            estudiante = Estudiante(
                id=usuario.id,
                nombre_completo=nombre_completo,
                programa_estudio=programa,
                codigo=codigo,
                dni=dni,
                sexo=sexo,
                fecha_nacimiento=fecha_nacimiento
            )
            db.session.add(estudiante)
            db.session.flush()

            # 3) crear info adicional
            info = EstudianteInfo(
                estudiante_id=estudiante.id,
                direccion=direccion or None,
                departamento=departamento or None,
                provincia=provincia or None,
                distrito=distrito or None,
                celular=celular or None
            )
            db.session.add(info)
            db.session.commit()

        except IntegrityError as ie:
            db.session.rollback()
            # detectar campo duplicado básico: email, dni o codigo únicos
            msg = str(ie.orig) if hasattr(ie, 'orig') else str(ie)
            if 'UNIQUE' in msg.upper() or 'unique' in msg.lower():
                flash("Error: ya existe un estudiante/usuario con ese DNI, código o email.", "error")
            else:
                flash("Error al crear el estudiante (integridad). Revisa los datos.", "error")
            return render_template('crear_estudiante.html', form=request.form)

        except Exception as e:
            db.session.rollback()
            routes.logger.exception("Error creando estudiante:")
            flash("Ocurrió un error al crear el estudiante.", "error")
            return render_template('crear_estudiante.html', form=request.form)

        flash(f"Estudiante {nombre_completo} creado correctamente (usuario: {usuario_nombre}).", "success")
        return redirect(url_for('routes.estudiantes_admin'))

    # GET -> mostrar formulario vacío
    return render_template('crear_estudiante.html', form={})

@routes.route('/administrador/programas/new', methods=['GET', 'POST'])
def abrir_programa():
    # Protección básica
    # importamos aquí para evitar import circular
    from .models import Programa, Modulo, ModuloActivo, db

    # Para GET -> cargar programas y módulos
    programas = Programa.query.all()

    if request.method == 'POST':
        programa_id = request.form.get('programa_id')
        modulo_id = request.form.get('modulo_id')
        inicio_raw = request.form.get('fecha_inicio')
        fin_raw = request.form.get('fecha_fin')

        if not (programa_id and modulo_id and inicio_raw and fin_raw):
            flash("Completa todos los campos obligatorios.", "error")
            return render_template('programa_new.html', programas=programas, form=request.form)

        # parsear fechas (DD/MM/YYYY o YYYY-MM-DD)
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

        # crear ModuloActivo
        try:
            nuevo = ModuloActivo(
                programa_id=programa_id,
                modulo_id=int(modulo_id),
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                estado="activo"
            )
            db.session.add(nuevo)
            db.session.commit()
            flash("Módulo abierto correctamente.", "success")
            return redirect(url_for('routes.gestion_programas'))
        except Exception as e:
            db.session.rollback()
            routes.logger.exception("Error creando ModuloActivo:")
            flash("Ocurrió un error al crear la oferta del módulo.", "error")
            return render_template('programa_new.html', programas=programas, form=request.form)

    # GET
    return render_template('programa_new.html', programas=programas, form={})

@routes.route('/administrador/usuarios')
def gestion_usuarios():

    # import relativo para evitar ciclos
    from .models import Administrador, Docente, Usuario

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

    from .models import Usuario, Docente, db

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

    from .models import Usuario, Administrador, db

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

    # import local para evitar ciclos
    from .models import ModuloActivo, CursoActivo, Curso, Docente, db, Modulo

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
                                    from .models import Docente as DocModel
                                    docobj = DocModel.query.get(int(docente_id))
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


# ====== Matricular alumnos en el ModuloActivo ======
@routes.route('/administrador/modulo_activo/<int:ma_id>/matricular', methods=['GET', 'POST'])
def matricular_modulo(ma_id):

    from .models import ModuloActivo, Estudiante, Matricula, db

    ma = ModuloActivo.query.get_or_404(ma_id)

    # Construir query para alumnos NO matriculados en *ningún* modulo
    # Intentamos usar Matricula.modulo_activo_id si existe; si no, buscar por cualquier Matricula existente
    try:
        # ver si Matricula tiene columna modulo_activo_id
        has_mod_act = hasattr(Matricula, 'modulo_activo_id')
    except Exception:
        has_mod_act = False

    if request.method == 'POST':
        estudiante_id = request.form.get('estudiante_id')
        if not estudiante_id:
            flash("Selecciona un estudiante.", "error")
            return redirect(url_for('routes.matricular_modulo', ma_id=ma_id))

        try:
            nueva = Matricula(
                fecha_matricula = date.today(),
                estado = "activa",
                estudiante_id = int(estudiante_id),
                modulo_id = ma.modulo_id
            )
            # si la tabla tiene modulo_activo_id, guárdala también
            if has_mod_act:
                nueva.modulo_activo_id = ma.id
            db.session.add(nueva)
            db.session.commit()
            flash("Estudiante matriculado correctamente.", "success")
        except Exception:
            db.session.rollback()
            routes.logger.exception("Error al matricular:")
            flash("Error al matricular al estudiante.", "error")
        return redirect(url_for('routes.gestion_programas'))

    # GET -> listar estudiantes NO matriculados
    # Si la Matricula tiene modulo_activo_id, consideramos alumnos matriculados si existen matriculas con cualquier modulo_activo_id
    # Fallback: si Matricula existe en cualquier forma, lo consideramos matriculado
    subq = None
    try:
        # usar subquery de Matricula para excluir estudiantes que ya tengan ANY matricula
        from sqlalchemy import exists
        estudiantes_no = (Estudiante.query
                          .filter(~exists().where(Matricula.estudiante_id == Estudiante.id))
                          .all())
    except Exception:
        # fallback simple: tomar todos (si algo falla)
        estudiantes_no = Estudiante.query.all()

    # soportar búsqueda por dni (query param 'q' o formulario)
    q = request.args.get('q') or request.form.get('q') if request.method == 'POST' else request.args.get('q')
    if q:
        q = q.strip()
        estudiantes_no = [e for e in estudiantes_no if q in (getattr(e,'dni','') or '')]

    return render_template('matricular_alumnos.html',
                           modulo_activo=ma,
                           estudiantes=estudiantes_no,
                           query=q or "")


@routes.route('/')
def hello():
    return render_template('index.html')

