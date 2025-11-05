from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint, CheckConstraint, text
import datetime
db = SQLAlchemy()

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    usuario = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=True) # Puede ser falso si solo se usa Google
    email = db.Column(db.String(120), unique=False, nullable = False)
    rol = db.Column(db.String(20), nullable=False) # 'administrador', 'docente', 'estudiante'

    # Relaciones 1:1 a roles
    estudiante = db.relationship("Estudiante", back_populates="usuario", uselist=False)
    docente = db.relationship("Docente", back_populates="usuario", uselist=False)
    administrador = db.relationship("Administrador", back_populates="usuario", uselist=False)
    
    # Relaciones 1:N (listas)
    tramites_gestionados = db.relationship('SolicitudTramite', foreign_keys='SolicitudTramite.admin_id', back_populates='administrador_usuario', lazy=True)

class Docente(db.Model):
    __tablename__ = "docentes"
    id = db.Column(db.Integer, db.ForeignKey('usuario.id'), primary_key=True)
    nombre_completo = db.Column(db.String(120))
    dni = db.Column(db.String(15))
    celular = db.Column(db.String(9))
    correo_personal = db.Column(db.String(120))
    fecha_nacimiento = db.Column(db.Date)
    
    usuario = db.relationship('Usuario', back_populates='docente', uselist=False)
    programaciones = db.relationship("ProgramacionClase", back_populates="docente", lazy=True)
    
    # Relaciones 1:N (listas)
    cursos_asignados = db.relationship('CursoActivo', back_populates='docente', lazy=True)
class Estudiante(db.Model):
    __tablename__ = "estudiantes"

    # Identificador (mismo que usuario)
    id = db.Column(db.Integer, db.ForeignKey("usuario.id"), primary_key=True)

    # Datos personales básicos
    dni = db.Column(db.String(15), unique=True, nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    nombre_completo = db.Column(db.String(100), nullable=False)
    sexo = db.Column(db.String(10), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=True)
    correo = db.Column(db.String(120), unique=True, nullable=True)

    # Lugar de nacimiento
    pais_nacimiento = db.Column(db.String(60), nullable=True)
    departamento_nacimiento = db.Column(db.String(60), nullable=True)
    provincia_nacimiento = db.Column(db.String(60), nullable=True)
    distrito_nacimiento = db.Column(db.String(60), nullable=True)

    # Información académica y laboral
    programa_estudio = db.Column(db.String(100), nullable=True)
    esta_trabajando = db.Column(db.Boolean, nullable=False, default=False)
    centro_trabajo = db.Column(db.String(120), nullable=True)
    puesto_trabajo = db.Column(db.String(120), nullable=True)
    nivel_educacion = db.Column(db.String(100), nullable=True)
    nombre_colegio = db.Column(db.String(120), nullable=True)

    # Información adicional
    estado_civil = db.Column(db.String(30), nullable=True)
    numero_hijos = db.Column(db.Integer, nullable=True)
    celular = db.Column(db.String(20), nullable=True)
    domicilio = db.Column(db.String(200), nullable=True)
    celular_familiar_contacto = db.Column(db.String(20), nullable=True)
    link_foto_dni = db.Column(db.String(255), nullable=True)
    medio_conocimiento = db.Column(db.String(150), nullable=True)

    # Relaciones
    usuario = db.relationship("Usuario", back_populates="estudiante", uselist=False)
    info = db.relationship("EstudianteInfo", back_populates="estudiante", uselist=False)

    # Relaciones 1:N (listas)
    matriculas = db.relationship("Matricula", back_populates="estudiante", lazy=True)
    tramites = db.relationship("SolicitudTramite", back_populates="estudiante", lazy=True)
    
    def __repr__(self):
        return f"<Estudiante {self.apellidos}, {self.nombre_completo}>"

# Tabla secundaria con campos opcionales/editables
class EstudianteInfo(db.Model):
    __tablename__ = "estudiantes_info"
    estudiante_id = db.Column(db.Integer, db.ForeignKey("estudiantes.id"), primary_key=True)
    direccion = db.Column(db.String(200), nullable=True)
    departamento = db.Column(db.String(100), nullable=True)
    provincia = db.Column(db.String(100), nullable=True)
    distrito = db.Column(db.String(100), nullable=True)
    celular = db.Column(db.String(20), nullable=True)

    # Contacto de emergencia
    contacto_nombre = db.Column(db.String(120), nullable=True)
    contacto_parentesco = db.Column(db.String(50), nullable=True)
    contacto_telefono = db.Column(db.String(20), nullable=True)
    contacto_nombre_2 = db.Column(db.String(120), nullable=True)
    contacto_parentesco_2 = db.Column(db.String(50), nullable=True)
    contacto_telefono_2 = db.Column(db.String(20), nullable=True)
    # Relación inversa
    estudiante = db.relationship("Estudiante", back_populates="info")

    def __repr__(self):
        return f"<Info de Estudiante {self.estudiante_id}>"
# =========================
# NUEVAS TABLAS (del diagrama)
# =========================

class Administrador(db.Model):
    __tablename__ = "administradores" 
    id = db.Column(db.Integer, db.ForeignKey("usuario.id"), primary_key=True)
    cargo = db.Column(db.String(80), nullable=True)

    usuario = db.relationship("Usuario", back_populates="administrador", uselist=False)    

    def __repr__(self):
        return f"<Administrador {self.id}>"


class Periodo(db.Model):
    __tablename__ = "periodos"
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False) # Ej: "2025-I"
    fecha_inicio = db.Column(db.Date, nullable=True)
    fecha_fin = db.Column(db.Date, nullable=True)
    estado = db.Column(db.String(20), default="activo") # activo, cerrado, planificado

    #  NUEVA RELACIÓN: Un Periodo agrupa muchas Ofertas de Módulos
    modulos_activos = db.relationship("ModuloActivo", back_populates="periodo", lazy=True)
    
    __table_args__ = (
        # 🚨 RESTRICCIÓN CRÍTICA CORREGIDA: Usando text() para evitar la evaluación prematura
        # y envolviendo el argumento de dialecto dentro del UniqueConstraint.
        # UniqueConstraint('estado',                 name='uq_unico_periodo_activo', postgresql_where=text("estado = 'activo'")),
        # CheckConstraint se mantiene, asegurando la validez del texto del estado
        CheckConstraint("estado IN ('activo','cerrado','planificado')", name='ck_periodo_estado_valido'),

    )

    def __repr__(self):
        return f"<Periodo {self.codigo} ({self.estado})>"
    
