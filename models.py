from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint, CheckConstraint
import datetime
db = SQLAlchemy()

# =========================
# Ya existentes en tu archivo
# =========================

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    usuario = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=True) # Puede ser falso si solo se usa Google
    email = db.Column(db.String(120), unique=True, nullable = False)
    rol = db.Column(db.String(20), nullable=False) # 'administrador', 'docente, 'estudiante'

    # Relación con Estudiante
    estudiante = db.relationship("Estudiante", back_populates="usuario", uselist=False)
    docente = db.relationship("Docente", back_populates="usuario", uselist=False)



class Docente(db.Model):
    __tablename__ = "docente"  # opcional, explícito
    id = db.Column(db.Integer, db.ForeignKey('usuario.id'), primary_key=True)
    nombre_completo = db.Column(db.String(120))
    dni = db.Column(db.String(6))
    celular = db.Column(db.String(9))
    correo_personal = db.Column(db.String(120))
    fecha_nacimiento = db.Column(db.Date)
    
    # Mantén UNA sola relación hacia Usuario; usamos back_populates
    usuario = db.relationship('Usuario', back_populates='docente', uselist=False)


# Tabla principal con campos obligatorios
class Estudiante(db.Model):
    __tablename__ = "estudiantes"

    id = db.Column(db.Integer, db.ForeignKey("usuario.id"), primary_key=True)
    nombre_completo = db.Column(db.String(120), nullable=False)
    programa_estudio = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    dni = db.Column(db.String(15), unique=True, nullable=False)
    sexo = db.Column(db.String(10), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=True)
    
    # Relación con Usuario y EstudianteInfo
    usuario = db.relationship("Usuario", back_populates="estudiante",  uselist=False)
    info = db.relationship("EstudianteInfo", back_populates="estudiante", uselist=False)

    # NUEVO 
    matriculas = db.relationship("Matricula", back_populates="estudiante")
    calificaciones = db.relationship("Calificacion", back_populates="estudiante")

    def __repr__(self):
        return f"<Estudiante {self.nombre_completo}>"

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
    """
    Extiende a Usuario (1 a 1). Permite guardar datos extra del administrador.
    Nota: el rol 'administrador' sigue viviendo en Usuario. Esta tabla es opcional
    pero respeta el diagrama.
    """
    __tablename__ = "administradores"

    id = db.Column(db.Integer, db.ForeignKey("usuario.id"), primary_key=True)
    cargo = db.Column(db.String(80), nullable=True)

    usuario = db.relationship("Usuario", backref=db.backref("administrador", uselist=False))
    def __reduce__(self):
        return f"<Administrador {self.id}>"

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

    def __repr__(self):
        return f"<Programa {self.id} - {self.nombre}>"


class Modulo(db.Model):
    __tablename__ = "modulos"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    unidad_competencia = db.Column(db.String(120), nullable=True)
    periodo_academico = db.Column(db.String(50), nullable=True)

    # FK al Programa (composición en el diagrama)
    programa_id = db.Column(db.String(20), db.ForeignKey("programas.id", ondelete="RESTRICT"), nullable=False)
    programa = db.relationship("Programa", back_populates="modulos")

    # Relación: Módulo -> Cursos (1 a N)
    cursos = db.relationship(
        "Curso",
        back_populates="modulo",
        cascade="all, delete-orphan",
        lazy=True,
    )

    # Relación: Módulo -> Matrículas (1 a N)
    matriculas = db.relationship(
        "Matricula",
        back_populates="modulo",
        cascade="all, delete-orphan",
        lazy=True,
    )

    def __repr__(self):
        return f"<Modulo {self.id} - {self.nombre}>"


class Curso(db.Model):
    __tablename__ = "cursos"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    horas_teoricas = db.Column(db.Integer, nullable=True)
    horas_practicas = db.Column(db.Integer, nullable=True)
    contenidos = db.Column(db.Text, nullable=True)

    # FK al Módulo (composición en el diagrama)
    modulo_id = db.Column(db.Integer, db.ForeignKey("modulos.id", ondelete="RESTRICT"), nullable=False)
    modulo = db.relationship("Modulo", back_populates="cursos")

    # Relación: Curso -> Programaciones de clase (1 a N)
    programaciones = db.relationship(
        "ProgramacionClase",
        back_populates="curso",
        cascade="all, delete-orphan",
        lazy=True,
    )

    # Relación: Curso -> Calificaciones (1 a N)
    calificaciones = db.relationship(
        "Calificacion",
        back_populates="curso",
        cascade="all, delete-orphan",
        lazy=True,
    )

    def __repr__(self):
        return f"<Curso {self.id} - {self.nombre}>"


class Salon(db.Model):
    __tablename__ = "salones"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    capacidad = db.Column(db.Integer, nullable=True)
    caracteristicas = db.Column(db.String(200), nullable=True)
    fecha_registro = db.Column(db.Date, nullable=True)

    programaciones = db.relationship(
        "ProgramacionClase",
        back_populates="salon",
        cascade="all, delete-orphan",
        lazy=True,
    )

    def __repr__(self):
        return f"<Salon {self.nombre}>"


