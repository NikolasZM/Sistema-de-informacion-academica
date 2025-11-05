# crear_periodos_y_programas_CORREGIDO.py
import sys
import os
import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Programa, Modulo, Curso, Periodo

def crear_periodos_academicos():
    """Crear los periodos académicos necesarios"""
    print("📅 Creando periodos académicos...")

    if Periodo.query.count() > 0:
        print("✅ Periodos académicos ya existen")
        return

    periodos = [
        Periodo(codigo="2025-I", fecha_inicio=datetime.date(2025, 1, 1), fecha_fin=datetime.date(2025, 6, 30), estado="activo"),
        Periodo(codigo="2025-II", fecha_inicio=datetime.date(2025, 7, 1), fecha_fin=datetime.date(2025, 12, 31), estado="planificado"),
        Periodo(codigo="2026-I", fecha_inicio=datetime.date(2026, 1, 1), fecha_fin=datetime.date(2026, 6, 30), estado="planificado"),
        Periodo(codigo="2026-II", fecha_inicio=datetime.date(2026, 7, 1), fecha_fin=datetime.date(2026, 12, 31), estado="planificado")
    ]

    db.session.add_all(periodos)
    db.session.commit()
    print("✅ Periodos académicos creados")


def crear_estilismo():
    """Crear programa de Estilismo"""
    print("💇 Creando programa Estilismo...")

    if Programa.query.filter_by(id="S3496-2-001").first():
        print("✅ Programa Estilismo ya existe")
        return

    programa = Programa(
        id="S3496-2-001",
        nombre="Estilismo",
        total_creditos=84,
        total_horas=2240
    )
    db.session.add(programa)
    db.session.commit()
    print("   ✅ Programa creado")

    # Módulos y cursos definidos en listas para facilidad
    modulos = [
        {
            "nombre": "Cortes Cabello, Barberia y Peinados",
            "unidad": "UC1, CE1",
            "cursos": [
                {"nombre": "Cortes de cabello", "ht":24, "hp":72},
                {"nombre": "Barberia", "ht":24, "hp":72},
                {"nombre": "Trenzas y recogidos", "ht":24, "hp":72},
                {"nombre": "Peinados", "ht":24, "hp":72},
                {"nombre": "Inglés Básico", "ht":12, "hp":12},
                {"nombre": "Comunicación Efectiva", "ht":12, "hp":12},
            ]
        },
        {
            "nombre": "Ondulaciones y colorimetría",
            "unidad": "UC2, CE2",
            "cursos": [
                {"nombre": "Permanentes", "ht":22, "hp":44},
                {"nombre": "Ondulaciones y frisados", "ht":22, "hp":44},
                {"nombre": "Principios de colorimetría y técnicas de decoloración", "ht":22, "hp":44},
                {"nombre": "Tinturación capilar", "ht":23, "hp":46},
                {"nombre": "Mechas tricolores", "ht":23, "hp":46},
                {"nombre": "Inglés Técnico", "ht":11, "hp":11},
                {"nombre": "Gestión Empresarial", "ht":11, "hp":11},
            ]
        },
        {
            "nombre": "Depilaciones y maquillajes",
            "unidad": "UC3, CE3, CE4",
            "cursos": [
                {"nombre": "Blanqueamiento a la piel", "ht":28, "hp":64},
                {"nombre": "Depilaciones de raíz y de cera", "ht":28, "hp":64},
                {"nombre": "Cremas depiladoras y depilaciones láser", "ht":28, "hp":64},
                {"nombre": "Maquillaje con estilo moderno", "ht":28, "hp":64},
                {"nombre": "Habilidades informáticas", "ht":14, "hp":14},
                {"nombre": "Formación laboral", "ht":14, "hp":14},
            ]
        },
        {
            "nombre": "Tratamiento facial, Maquillaje de caracterización, Manicure y Pedicure",
            "unidad": "UC4, CE5, CE6",
            "cursos": [
                {"nombre": "Limpieza de cutis y tratamientos faciales", "ht":32, "hp":64},
                {"nombre": "Mascarillas y microdermoabrasión", "ht":32, "hp":64},
                {"nombre": "Maquillaje artístico de caracterización", "ht":32, "hp":64},
                {"nombre": "Uñas naturales o acrílicas", "ht":32, "hp":64},
                {"nombre": "Diseño de uñas", "ht":32, "hp":64},
                {"nombre": "Pedicura aplicado a la podología", "ht":32, "hp":64},
                {"nombre": "Ética Profesional", "ht":16, "hp":16},
                {"nombre": "Emprendimiento", "ht":16, "hp":16},
            ]
        }
    ]

    for mod in modulos:
        modulo = Modulo(nombre=mod["nombre"], programa_id=programa.id, unidad_competencia=mod["unidad"])
        db.session.add(modulo)
        db.session.commit()
        print(f"   ✅ Módulo '{mod['nombre']}' creado")
        cursos = [
            Curso(sesiones_programadas=30, nombre=c["nombre"], horas_teoricas=c["ht"], horas_practicas=c["hp"], contenidos=c["nombre"], modulo_id=modulo.id)
            for c in mod["cursos"]
        ]
        db.session.add_all(cursos)
        db.session.commit()
        print(f"   ✅ Cursos del módulo '{mod['nombre']}' creados")

    print("✅ Programa Estilismo creado exitosamente!")