# ----------------------------------------------------
# CATÁLOGO ACADÉMICO (PLANTILLAS)
# ----------------------------------------------------

class Programa(db.Model):
    __tablename__ = "programas"
    # En el diagrama idPrograma es string; mantenemos cadena como PK
    id = db.Column(db.String(20), primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    total_creditos = db.Column(db.Integer, nullable=True)
    total_horas = db.Column(db.Integer, nullable=True)

    # Relación: Programa -> Módulos (1 a N)
    modulos = db.relationship(
        "Modulo",
        back_populates="programa",
        cascade="all, delete-orphan",
        lazy=True
    )
    modulos_activos = db.relationship("ModuloActivo", back_populates="programa", lazy=True)

    def __repr__(self):
        return f"<Programa {self.id} - {self.nombre}>"


class Modulo(db.Model):
    __tablename__ = "modulos"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    unidad_competencia = db.Column(db.String(120), nullable=True)
    num_modulo = db.Column(db.Integer, nullable=False, default=1)
    # FK al Programa (composición en el diagrama)
    programa_id = db.Column(db.String(20), db.ForeignKey("programas.id", ondelete="RESTRICT"), nullable=False)
    programa = db.relationship("Programa", back_populates="modulos")

    # Relación: Módulo -> Cursos (1 a N)
    cursos = db.relationship("Curso", back_populates="modulo", cascade="all, delete-orphan", lazy=True, )
    ofertas = db.relationship("ModuloActivo", back_populates="modulo", lazy="dynamic")
    tramites = db.relationship("SolicitudTramite", back_populates="modulo", lazy="dynamic")

    # Relación: Módulo -> Matrículas (1 a N)
    matriculas = db.relationship("Matricula", back_populates="modulo", cascade="all, delete-orphan", lazy=True, )
    periodo_academico = db.Column(db.String(50), nullable=True)
    def __repr__(self):
        return f"<Modulo {self.id} - {self.nombre}>"


class Curso(db.Model):
    __tablename__ = "cursos"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    horas_teoricas = db.Column(db.Integer, nullable=True)
    horas_practicas = db.Column(db.Integer, nullable=True)
    contenidos = db.Column(db.Text, nullable=True)
    # Almacena la ruta o el nombre del archivo PDF
    ruta_silabo = db.Column(db.String(255), nullable=True)
    # Sesiones programadas
    sesiones_programadas = db.Column(db.Integer, nullable=True)
    # FK al Módulo (composición en el diagrama)
    modulo_id = db.Column(db.Integer, db.ForeignKey("modulos.id", ondelete="RESTRICT"), nullable=False)
    modulo = db.relationship("Modulo", back_populates="cursos")

    cursos_activos = db.relationship('CursoActivo', back_populates='curso', lazy=True)

    def __repr__(self):
        return f"<Curso {self.id} - {self.nombre}>"


class Salon(db.Model):
    __tablename__ = "salones"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    capacidad = db.Column(db.Integer, nullable=True)
    caracteristicas = db.Column(db.String(200), nullable=True)
    fecha_registro = db.Column(db.Date, nullable=True)

    programaciones = db.relationship("ProgramacionClase", back_populates="salon", cascade="all, delete-orphan", lazy=True)

    def __repr__(self):
        return f"<Salon {self.nombre}>"

# ----------------------------------------------------
# OFERTA ACADÉMICA (INSTANCIAS EN EL TIEMPO)
# ----------------------------------------------------

class ModuloActivo(db.Model):
    __tablename__ = "modulos_activos"

    id = db.Column(db.Integer, primary_key=True)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    estado = db.Column(db.String(20), nullable=False, default="activo")  # activo | finalizado | suspendido
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    programa_id = db.Column(db.String(20), db.ForeignKey("programas.id", ondelete="RESTRICT"), nullable=False)
    modulo_id = db.Column(db.Integer, db.ForeignKey("modulos.id", ondelete="RESTRICT"), nullable=False)

    periodo_id = db.Column(db.Integer, db.ForeignKey("periodos.id"), nullable=False)

    # Relaciones
    periodo = db.relationship("Periodo", back_populates="modulos_activos")
    programa = db.relationship("Programa", back_populates="modulos_activos")
    modulo = db.relationship("Modulo", back_populates="ofertas")
    cursos_activos = db.relationship('CursoActivo', back_populates='modulo_activo', lazy=True)
    #__table_args__ = (
        # La oferta debe estar dentro del rango de su periodo
        # CheckConstraint(db.column('fecha_inicio') >= db.select([Periodo.fecha_inicio]).where(Periodo.id == db.column('periodo_id')).scalar_subquery(), name='ck_oferta_inicio_valido'),
        # CheckConstraint(db.column('fecha_fin') <= db.select([Periodo.fecha_fin]).where(Periodo.id == db.column('periodo_id')).scalar_subquery(), name='ck_oferta_fin_valido')
    #)

    def __repr__(self):
        return f"<ModuloActivo id={self.id} modulo={self.modulo_id} prog={self.programa_id} {self.estado}>"

class CursoActivo(db.Model):
    __tablename__ = 'cursos_activos'                # nombre de tabla consistente (plural)
    id = db.Column(db.Integer, primary_key=True)

    # FK al ModuloActivo (tabla definida como "modulos_activos")
    modulo_activo_id = db.Column(db.Integer, db.ForeignKey('modulos_activos.id', ondelete="CASCADE"), nullable=False)

    # FK al curso del catálogo (tabla "cursos")
    curso_id = db.Column(db.Integer, db.ForeignKey('cursos.id', ondelete="RESTRICT"), nullable=False)

    # Relación al docente (tu tabla de usuarios/docentes)
    # Tu tabla Usuario no tiene __tablename__ explícito, su tabla es "usuario" (lowercase class name)
    docente_id = db.Column(db.Integer, db.ForeignKey('docentes.id'), nullable=True)

    # Relaciones ORM
    modulo_activo = db.relationship('ModuloActivo', back_populates='cursos_activos')
    curso = db.relationship('Curso', back_populates='cursos_activos')
    docente = db.relationship('Docente', back_populates='cursos_asignados')
    programaciones = db.relationship("ProgramacionClase", back_populates="curso_activo", lazy=True)
    matricula_cursos = db.relationship("MatriculaCurso", back_populates="curso_activo", lazy=True)

    def __repr__(self):
        return f"<CursoActivo {self.id} - curso {self.curso_id} en ModuloActivo {self.modulo_activo_id}>"


# ----------------------------------------------------
# TABLAS DE REGISTRO (VINCULADAS A LA OFERTA)
# ---------------------------------------------------

class ProgramacionClase(db.Model):
    __tablename__ = "programaciones_clase"
    id = db.Column(db.Integer, primary_key=True)
    dia_semana = db.Column(db.String(15), nullable=False)  # 'Lunes'...'Domingo'
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    # FKs
    curso_activo_id = db.Column(db.Integer, db.ForeignKey('cursos_activos.id', ondelete="CASCADE"), nullable=False)
    salon_id = db.Column(db.Integer, db.ForeignKey("salones.id", ondelete="RESTRICT"), nullable=False)
    docente_id = db.Column(db.Integer, db.ForeignKey("docentes.id", ondelete="SET NULL"), nullable=True)
    # Relaciones
    curso_activo = db.relationship("CursoActivo", back_populates="programaciones")
    salon = db.relationship("Salon", back_populates="programaciones")
    docente = db.relationship("Docente", back_populates="programaciones")
    
    __table_args__ = (
        #UniqueConstraint('curso_activo_id', 'salon_id', 'dia_semana', 'hora_inicio', name='uq_instancia_salon_horario'),
        CheckConstraint("hora_fin > hora_inicio", name='ck_hora_fin_gt_inicio'),

    )

    def __repr__(self):
        return f"<ProgClase curso={self.curso_activo_id} {self.dia_semana} {self.hora_inicio}-{self.hora_fin}>"

class Matricula(db.Model):
    __tablename__ = "matriculas"
    id = db.Column(db.Integer, primary_key=True)
    fecha_matricula = db.Column(db.Date, nullable=False)
    estado = db.Column(db.String(30), nullable=False, default="activa")  
    # FKs
    estudiante_id = db.Column(db.Integer, db.ForeignKey("estudiantes.id", ondelete="CASCADE"), nullable=False)
    modulo_id = db.Column(db.Integer, db.ForeignKey("modulos.id", ondelete="RESTRICT"), nullable=False)
    modulo_activo_id = db.Column(db.Integer, db.ForeignKey("modulos_activos.id", ondelete="SET NULL"), nullable=True)
    # 🔹 NUEVO: Permite matrícula específica a un curso dentro del módulo activo (opcional)
    curso_activo_id = db.Column(db.Integer, db.ForeignKey("cursos_activos.id", ondelete="SET NULL"), nullable=True)
    cursos_inscritos = db.relationship("MatriculaCurso", back_populates="matricula", cascade="all, delete-orphan", lazy=True)
    # Relaciones (usar back_populates para coincidir con Estudiante.matriculas)
    estudiante = db.relationship("Estudiante", back_populates="matriculas", lazy=True)
    modulo = db.relationship("Modulo", back_populates="matriculas")
    modulo_activo = db.relationship("ModuloActivo", backref=db.backref("matriculas", lazy=True))
    curso_activo = db.relationship("CursoActivo", backref=db.backref("matriculas", lazy=True))

    __table_args__ = (
        db.UniqueConstraint('estudiante_id', 'modulo_id', 'fecha_matricula', name='uq_matricula_est_mod_fecha'),
    )
    def __repr__(self):
        tipo = "curso" if self.curso_activo_id else "módulo"
        return f"<Matricula id={self.id} est={self.estudiante_id} {tipo}={self.curso_activo_id or self.modulo_id} estado={self.estado}>"

class MatriculaCurso(db.Model):
    """
    Tabla de Detalle: Vincula una Matrícula (bloque) a los Cursos Activos específicos.
    Aquí se registran notas y asistencias, ya que es el nivel más granular.
    """
    __tablename__ = "matricula_curso_detalle"
    id = db.Column(db.Integer, primary_key=True)
    #  FK a la Matrícula padre
    matricula_id = db.Column(db.Integer, db.ForeignKey('matriculas.id', ondelete="CASCADE"), nullable=False)
    # FK al Curso Activo (la unidad de enseñanza)
    curso_activo_id = db.Column(db.Integer, db.ForeignKey('cursos_activos.id', ondelete="RESTRICT"), nullable=False)
    # Relaciones
    matricula = db.relationship("Matricula", back_populates="cursos_inscritos")
    curso_activo = db.relationship("CursoActivo", back_populates="matricula_cursos") # OK
    calificaciones = db.relationship("Calificacion", back_populates="matricula_curso", cascade="all, delete-orphan", lazy=True)
    asistencias = db.relationship("Asistencia", back_populates="matricula_curso", cascade="all, delete-orphan", lazy=True)

    __table_args__ = (
        # Asegura que un estudiante no se matricule dos veces en el mismo curso activo
        UniqueConstraint('matricula_id', 'curso_activo_id', name='uq_matricula_curso_unica'),
    )


class Calificacion(db.Model):
    __tablename__ = "calificaciones"
    id = db.Column(db.Integer, primary_key=True)
    valor = db.Column(db.Float, nullable=False)  # 0.0 - 20.0, por ejemplo
    indicador_logro = db.Column(db.String(50), nullable=True)  # A, B, C... o texto
    tipo_evaluacion = db.Column(db.String(50), nullable=True)  # Parcial, Práctica, Proyecto...
    fecha_registro = db.Column(db.Date, nullable=False)

    # FKs
    # Apunta al registro de curso matriculado (MatriculaCurso)
    matricula_curso_id = db.Column(db.Integer, db.ForeignKey('matricula_curso_detalle.id', ondelete="CASCADE"), nullable=False)
    matricula_curso = db.relationship("MatriculaCurso", back_populates="calificaciones")
    __table_args__ = (
        CheckConstraint("valor >= 0 AND valor <= 20", name='ck_rango_nota'),
    )

    def __repr__(self):
        return f"<Calificacion matricula={self.matricula_id} nota={self.valor}>"

class Asistencia(db.Model):
    __tablename__ = 'asistencias'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    estado = db.Column(db.String(10), nullable=False)  # 'asistio', 'falta'
    justificada = db.Column(db.Boolean, default=False)
    observacion = db.Column(db.String(255))

    
    # --- Relaciones ---
    # Apunta al registro de curso matriculado (MatriculaCurso)
    matricula_curso_id = db.Column(db.Integer, db.ForeignKey('matricula_curso_detalle.id', ondelete="CASCADE"), nullable=False)
    matricula_curso = db.relationship("MatriculaCurso", back_populates="asistencias")

    __table_args__ = (
        CheckConstraint("estado IN ('asistio','falta','tardanza','justificada')", name='ck_asistencia_estado_valido'),
    )

class SolicitudTramite(db.Model):
    __tablename__ = 'solicitudes_tramite'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Quién lo solicita
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiantes.id'), nullable=False)
    
    # El trámite se solicita por el Módulo (catálogo), no por la oferta
    modulo_id = db.Column(db.Integer, db.ForeignKey('modulos.id'), nullable=True)

    # Detalles de la solicitud
    tipo_tramite = db.Column(db.String(100), nullable=False) # Ej: 'Certificado de Módulo', 'Constancia de Estudios'
    fecha_solicitud = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    estado = db.Column(db.String(30), nullable=False, default='Solicitado') # Solicitado, En Revisión, Aprobado, Rechazado
    
    # Observaciones
    observaciones_estudiante = db.Column(db.Text, nullable=True)
    observaciones_admin = db.Column(db.Text, nullable=True)
    
    # Quién lo gestiona (opcional)
    admin_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    fecha_actualizacion = db.Column(db.DateTime, onupdate=datetime.datetime.utcnow)
    # Archivo resultante (Certificado del modulo)
    ruta_archivo = db.Column(db.String(255), nullable=True)

    # Relaciones
    estudiante = db.relationship('Estudiante', back_populates='tramites')
    modulo = db.relationship('Modulo', back_populates='tramites')
    # admin_id apunta a 'usuario.id', la relación inversa está en Usuario
    administrador_usuario = db.relationship('Usuario', back_populates='tramites_gestionados', foreign_keys=[admin_id])

    def __repr__(self):
        return f"<Tramite {self.id} - {self.tipo_tramite} ({self.estado})>"
