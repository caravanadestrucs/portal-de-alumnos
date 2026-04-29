"""
Script para recrear la base de datos con las nuevas restricciones de clave foránea
Ejecutar: python migrate_cascade.py
"""
from app import app, db
from models import (
    Admin, Carrera, Materia, Alumno, Calificacion, 
    PracticaProfesional, NotaRemision, Profesor, 
    Grupo, GrupoIntegrante, Asignacion
)

with app.app_context():
    print('Eliminando tablas existentes...')
    db.drop_all()
    
    print('Creando tablas con restricciones en cascada...')
    db.create_all()
    
    print('✅ Base de datos recreada con éxito')
    print('⚠️  Nota: Se perderán todos los datos existentes')
    print('   Para mantener datos, hacer un respaldo antes de ejecutar')
