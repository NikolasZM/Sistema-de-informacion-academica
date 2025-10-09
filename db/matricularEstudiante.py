import sys
import os
import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Matricula, Estudiante, Modulo

with app.app_context():
    modulo = Modulo.query.first()  # O el módulo que desees
    estudiantes = Estudiante.query.all()
    for est in estudiantes:
        existe = Matricula.query.filter_by(estudiante_id=est.id, modulo_id=modulo.id).first()
        if not existe:
            m = Matricula(
                estudiante_id=est.id,
                modulo_id=modulo.id,
                fecha_matricula=datetime.date.today(),
                estado="activa"
            )
            db.session.add(m)
    db.session.commit()
    print(f"¡Estudiantes matriculados en el módulo '{modulo.nombre}'!")