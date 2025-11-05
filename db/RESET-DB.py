# reset_database.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db

with app.app_context():
    # Eliminar todas las tablas
    db.drop_all()
    print("🗑️  Tablas eliminadas")
    
    # Crear todas las tablas nuevamente
    db.create_all()
    print("✅ Tablas recreadas")