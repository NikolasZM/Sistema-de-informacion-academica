import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Salon

with app.app_context():
    salon = Salon(nombre="Aula 101", capacidad=30, caracteristicas="Pizarra")
    db.session.add(salon)
    db.session.commit()