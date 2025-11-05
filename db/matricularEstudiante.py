import sys
import os
import datetime

# Ajustar path para importar app y modelos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import (
    Matricula,
    MatriculaCurso,
    Estudiante,
    ModuloActivo,
    Periodo,
    CursoActivo
)

with app.app_context():
    # 1️⃣ Buscar el periodo activo
    periodo_activo = Periodo.query.filter_by(estado="activo").first()
    if not periodo_activo:
        print("❌ No hay periodo activo. No se puede realizar matrícula.")
        exit()

    print(f"📅 Periodo activo: {periodo_activo.codigo}")

    # 2️⃣ Obtener todos los módulos activos de este periodo
    #modulos_activos = ModuloActivo.query.filter_by(periodo_id=periodo_activo.id).all()
    modulos_activos = ModuloActivo.query.filter_by(periodo_id=periodo_activo.id).limit(2).all()

    if not modulos_activos:
        print("❌ No se encontraron módulos activos para el periodo actual.")
        exit()

    # 3️⃣ Obtener todos los estudiantes
    estudiantes = Estudiante.query.all()
    if not estudiantes:
        print("⚠️ No hay estudiantes en la base de datos.")
        exit()

    total_matriculas = 0
    total_cursos = 0

    for modulo_activo in modulos_activos:
        print(f"\n📘 Procesando módulo: {modulo_activo.modulo.nombre} (ID: {modulo_activo.id})")
        
        # Cursos activos del módulo
        cursos_activos = CursoActivo.query.filter_by(modulo_activo_id=modulo_activo.id).all()
        if not cursos_activos:
            print(f"⚠️ No hay cursos activos en este módulo.")
            continue

        for estudiante in estudiantes:
            # Verificar si ya existe matrícula para este módulo
            matricula_existente = Matricula.query.filter_by(
                estudiante_id=estudiante.id,
                modulo_activo_id=modulo_activo.id
            ).first()

            if matricula_existente:
                print(f"🔹 {estudiante.nombre_completo} ya tiene matrícula en este módulo.")
                matricula = matricula_existente
            else:
                # Crear nueva matrícula
                matricula = Matricula(
                    estudiante_id=estudiante.id,
                    modulo_activo_id=modulo_activo.id,
                    fecha_matricula=datetime.date.today(),
                    estado="activa"
                )
                db.session.add(matricula)
                total_matriculas += 1
                print(f"✅ Matrícula creada para {estudiante.nombre_completo} en módulo '{modulo_activo.modulo.nombre}'")

            # Inscribir cada curso activo en MatriculaCurso
            count_cursos = 0
            for curso_activo in cursos_activos:
                curso_inscrito = MatriculaCurso.query.filter_by(
                    matricula_id=matricula.id,
                    curso_activo_id=curso_activo.id
                ).first()

                if not curso_inscrito:
                    detalle_curso = MatriculaCurso(
                        matricula_id=matricula.id,
                        curso_activo_id=curso_activo.id
                    )
                    db.session.add(detalle_curso)
                    count_cursos += 1
                    total_cursos += 1

            if count_cursos > 0:
                print(f"   🎓 {count_cursos} cursos inscritos para {estudiante.nombre_completo}")
            else:
                print(f"   ⚠️ Todos los cursos ya estaban inscritos para {estudiante.nombre_completo}")

    db.session.commit()
    print("\n🎉 Proceso completado con éxito!")
    print(f"Total de matrículas creadas: {total_matriculas}")
    print(f"Total de cursos inscritos: {total_cursos}")
