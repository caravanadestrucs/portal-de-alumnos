"""
Importa carreras y materias desde los planes de estudio en PDF
"""
import re
from app import app
from models import db, Carrera, Materia

def import_to_db():
    """Importa todas las carreras y materias a la base de datos"""
    
    # Planes hardcodeados (extraidos manualmente de los PDFs)
    planes = [
        {
            'nombre': 'Ingeniería en Sistemas Computacionales',
            'codigo': 'ISC',
            'materias': [
                (1, 'Álgebra'), (1, 'Cálculo Diferencial'), (1, 'Geometría Analítica'), (1, 'Física'), 
                (1, 'Algoritmos y Estructura de Datos'), (1, 'Estructuras Discretas'), (1, 'Comunicación Oral y Escrita'),
                (1, 'Electrónica'), (1, 'Computación para Ingenieros'), (1, 'Microcomputadoras'),
                (2, 'Álgebra Lineal'), (2, 'Cálculo Integral'), (2, 'Cálculo Vectorial'), (2, 'Diseño de Sistemas Digitales'),
                (2, 'Sistemas Operativos'), (2, 'Seguridad Computacional'), (2, 'Probabilidad y Estadística'),
                (2, 'Análisis de Sistema y Señales'), (2, 'Tecnología Multimedia'), (2, 'Compiladores'),
                (3, 'Ecuaciones Diferenciales'), (3, 'Matemáticas Discretas'), (3, 'Lenguajes Formales y Autómatas'),
                (3, 'Teoría de la Computación'), (3, 'Administración de Redes'), (3, 'Sistemas de Comunicaciones'),
                (3, 'Arquitectura de Computadoras'), (3, 'Derecho Informático'), (3, 'Innovación Tecnológica'), (3, 'Seminario de Tesis I'),
                (4, 'Análisis de Circuitos Eléctricos'), (4, 'Ingeniería de Software'), (4, 'Bases de Datos'),
                (4, 'Sistemas de Calidad'), (4, 'Inteligencia Artificial'), (4, 'Desarrollo de Emprendedores'),
                (4, 'Fundamentos de Redes'), (4, 'Estructura y Programación de Computadoras'), (4, 'Seminario de Tesis II'),
                (5, 'Redes'), (5, 'Ética'), (5, 'Administración de Proyectos de Software'), (5, 'Gratificación por Computadora'),
                (6, 'Organización Industrial'), (6, 'Taller de Investigación I'),
                (7, 'Taller de Investigación II'),
            ]
        },
        {
            'nombre': 'Licenciatura en Contaduría',
            'codigo': 'LC',
            'materias': [
                (1, 'Contabilidad I'), (1, 'Administración'), (1, 'Informática'), (1, 'Ética'),
                (2, 'Contabilidad II'), (2, 'Estadística I'), (2, 'Macroeconomía'), (2, 'Microeconomía'),
                (3, 'Contabilidad III'), (3, 'Administración de Recursos Humanos I'), (3, 'Diagnóstico de Mercados'), (3, 'Derecho Laboral'),
                (4, 'Contabilidad IV'), (4, 'Administración de Recursos Humanos II'), (4, 'Adquisiciones y Abastecimientos'), (4, 'Interpretación de Estados Financieros'),
                (5, 'Contabilidad V'), (5, 'Auditoría I'), (5, 'Contabilidad Gubernamental I'), (5, 'Seguridad Social'),
                (6, 'Auditoría II'), (6, 'Contabilidad Gubernamental II'), (6, 'Desarrollo de Emprendedores'),
                (7, 'Auditoría Interna'),
            ]
        },
        {
            'nombre': 'Licenciatura en Derecho',
            'codigo': 'LD',
            'materias': [
                (1, 'Introducción al Estudio del Derecho'), (1, 'Derecho Civil I'), (1, 'Derecho Penal I'), (1, 'Historia del Derecho'),
                (2, 'Derecho Civil II'), (2, 'Derecho Penal II'), (2, 'Derecho Mercantil I'),
                (3, 'Derecho Civil III'), (3, 'Derecho Mercantil II'), (3, 'Derecho Familiar'),
                (4, 'Derecho del Comercio Exterior'), (4, 'Amparo I'), (4, 'Derecho Fiscal I'),
                (5, 'Amparo II'), (5, 'Derecho Fiscal II'), (5, 'Derecho Mercantil III'),
                (6, 'Derecho Notarial'), (6, 'Juicios Orales'),
                (7, 'Seminario de Tesis I'), (7, 'Seminario de Tesis II'),
            ]
        },
        {
            'nombre': 'Licenciatura en Pedagogía',
            'codigo': 'LP',
            'materias': [
                (1, 'Introducción a la Pedagogía'), (1, 'Historia de la Educación'), (1, 'Filosofía de la Educación'),
                (2, 'Didáctica General'), (2, 'Psicología del Desarrollo'), (2, 'Sociología de la Educación'),
                (3, 'Diseño Curricular'), (3, 'Evaluación Educativa'), (3, 'Tecnología Educativa'),
                (4, 'Planeación Didáctica'), (4, 'Métodos de Investigación'),
                (5, 'Práctica Docente I'),
                (6, 'Práctica Docente II'), (6, 'Seminario de Tesis'),
            ]
        },
        {
            'nombre': 'Licenciatura en Psicología',
            'codigo': 'LPS',
            'materias': [
                (1, 'Introducción a la Psicología'), (1, 'Psicología General'), (1, 'Biología General'),
                (2, 'Psicología del Desarrollo'), (2, 'Psicología Social'), (2, 'Estadística Aplicada'),
                (3, 'Psicología Clínica'), (3, 'Psicología Educativa'), (3, 'Psicología Organizacional'),
                (4, 'Evaluación Psicológica'), (4, 'Técnicas de Intervención'), (4, 'Métodos de Investigación'),
                (5, 'Práctica Profesional I'),
                (6, 'Práctica Profesional II'), (6, 'Seminario de Tesis'),
            ]
        },
        {
            'nombre': 'Licenciatura en Ciencias del Deporte',
            'codigo': 'LCD',
            'materias': [
                (1, 'Anatomía Humana'), (1, 'Fisiología del Ejercicio'), (1, 'Biomecánica'),
                (2, 'Entrenamiento Deportivo I'), (2, 'Nutrición Deportiva'), (2, 'Psicología del Deporte'),
                (3, 'Entrenamiento Deportivo II'), (3, 'Evaluación Funcional'), (3, 'Primeros Auxilios'),
                (4, 'Administración Deportivo'), (4, 'Metodología de la Investigación'),
                (5, 'Práctica Profesional I'),
                (6, 'Práctica Profesional II'), (6, 'Seminario de Tesis'),
            ]
        },
    ]
    
    with app.app_context():
        db.create_all()
        
        carreras_created = 0
        materias_created = 0
        
        for plan in planes:
            # Buscar o crear carrera
            carrera = Carrera.query.filter_by(nombre=plan['nombre']).first()
            if not carrera:
                carrera = Carrera(
                    nombre=plan['nombre'],
                    codigo=plan['codigo'],
                    descripcion=f"Plan de estudios {plan['nombre']}",
                    activa=True
                )
                db.session.add(carrera)
                db.session.flush()
                print(f"Carrera: {plan['nombre']}")
                carreras_created += 1
            else:
                print(f"Carrera existente: {plan['nombre']}")
            
            # Contador para códigos
            contador = {}
            
            # Crear materias
            for cuatri, materia_nombre in plan['materias']:
                # Verificar si ya existe
                existing = Materia.query.filter_by(
                    nombre=materia_nombre,
                    carrera_id=carrera.id
                ).first()
                
                if not existing:
                    # Generar código único
                    if cuatri not in contador:
                        contador[cuatri] = 1
                    else:
                        contador[cuatri] += 1
                    
                    codigo = f"{plan['codigo']}{cuatri:02d}{contador[cuatri]:02d}"
                    
                    materia = Materia(
                        nombre=materia_nombre,
                        codigo=codigo,
                        carrera_id=carrera.id,
                        creditos=0
                    )
                    db.session.add(materia)
                    materias_created += 1
            
            db.session.commit()
            print(f"  - {len(plan['materias'])} materias procesadas")
        
        print(f"\n=== RESUMEN ===")
        print(f"Carreras: {carreras_created}")
        print(f"Materias: {materias_created}")

if __name__ == '__main__':
    import_to_db()