import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Programa, Modulo, Curso

with app.app_context():
    # 1. Crear el programa
    programa = Programa(
        id="S3496-2-001",
        nombre="Estilismo",
        total_creditos=84,
        total_horas=2240
    )
    db.session.add(programa)
    db.session.commit()

    # 2. Modulo 1: Cortes Cabello, Barberia y Peinados
    mod1 = Modulo(
        nombre="Cortes Cabello, Barberia y Peinados",
        programa_id=programa.id,
        periodo_academico="I",
        unidad_competencia="UC1, CE1"
        
    )
    db.session.add(mod1)
    db.session.commit()

    # Cursos (unidades didácticas) del Módulo 1
    cursos_mod1 = [
        Curso(
            nombre="Cortes de cabello",
            horas_teoricas=24,
            horas_practicas=72,
            contenidos="Cortes de cabello",
            modulo_id=mod1.id
        ),
        Curso(
            nombre="Barberia",
            horas_teoricas=24,
            horas_practicas=72,
            contenidos="Barberia",
            modulo_id=mod1.id
        ),
        Curso(
            nombre="Trenzas y recogidos",
            horas_teoricas=24,
            horas_practicas=72,
            contenidos="Trenzas y recogidos",
            modulo_id=mod1.id
        ),
        Curso(
            nombre="Peinados",
            horas_teoricas=24,
            horas_practicas=72,
            contenidos="Peinados",
            modulo_id=mod1.id
        ),
        Curso(
            nombre="Inglés Básico",
            horas_teoricas=12,
            horas_practicas=12,
            contenidos="Inglés Básico",
            modulo_id=mod1.id
        ),
        Curso(
            nombre="Comunicación Efectiva",
            horas_teoricas=12,
            horas_practicas=12,
            contenidos="Comunicación Efectiva",
            modulo_id=mod1.id
        ),
    ]
    db.session.add_all(cursos_mod1)
    db.session.commit()

    # 3. Modulo 2: Ondulaciones y colorimetría
    mod2 = Modulo(
        nombre="Ondulaciones y colorimetría",
        programa_id=programa.id,
        periodo_academico="II", 
        unidad_competencia="UC2, CE2"
    )
    db.session.add(mod2)
    db.session.commit()

    cursos_mod2 = [
        Curso(
            nombre="Permanentes",
            horas_teoricas=22,
            horas_practicas=44,
            contenidos="Permanentes",
            modulo_id=mod2.id
        ),
        Curso(
            nombre="Ondulaciones y frisados",
            horas_teoricas=22,
            horas_practicas=44,
            contenidos="Ondulaciones y frisados",
            modulo_id=mod2.id
        ),
        Curso(
            nombre="Principios de colorimetría y técnicas de decoloración",
            horas_teoricas=22,
            horas_practicas=44,
            contenidos="Principios de colorimetría y técnicas de decoloración",
            modulo_id=mod2.id
        ),
        Curso(
            nombre="Tinturación capilar",
            horas_teoricas=23,
            horas_practicas=46,
            contenidos="Tinturación capilar",
            modulo_id=mod2.id
        ),
        Curso(
            nombre="Mechas tricolores",
            horas_teoricas=23,
            horas_practicas=46,
            contenidos="Mechas tricolores",
            modulo_id=mod2.id
        ),
        Curso(
            nombre="Inglés Técnico",
            horas_teoricas=11,
            horas_practicas=11,
            contenidos="Inglés Técnico",
            modulo_id=mod2.id
        ),
        Curso(
            nombre="Gestión Empresarial",
            horas_teoricas=11,
            horas_practicas=11,
            contenidos="Gestión Empresarial",
            modulo_id=mod2.id
        ),
    ]
    db.session.add_all(cursos_mod2)
    db.session.commit()

    # 4. Modulo 3: Depilaciones y maquillajes
    mod3 = Modulo(
        nombre="Depilaciones y maquillajes",
        programa_id=programa.id,
        periodo_academico="III",
        unidad_competencia="UC3, CE3, CE4"
    )
    db.session.add(mod3)
    db.session.commit()

    cursos_mod3 = [
        Curso(
            nombre="Blanqueamiento a la piel",
            horas_teoricas=28,
            horas_practicas=64,
            contenidos="Blanqueamiento a la piel",
            modulo_id=mod3.id
        ),
        Curso(
            nombre="Depilaciones de raíz y de cera",
            horas_teoricas=28,
            horas_practicas=64,
            contenidos="Depilaciones de raíz y de cera",
            modulo_id=mod3.id
        ),
        Curso(
            nombre="Cremas depiladoras y depilaciones láser",
            horas_teoricas=28,
            horas_practicas=64,
            contenidos="Cremas depiladoras y depilaciones láser",
            modulo_id=mod3.id
        ),
        Curso(
            nombre="Maquillaje con estilo moderno",
            horas_teoricas=28,
            horas_practicas=64,
            contenidos="Maquillaje con estilo moderno",
            modulo_id=mod3.id
        ),
        Curso(
            nombre="Habilidades informáticas",
            horas_teoricas=14,
            horas_practicas=14,
            contenidos="Habilidades informáticas",
            modulo_id=mod3.id
        ),
        Curso(
            nombre="Formación laboral",
            horas_teoricas=14,
            horas_practicas=14,
            contenidos="Formación laboral",
            modulo_id=mod3.id
        ),
    ]
    db.session.add_all(cursos_mod3)
    db.session.commit()

    # 5. Modulo 4: Tratamiento facial, Maquillaje de caracterización, Manicure y Pedicure
    mod4 = Modulo(
        nombre="Tratamiento facial, Maquillaje de caracterización, Manicure y Pedicure",
        programa_id=programa.id,
        periodo_academico="IV",
        unidad_competencia="UC4, CE5, CE6"
    )
    db.session.add(mod4)
    db.session.commit()

    cursos_mod4 = [
        Curso(
            nombre="Limpieza de cutis y tratamientos faciales",
            horas_teoricas=32,
            horas_practicas=64,
            contenidos="Limpieza de cutis y tratamientos faciales",
            modulo_id=mod4.id
        ),
        Curso(
            nombre="Mascarillas y microdermoabrasión",
            horas_teoricas=32,
            horas_practicas=64,
            contenidos="Mascarillas y microdermoabrasión",
            modulo_id=mod4.id
        ),
        Curso(
            nombre="Maquillaje artístico de caracterización",
            horas_teoricas=32,
            horas_practicas=64,
            contenidos="Maquillaje artístico de caracterización",
            modulo_id=mod4.id
        ),
        Curso(
            nombre="Uñas naturales o acrílicas",
            horas_teoricas=32,
            horas_practicas=64,
            contenidos="Uñas naturales o acrílicas",
            modulo_id=mod4.id
        ),
        Curso(
            nombre="Diseño de uñas",
            horas_teoricas=32,
            horas_practicas=64,
            contenidos="Diseño de uñas",
            modulo_id=mod4.id
        ),
        Curso(
            nombre="Pedicura aplicado a la podología",
            horas_teoricas=32,
            horas_practicas=64,
            contenidos="Pedicura aplicado a la podología",
            modulo_id=mod4.id
        ),
        Curso(
            nombre="Ética Profesional",
            horas_teoricas=16,
            horas_practicas=16,
            contenidos="Ética Profesional",
            modulo_id=mod4.id
        ),
        Curso(
            nombre="Emprendimiento",
            horas_teoricas=16,
            horas_practicas=16,
            contenidos="Emprendimiento",
            modulo_id=mod4.id
        ),
    ]
    db.session.add_all(cursos_mod4)
    db.session.commit()


    print("¡Programa Estilismo, módulos y cursos creados exitosamente!")