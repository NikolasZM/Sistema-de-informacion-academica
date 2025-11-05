CREATE TABLE usuario (
    id INTEGER NOT NULL,
    usuario VARCHAR(80) NOT NULL,
    password VARCHAR(200),
    email VARCHAR(120) NOT NULL,
    rol VARCHAR(20) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (usuario),
    UNIQUE (email)
);

CREATE TABLE periodos (
    id INTEGER NOT NULL,
    codigo VARCHAR(20) NOT NULL,
    fecha_inicio DATE,
    fecha_fin DATE,
    estado VARCHAR(20) DEFAULT 'activo',
    PRIMARY KEY (id),
    UNIQUE (codigo)
);

CREATE TABLE programas (
    id VARCHAR(20) NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    total_creditos INTEGER,
    total_horas INTEGER,
    PRIMARY KEY (id)
);

CREATE TABLE salones (
    id INTEGER NOT NULL,
    nombre VARCHAR(50) NOT NULL,
    capacidad INTEGER,
    caracteristicas VARCHAR(200),
    fecha_registro DATE,
    PRIMARY KEY (id)
);

-- =========================
-- Tablas dependientes (Tier 1)
-- =========================

CREATE TABLE docente (
    id INTEGER NOT NULL,
    nombre_completo VARCHAR(120),
    dni VARCHAR(8),
    celular VARCHAR(9),
    correo_personal VARCHAR(120),
    fecha_nacimiento DATE,
    PRIMARY KEY (id),
    FOREIGN KEY(id) REFERENCES usuario (id)
);

CREATE TABLE estudiantes (
    id INTEGER NOT NULL,
    nombre_completo VARCHAR(120) NOT NULL,
    programa_estudio VARCHAR(100) NOT NULL,
    codigo VARCHAR(20) NOT NULL,
    dni VARCHAR(15) NOT NULL,
    sexo VARCHAR(10) NOT NULL,
    fecha_nacimiento DATE,
    PRIMARY KEY (id),
    FOREIGN KEY(id) REFERENCES usuario (id),
    UNIQUE (codigo),
    UNIQUE (dni)
);

CREATE TABLE administradores (
    id INTEGER NOT NULL,
    cargo VARCHAR(80),
    PRIMARY KEY (id),
    FOREIGN KEY(id) REFERENCES usuario (id)
);

CREATE TABLE modulos (
    id INTEGER NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    unidad_competencia VARCHAR(120),
    periodo_id INTEGER NOT NULL,
    programa_id VARCHAR(20) NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(periodo_id) REFERENCES periodos (id) ON DELETE RESTRICT,
    FOREIGN KEY(programa_id) REFERENCES programas (id) ON DELETE RESTRICT
);

-- =========================
-- Tablas dependientes (Tier 2)
-- =========================

CREATE TABLE estudiantes_info (
    estudiante_id INTEGER NOT NULL,
    direccion VARCHAR(200),
    departamento VARCHAR(100),
    provincia VARCHAR(100),
    distrito VARCHAR(100),
    celular VARCHAR(20),
    contacto_nombre VARCHAR(120),
    contacto_parentesco VARCHAR(50),
    contacto_telefono VARCHAR(20),
    contacto_nombre_2 VARCHAR(120),
    contacto_parentesco_2 VARCHAR(50),
    contacto_telefono_2 VARCHAR(20),
    PRIMARY KEY (estudiante_id),
    FOREIGN KEY(estudiante_id) REFERENCES estudiantes (id)
);

CREATE TABLE cursos (
    id INTEGER NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    horas_teoricas INTEGER,
    horas_practicas INTEGER,
    contenidos TEXT,
    sesiones_programadas INTEGER,
    modulo_id INTEGER NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(modulo_id) REFERENCES modulos (id) ON DELETE RESTRICT
);

CREATE TABLE matriculas (
    id INTEGER NOT NULL,
    fecha_matricula DATE NOT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'activa',
    estudiante_id INTEGER NOT NULL,
    modulo_id INTEGER NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(estudiante_id) REFERENCES estudiantes (id) ON DELETE CASCADE,
    FOREIGN KEY(modulo_id) REFERENCES modulos (id) ON DELETE RESTRICT,
    UNIQUE (estudiante_id, modulo_id, fecha_matricula)
);

-- =========================
-- Tablas dependientes (Tier 3)
-- =========================

CREATE TABLE programaciones_clase (
    id INTEGER NOT NULL,
    dia_semana VARCHAR(15) NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    periodo_id INTEGER NOT NULL,
    curso_id INTEGER NOT NULL,
    salon_id INTEGER NOT NULL,
    docente_id INTEGER,
    PRIMARY KEY (id),
    FOREIGN KEY(periodo_id) REFERENCES periodos (id) ON DELETE RESTRICT,
    FOREIGN KEY(curso_id) REFERENCES cursos (id) ON DELETE CASCADE,
    FOREIGN KEY(salon_id) REFERENCES salones (id) ON DELETE RESTRICT,
    FOREIGN KEY(docente_id) REFERENCES docente (id) ON DELETE SET NULL,
    UNIQUE (periodo_id, salon_id, dia_semana, hora_inicio),
    CHECK (hora_fin > hora_inicio)
);

CREATE TABLE calificaciones (
    id INTEGER NOT NULL,
    valor FLOAT NOT NULL,
    indicador_logro VARCHAR(50),
    tipo_evaluacion VARCHAR(50),
    fecha_registro DATE NOT NULL,
    estudiante_id INTEGER NOT NULL,
    curso_id INTEGER NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(estudiante_id) REFERENCES estudiantes (id) ON DELETE CASCADE,
    FOREIGN KEY(curso_id) REFERENCES cursos (id) ON DELETE CASCADE
);

CREATE TABLE asistencias (
    id INTEGER NOT NULL,
    estudiante_id INTEGER NOT NULL,
    curso_id INTEGER NOT NULL,
    fecha DATE NOT NULL,
    estado VARCHAR(10) NOT NULL,
    justificada BOOLEAN DEFAULT FALSE,
    observacion VARCHAR(255),
    PRIMARY KEY (id),
    FOREIGN KEY(estudiante_id) REFERENCES estudiantes (id),
    FOREIGN KEY(curso_id) REFERENCES cursos (id)
);

-- =========================
-- Tablas dependientes (Tier 4)
-- =========================

CREATE TABLE solicitudes_tramite (
    id INTEGER NOT NULL,
    estudiante_id INTEGER NOT NULL,
    modulo_id INTEGER,
    tipo_tramite VARCHAR(100) NOT NULL,
    fecha_solicitud TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(30) NOT NULL DEFAULT 'Solicitado',
    observaciones_estudiante TEXT,
    observaciones_admin TEXT,
    admin_id INTEGER,
    fecha_actualizacion TIMESTAMP,
    ruta_archivo VARCHAR(255),
    PRIMARY KEY (id),
    FOREIGN KEY(estudiante_id) REFERENCES estudiantes (id),
    FOREIGN KEY(modulo_id) REFERENCES modulos (id),
    FOREIGN KEY(admin_id) REFERENCES usuario (id)
);