class ProgramacionClase(db.Model):
    __tablename__ = "programaciones_clase"
    id = db.Column(db.Integer, primary_key=True)
    dia_semana = db.Column(db.String(15), nullable=False)  # 'Lunes'...'Domingo'
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    periodo_academico = db.Column(db.String(50), nullable=False)

    # FKs
    curso_id = db.Column(db.Integer, db.ForeignKey("cursos.id", ondelete="CASCADE"), nullable=False)
    salon_id = db.Column(db.Integer, db.ForeignKey("salones.id", ondelete="RESTRICT"), nullable=False)
    docente_id = db.Column(db.Integer, db.ForeignKey("docente.id", ondelete="SET NULL"), nullable=True)

    # Relaciones
    curso = db.relationship("Curso", back_populates="programaciones")
    salon = db.relationship("Salon", back_populates="programaciones")
    docente = db.relationship("Docente", backref=db.backref("programaciones", lazy=True))

    __table_args__ = (
        # Evitar duplicar el mismo bloque horario en el mismo salón y período
        UniqueConstraint('salon_id', 'dia_semana', 'hora_inicio', 'hora_fin', 'periodo_academico',
                         name='uq_salon_horario_periodo'),
        CheckConstraint('hora_fin > hora_inicio', name='ck_hora_fin_gt_inicio'),
    )

    def __repr__(self):
        return f"<ProgClase curso={self.curso_id} {self.dia_semana} {self.hora_inicio}-{self.hora_fin}>"


class Matricula(db.Model):
    __tablename__ = "matriculas"
    id = db.Column(db.Integer, primary_key=True)
    fecha_matricula = db.Column(db.Date, nullable=False)
    estado = db.Column(db.String(30), nullable=False, default="activa")  # activa | anulada | suspendida

    # FKs
    estudiante_id = db.Column(db.Integer, db.ForeignKey("estudiantes.id", ondelete="CASCADE"), nullable=False)
    modulo_id = db.Column(db.Integer, db.ForeignKey("modulos.id", ondelete="RESTRICT"), nullable=False)

    modulo_activo_id = db.Column(db.Integer, db.ForeignKey("modulos_activos.id", ondelete="SET NULL"), nullable=True)


    # Relaciones (usar back_populates para coincidir con Estudiante.matriculas)
    estudiante = db.relationship("Estudiante", back_populates="matriculas", lazy=True)
    modulo = db.relationship("Modulo", back_populates="matriculas")
    modulo_activo = db.relationship("ModuloActivo", backref=db.backref("matriculas", lazy=True))


    __table_args__ = (
        UniqueConstraint('estudiante_id', 'modulo_id', 'fecha_matricula', name='uq_matricula_est_mod_fecha'),
    )


class Calificacion(db.Model):
    __tablename__ = "calificaciones"
    id = db.Column(db.Integer, primary_key=True)
    valor = db.Column(db.Float, nullable=False)
    indicador_logro = db.Column(db.String(50), nullable=True)
    tipo_evaluacion = db.Column(db.String(50), nullable=True)
    fecha_registro = db.Column(db.Date, nullable=False)

    estudiante_id = db.Column(db.Integer, db.ForeignKey("estudiantes.id", ondelete="CASCADE"), nullable=False)
    curso_id = db.Column(db.Integer, db.ForeignKey("cursos.id", ondelete="CASCADE"), nullable=False)

    estudiante = db.relationship("Estudiante", back_populates="calificaciones", lazy=True)
    curso = db.relationship("Curso", back_populates="calificaciones")

    def __repr__(self):
        return f"<Calificacion est={self.estudiante_id} curso={self.curso_id} nota={self.valor}>"


class Asistencia(db.Model):
    __tablename__ = 'asistencias'
    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiantes.id'), nullable=False)
    curso_id = db.Column(db.Integer, db.ForeignKey('cursos.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    estado = db.Column(db.String(10), nullable=False)  # 'asistio', 'falta'
    justificada = db.Column(db.Boolean, default=False)
    observacion = db.Column(db.String(255))

class ModuloActivo(db.Model):
    __tablename__ = "modulos_activos"

    id = db.Column(db.Integer, primary_key=True)
    programa_id = db.Column(db.String(20), db.ForeignKey("programas.id", ondelete="RESTRICT"), nullable=False)
    modulo_id = db.Column(db.Integer, db.ForeignKey("modulos.id", ondelete="RESTRICT"), nullable=False)

    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    estado = db.Column(db.String(20), nullable=False, default="activo")  # activo | finalizado | suspendido
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Relaciones
    programa = db.relationship("Programa", backref=db.backref("modulos_activos", lazy=True))
    modulo = db.relationship("Modulo", backref=db.backref("ofertas", lazy=True))

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
    docente_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)

    # Relaciones ORM
    modulo_activo = db.relationship('ModuloActivo', backref=db.backref('cursos_activos', lazy=True))
    curso = db.relationship('Curso', backref=db.backref('cursos_activos', lazy=True))
    docente = db.relationship('Usuario', backref=db.backref('cursos_asignados', lazy=True))

    def __repr__(self):
        return f"<CursoActivo {self.id} - curso {self.curso_id} en ModuloActivo {self.modulo_activo_id}>"