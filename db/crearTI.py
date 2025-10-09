import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Programa, Modulo, Curso

with app.app_context():
    # 1. Crear el programa
    programa = Programa(
        id="J2662-2-002",
        nombre="Plataformas y servicios de tecnologias de la informacion",
        total_creditos=93,
        total_horas=2448
    )
    db.session.add(programa)
    db.session.commit()

    # 2. Modulo 1: Soporte tecnico, redes y conectividad en sistemas de TI
    mod1 = Modulo(
        nombre="Soporte tecnico, redes y conectividad en sistemas de TI",
        programa_id=programa.id,
        periodo_academico="I",
        unidad_competencia="UC1, CE1"
    )
    db.session.add(mod1)
    db.session.commit()

    cursos_mod1 = [
        Curso(
            nombre="Gestion de sistemas operativos",
            horas_teoricas=16,
            horas_practicas=40,
            contenidos="Gestion de sistemas operativos",
            modulo_id=mod1.id
        ),
        Curso(
            nombre="Internet",
            horas_teoricas=16,
            horas_practicas=40,
            contenidos="Internet",
            modulo_id=mod1.id
        ),
        Curso(
            nombre="Procesador de texto",
            horas_teoricas=16,
            horas_practicas=40,
            contenidos="Procesador de texto",
            modulo_id=mod1.id
        ),
        Curso(
            nombre="Presentador Informatico",
            horas_teoricas=16,
            horas_practicas=40,
            contenidos="Presentador Informatico",
            modulo_id=mod1.id
        ),
        Curso(
            nombre="Hojas de calculo",
            horas_teoricas=16,
            horas_practicas=40,
            contenidos="Hojas de calculo",
            modulo_id=mod1.id
        ),
        Curso(
            nombre="Infraestructura y gestion de recursos TI",
            horas_teoricas=16,
            horas_practicas=40,
            contenidos="Infraestructura y gestion de recursos TI",
            modulo_id=mod1.id
        ),
        Curso(
            nombre="Soporte tecnico en infraestructuras TI",
            horas_teoricas=16,
            horas_practicas=40,
            contenidos="Soporte tecnico en infraestructuras TI",
            modulo_id=mod1.id
        ),
        Curso(
            nombre="Arquitectura de sistema de informacion",
            horas_teoricas=16,
            horas_practicas=40,
            contenidos="Arquitectura de sistema de informacion",
            modulo_id=mod1.id
        ),
        Curso(
            nombre="Ingles Basico",
            horas_teoricas=8,
            horas_practicas=8,
            contenidos="Ingles Basico",
            modulo_id=mod1.id
        ),
        Curso(
            nombre="Comunicacion efectiva",
            horas_teoricas=8,
            horas_practicas=8,
            contenidos="Comunicacion efectiva",
            modulo_id=mod1.id
        ),
    ]
    db.session.add_all(cursos_mod1)
    db.session.commit()

    # 3. Modulo 2: Gestion y asistencia en redes de acceso
    mod2 = Modulo(
        nombre="Gestion y asistencia en redes de acceso",
        programa_id=programa.id,
        periodo_academico="II",
        unidad_competencia="UC2, CE2"
    )
    db.session.add(mod2)
    db.session.commit()

    cursos_mod2 = [
        Curso(
            nombre="Requerimientos y Caracteristicas fisicas",
            horas_teoricas=21,
            horas_practicas=42,
            contenidos="Requerimientos y Caracteristicas fisicas",
            modulo_id=mod2.id
        ),
        Curso(
            nombre="Instalacion hardware en redes",
            horas_teoricas=21,
            horas_practicas=42,
            contenidos="Instalacion hardware en redes",
            modulo_id=mod2.id
        ),
        Curso(
            nombre="Operacion de redes",
            horas_teoricas=21,
            horas_practicas=42,
            contenidos="Operacion de redes",
            modulo_id=mod2.id
        ),
        Curso(
            nombre="Instalacion software para redes",
            horas_teoricas=21,
            horas_practicas=42,
            contenidos="Instalacion software para redes",
            modulo_id=mod2.id
        ),
        Curso(
            nombre="Redes inalambricas",
            horas_teoricas=22,
            horas_practicas=44,
            contenidos="Redes inalambricas",
            modulo_id=mod2.id
        ),
        Curso(
            nombre="Mantenimiento de redes",
            horas_teoricas=22,
            horas_practicas=44,
            contenidos="Mantenimiento de redes",
            modulo_id=mod2.id
        ),
        Curso(
            nombre="Ingles Tecnico",
            horas_teoricas=11,
            horas_practicas=11,
            contenidos="Ingles Tecnico",
            modulo_id=mod2.id
        ),
        Curso(
            nombre="Gestion Empresarial",
            horas_teoricas=11,
            horas_practicas=11,
            contenidos="Gestion Empresarial",
            modulo_id=mod2.id
        ),
    ]
    db.session.add_all(cursos_mod2)
    db.session.commit()

    # 4. Modulo 3: Diseño de plataformas de TI y programacion
    mod3 = Modulo(
        nombre="Diseño de plataformas de TI y programacion",
        programa_id=programa.id,
        periodo_academico="III",
        unidad_competencia="UC3, CE4"
    )
    db.session.add(mod3)
    db.session.commit()

    cursos_mod3 = [
        Curso(
            nombre="Programacion orientada a objetos",
            horas_teoricas=24,
            horas_practicas=48,
            contenidos="Programacion orientada a objetos",
            modulo_id=mod3.id
        ),
        Curso(
            nombre="Python",
            horas_teoricas=24,
            horas_practicas=48,
            contenidos="Python",
            modulo_id=mod3.id
        ),
        Curso(
            nombre="Bases de datos (gestion y administracion)",
            horas_teoricas=24,
            horas_practicas=48,
            contenidos="Bases de datos (gestion y administracion)",
            modulo_id=mod3.id
        ),
        Curso(
            nombre="Programas de edicion y reportes",
            horas_teoricas=24,
            horas_practicas=48,
            contenidos="Programas de edicion y reportes",
            modulo_id=mod3.id
        ),
        Curso(
            nombre="Desarrollo de recursos TIC'sistemas",
            horas_teoricas=24,
            horas_practicas=48,
            contenidos="Desarrollo de recursos TIC'sistemas",
            modulo_id=mod3.id
        ),
        Curso(
            nombre="Desarrollo de aplicaciones web",
            horas_teoricas=24,
            horas_practicas=48,
            contenidos="Desarrollo de aplicaciones web",
            modulo_id=mod3.id
        ),
        Curso(
            nombre="Desarrollo de aplicaciones moviles",
            horas_teoricas=24,
            horas_practicas=48,
            contenidos="Desarrollo de aplicaciones moviles",
            modulo_id=mod3.id
        ),
        Curso(
            nombre="Formacion Laboral",
            horas_teoricas=12,
            horas_practicas=12,
            contenidos="Formacion Laboral",
            modulo_id=mod3.id
        ),
    ]
    db.session.add_all(cursos_mod3)
    db.session.commit()

    # 5. Modulo 4: Marketing digital, redes sociales y audiovisuales
    mod4 = Modulo(
        nombre="Marketing digital, redes sociales y audiovisuales",
        programa_id=programa.id,
        periodo_academico="IV",
        unidad_competencia="UC4, CE5, CE6"
    )
    db.session.add(mod4)
    db.session.commit()

    cursos_mod4 = [
        Curso(
            nombre="Diseño grafico",
            horas_teoricas=21,
            horas_practicas=48,
            contenidos="Diseño grafico",
            modulo_id=mod4.id
        ),
        Curso(
            nombre="Edicion de audio y video",
            horas_teoricas=21,
            horas_practicas=48,
            contenidos="Edicion de audio y video",
            modulo_id=mod4.id
        ),
        Curso(
            nombre="Marketing digital",
            horas_teoricas=21,
            horas_practicas=48,
            contenidos="Marketing digital",
            modulo_id=mod4.id
        ),
        Curso(
            nombre="Redes sociales",
            horas_teoricas=21,
            horas_practicas=48,
            contenidos="Redes sociales",
            modulo_id=mod4.id
        ),
        Curso(
            nombre="Seguridad informatica",
            horas_teoricas=22,
            horas_practicas=48,
            contenidos="Seguridad informatica",
            modulo_id=mod4.id
        ),
        Curso(
            nombre="Etica profesional",
            horas_teoricas=11,
            horas_practicas=24,
            contenidos="Etica profesional",
            modulo_id=mod4.id
        ),
        Curso(
            nombre="Emprendimiento",
            horas_teoricas=11,
            horas_practicas=24,
            contenidos="Emprendimiento",
            modulo_id=mod4.id
        ),
    ]
    db.session.add_all(cursos_mod4)
    db.session.commit()

    print("¡Programa TI, módulos y cursos creados exitosamente!")