def crear_ti():
    """Crear programa de TI"""
    print("💻 Creando programa TI...")

    if Programa.query.filter_by(id="J2662-2-002").first():
        print("✅ Programa TI ya existe")
        return

    programa = Programa(
        id="J2662-2-002",
        nombre="Plataformas y servicios de tecnologias de la informacion",
        total_creditos=93,
        total_horas=2448
    )
    db.session.add(programa)
    db.session.commit()
    print("   ✅ Programa TI creado")

    modulos = [
        {
            "nombre": "Soporte tecnico, redes y conectividad en sistemas de TI",
            "unidad": "UC1, CE1",
            "cursos": [
                {"nombre":"Gestion de sistemas operativos","ht":16,"hp":40},
                {"nombre":"Internet","ht":16,"hp":40},
                {"nombre":"Procesador de texto","ht":16,"hp":40},
                {"nombre":"Presentador Informatico","ht":16,"hp":40},
                {"nombre":"Hojas de calculo","ht":16,"hp":40},
                {"nombre":"Infraestructura y gestion de recursos TI","ht":16,"hp":40},
                {"nombre":"Soporte tecnico en infraestructuras TI","ht":16,"hp":40},
                {"nombre":"Arquitectura de sistema de informacion","ht":16,"hp":40},
                {"nombre":"Ingles Basico","ht":8,"hp":8},
                {"nombre":"Comunicacion efectiva","ht":8,"hp":8},
            ]
        },
        {
            "nombre":"Gestion y asistencia en redes de acceso",
            "unidad":"UC2, CE2",
            "cursos":[
                {"nombre":"Requerimientos y Caracteristicas fisicas","ht":21,"hp":42},
                {"nombre":"Instalacion hardware en redes","ht":21,"hp":42},
                {"nombre":"Operacion de redes","ht":21,"hp":42},
                {"nombre":"Instalacion software para redes","ht":21,"hp":42},
                {"nombre":"Redes inalambricas","ht":22,"hp":44},
                {"nombre":"Mantenimiento de redes","ht":22,"hp":44},
                {"nombre":"Ingles Tecnico","ht":11,"hp":11},
                {"nombre":"Gestion Empresarial","ht":11,"hp":11},
            ]
        },
        {
            "nombre":"Diseño de plataformas de TI y programacion",
            "unidad":"UC3, CE4",
            "cursos":[
                {"nombre":"Programacion orientada a objetos","ht":24,"hp":48},
                {"nombre":"Python","ht":24,"hp":48},
                {"nombre":"Bases de datos (gestion y administracion)","ht":24,"hp":48},
                {"nombre":"Programas de edicion y reportes","ht":24,"hp":48},
                {"nombre":"Desarrollo de recursos TIC'sistemas","ht":24,"hp":48},
                {"nombre":"Desarrollo de aplicaciones web","ht":24,"hp":48},
                {"nombre":"Desarrollo de aplicaciones moviles","ht":24,"hp":48},
                {"nombre":"Formacion Laboral","ht":12,"hp":12},
            ]
        },
        {
            "nombre":"Marketing digital, redes sociales y audiovisuales",
            "unidad":"UC4, CE5, CE6",
            "cursos":[
                {"nombre":"Diseño grafico","ht":21,"hp":48},
                {"nombre":"Edicion de audio y video","ht":21,"hp":48},
                {"nombre":"Marketing digital","ht":21,"hp":48},
                {"nombre":"Redes sociales","ht":21,"hp":48},
                {"nombre":"Seguridad informatica","ht":22,"hp":48},
                {"nombre":"Etica profesional","ht":11,"hp":24},
                {"nombre":"Emprendimiento","ht":11,"hp":24},
            ]
        }
    ]

    for mod in modulos:
        modulo = Modulo(nombre=mod["nombre"], programa_id=programa.id, unidad_competencia=mod["unidad"])
        db.session.add(modulo)
        db.session.commit()
        print(f"   ✅ Módulo '{mod['nombre']}' creado")
        cursos = [
            Curso(sesiones_programadas=30, nombre=c["nombre"], horas_teoricas=c["ht"], horas_practicas=c["hp"], contenidos=c["nombre"], modulo_id=modulo.id)
            for c in mod["cursos"]
        ]
        db.session.add_all(cursos)
        db.session.commit()
        print(f"   ✅ Cursos del módulo '{mod['nombre']}' creados")

    print("✅ Programa TI creado exitosamente!")


if __name__ == "__main__":
    with app.app_context():
        try:
            crear_periodos_academicos()
            crear_estilismo()
            crear_ti()
            print("\n🎉 ¡Periodos y programas creados exitosamente!")
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()
