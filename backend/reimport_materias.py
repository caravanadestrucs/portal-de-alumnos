"""
Re-importa TODAS las materias de las 6 carreras objetivo
"""
from app import app
from models import db, Carrera, Materia

def import_all_materias():
    """Importa TODAS las materias con identificador unico"""
    
    # Las 6 carreras objetivobuscar por CODIGO (ya que los nombres en la BD no coinciden exactamente)
    planes = [
        {
            'codigo': 'ISC',
            'buscar': 'Sistemas',  # Por nombre similarity
            'materias': [
                (1, 'Algebra'), (1, 'Calculo Diferencial'), (1, 'Geometria Analitica'), (1, 'Fisica'), (1, 'Algoritmos y Estructura de Datos'),
                (2, 'Algebra Lineal'), (2, 'Calculo Integral'), (2, 'Calculo Vectorial'), (2, 'Diseno de Sistemas Digitales'), (2, 'Sistemas Operativos'),
                (3, 'Ecuaciones Diferenciales'), (3, 'Matematicas Discretas'), (3, 'Lenguajes Formales y Automatas'), (3, 'Teoria de la Computacion'), (3, 'Administracion de Redes'),
                (4, 'Analisis de Circuitos Electricos'), (4, 'Ingenieria de Software'), (4, 'Bases de Datos'), (4, 'Sistemas de Calidad'), (4, 'Inteligencia Artificial'),
                (5, 'Redes'), (5, 'Etica'), (5, 'Administracion de Proyectos de Software'), (5, 'Gratificacion por Computadora'), (5, 'Desarrollo de Emprendedores'),
                (6, 'Organizacion Industrial'), (6, 'Taller de Investigacion I'), (6, 'Seguridad Computacional'), (6, 'Sistemas de Comunicaciones'), (6, 'Arquitectura de Computadoras'),
                (7, 'Taller de Investigacion II'), (7, 'Seminario de Tesis I'), (7, 'Derecho Informatico'), (7, 'Innovacion Tecnologica'), (7, 'Computacion para Ingenieros'),
                (8, 'Estructura y Programacion de Computadoras'), (8, 'Microcomputadoras'), (8, 'Compiladores'), (8, 'Tecnologia Multimedia'), (8, 'Analisis de Sistema y Senales'),
                (9, 'Seminario de Tesis II'), (9, 'Probabilidad y Estadistica'), (9, 'Comunicacion Oral y Escrita'), (9, 'Fundamentos de Redes'), (9, 'Electronica'),
            ]
        },
        {
            'codigo': 'LC',
            'buscar': 'Contaduria',
            'materias': [
                (1, 'Contabilidad I'), (1, 'Administracion'), (1, 'Informatica'), (1, 'Etica'), (1, 'Matematicas I'),
                (2, 'Contabilidad II'), (2, 'Estadistica I'), (2, 'Macroeconomia'), (2, 'Microeconomia'), (2, 'Matematicas II'),
                (3, 'Contabilidad III'), (3, 'Administracion de Recursos Humanos I'), (3, 'Diagnostico de Mercados'), (3, 'Derecho Laboral'), (3, 'Derecho Mercantil I'),
                (4, 'Contabilidad IV'), (4, 'Administracion de Recursos Humanos II'), (4, 'Adquisiciones y Abastecimientos'), (4, 'Interpretacion de Estados Financieros'), (4, 'Derecho Mercantil II'),
                (5, 'Contabilidad V'), (5, 'Auditoria I'), (5, 'Contabilidad Gubernamental I'), (5, 'Seguridad Social'), (5, 'Impuestos I'),
                (6, 'Auditoria II'), (6, 'Contabilidad Gubernamental II'), (6, 'Desarrollo de Emprendedores'), (6, 'Impuestos II'), (6, 'Costos'),
                (7, 'Auditoria Interna'), (7, 'Seminario de Tesis'), (7, 'Finanzas'), (7, 'Tributacion'), (7, 'Planeacion Financiera'),
                (8, 'Revision Fiscal'), (8, 'Gestion Contable'), (8, 'Normas de Informacion'), (8, 'Contabilidad Internacional'), (8, 'Contabilidad Avanzada'),
                (9, 'Residencia Profesional'), (9, 'Proyecto Integrador'), (9, 'Optativa I'), (9, 'Optativa II'), (9, 'Optativa III'),
            ]
        },
        {
            'codigo': 'LD',
            'buscar': 'Derecho',
            'materias': [
                (1, 'Introduccion al Estudio del Derecho'), (1, 'Derecho Civil I'), (1, 'Derecho Penal I'), (1, 'Historia del Derecho'), (1, 'Filosofia del Derecho'),
                (2, 'Derecho Civil II'), (2, 'Derecho Penal II'), (2, 'Derecho Mercantil I'), (2, 'Teoria General del Proceso'), (2, 'Derecho Constitucional'),
                (3, 'Derecho Civil III'), (3, 'Derecho Mercantil II'), (3, 'Derecho Familiar'), (3, 'Derecho Procesal Civil'), (3, 'Derecho Internacional'),
                (4, 'Derecho del Comercio Exterior'), (4, 'Amparo I'), (4, 'Derecho Fiscal I'), (4, 'Derecho Laboral I'), (4, 'Derecho Notarial I'),
                (5, 'Amparo II'), (5, 'Derecho Fiscal II'), (5, 'Derecho Mercantil III'), (5, 'Derecho Laboral II'), (5, 'Derecho Notarial II'),
                (6, 'Juicios Orales'), (6, 'Derecho Agrario'), (6, 'Derecho Penal Especial'), (6, 'Derecho Mercantil IV'), (6, 'Medicina Forense'),
                (7, 'Seminario de Tesis I'), (7, 'Practica Forense'), (7, 'Argumentacion Juridica'), (7, 'Derecho Ambiental'), (7, 'Integral I'),
                (8, 'Seminario de Tesis II'), (8, 'Integral II'), (8, 'Integral III'), (8, 'Integral IV'), (8, 'Integral V'),
                (9, 'Residencia'), (9, 'Proyecto'), (9, 'Optativa I'), (9, 'Optativa II'), (9, 'Optativa III'),
            ]
        },
        {
            'codigo': 'LP',
            'buscar': 'Pedagogia',
            'materias': [
                (1, 'Introduccion a la Pedagogia'), (1, 'Historia de la Educacion'), (1, 'Filosofia de la Educacion'), (1, 'Psicologia General'), (1, 'Sociologia de la Educacion'),
                (2, 'Didactica General'), (2, 'Psicologia del Desarrollo'), (2, 'Sociologia de la Educacion II'), (2, 'Filosofia de la Educacion II'), (2, 'Historia de la Educacion II'),
                (3, 'Diseno Curricular'), (3, 'Evaluacion Educativa'), (3, 'Tecnologia Educativa'), (3, 'Metodologia de la Investigacion I'), (3, 'Politica Educativa'),
                (4, 'Planeacion Didactica'), (4, 'Metodos de Investigacion'), (4, 'Teoria Pedagogica'), (4, 'Curriculo'), (4, 'Evaluacion'),
                (5, 'Practica Docente I'), (5, 'Diseno de Materiales'), (5, 'Educacion a Distancia'), (5, 'Tutoria'), (5, 'Optativa I'),
                (6, 'Practica Docente II'), (6, 'Seminario de Tesis'), (6, 'Gestion Educativa'), (6, 'Optativa II'), (6, 'Optativa III'),
                (7, 'Proyecto Final'), (7, 'Residencia'), (7, 'Integral I'), (7, 'Integral II'), (7, 'Integral III'),
                (8, 'Integral IV'), (8, 'Integral V'), (8, 'Integral VI'), (8, 'Integral VII'), (8, 'Integral VIII'),
                (9, 'Integral IX'), (9, 'Integral X'), (9, 'Optativa IV'), (9, 'Optativa V'), (9, 'Integral XI'),
            ]
        },
        {
            'codigo': 'LPS',
            'buscar': 'Psicologia',
            'materias': [
                (1, 'Introduccion a la Psicologia'), (1, 'Psicologia General'), (1, 'Biologia General'), (1, 'Historia de la Psicologia'), (1, 'Etica Profesional'),
                (2, 'Psicologia del Desarrollo'), (2, 'Psicologia Social'), (2, 'Estadistica Aplicada'), (2, 'Psicologia Cognitiva'), (2, 'Metodologia de Investigacion'),
                (3, 'Psicologia Clinica'), (3, 'Psicologia Educativa'), (3, 'Psicologia Organizacional'), (3, 'Psicometria'), (3, 'Teorias de la Personalidad'),
                (4, 'Evaluacion Psicologica'), (4, 'Tecnicas de Intervencion'), (4, 'Psicologia del Trabajo'), (4, 'Psicologia Comunitaria'), (4, 'Neurociencia'),
                (5, 'Practica Profesional I'), (5, 'Intervencion en Crisis'), (5, 'Psicologia Juridica'), (5, 'Optativa I'), (5, 'Optativa II'),
                (6, 'Practica Profesional II'), (6, 'Seminario de Tesis'), (6, 'Evaluacion Neuropsicologica'), (6, 'Optativa III'), (6, 'Optativa IV'),
                (7, 'Residencia'), (7, 'Proyecto'), (7, 'Integral I'), (7, 'Integral II'), (7, 'Integral III'),
                (8, 'Integral IV'), (8, 'Integral V'), (8, 'Integral VI'), (8, 'Integral VII'), (8, 'Integral VIII'),
                (9, 'Integral IX'), (9, 'Integral X'), (9, 'Optativa V'), (9, 'Optativa VI'), (9, 'Integral XI'),
            ]
        },
        {
            'codigo': 'LCD',
            'buscar': 'Deporte',
            'materias': [
                (1, 'Anatomia Humana'), (1, 'Fisiologia del Ejercicio'), (1, 'Biomecanica'), (1, 'Primeros Auxilios'), (1, 'Natacion'),
                (2, 'Entrenamiento Deportivo I'), (2, 'Nutricula Deportiva'), (2, 'Psicologia del Deporte'), (2, 'Actividad Fisica Adaptada'), (2, 'Baloncesto'),
                (3, 'Entrenamiento Deportivo II'), (3, 'Evaluacion Funcional'), (3, 'Fisiologia del Ejercicio II'), (3, 'Medicina Deportiva'), (3, 'Voleibol'),
                (4, 'Administracion Deportivo'), (4, 'Metodologia de la Investigacion'), (4, 'Entrenamiento Deportivo III'), (4, 'Periodizacion'), (4, 'Futbol'),
                (5, 'Practica Profesional I'), (5, 'Gestion de Eventos'), (5, 'Optativa I'), (5, 'Optativa II'), (5, 'Badminton'),
                (6, 'Practica Profesional II'), (6, 'Seminario de Tesis'), (6, 'Alto Rendimiento'), (6, 'Optativa III'), (6, 'Optativa IV'),
                (7, 'Residencia'), (7, 'Proyecto Final'), (7, 'Integral I'), (7, 'Integral II'), (7, 'Integral III'),
                (8, 'Integral IV'), (8, 'Integral V'), (8, 'Integral VI'), (8, 'Integral VII'), (8, 'Integral VIII'),
                (9, 'Integral IX'), (9, 'Integral X'), (9, 'Optativa V'), (9, 'Optativa VI'), (9, 'Integral XI'),
            ]
        },
    ]
    
    with app.app_context():
        materias_created = 0
        
        for plan in planes:
            codigo = plan['codigo']
            buscar = plan['buscar']
            
            # Buscar carrera por CODIGO primero
            carrera = Carrera.query.filter_by(codigo=codigo).first()
            
            if not carrera:
                # Buscar por nombre similarity
                carrera = Carrera.query.filter(Carrera.nombre.contains(buscar)).first()
            
            if not carrera:
                print(f"NO ENCONTRADA: {codigo}")
                continue
            
            # Actualizar codigo si es diferente
            if carrera.codigo != codigo:
                carrera.codigo = codigo
                db.session.commit()
            
            print(f"\n=== {codigo}: {carrera.nombre} ===")
            
            # Limpiar materias existentes
            Materia.query.filter_by(carrera_id=carrera.id).delete()
            db.session.commit()
            
            # Contador por cuatrimestre
            contador = {}
            
            # Crear TODAS las materias (45 = 9 cuatrimestres x 5 materias)
            for cuatri, materia_nombre in plan['materias']:
                if cuatri not in contador:
                    contador[cuatri] = 1
                else:
                    contador[cuatri] += 1
                
                # Codigo: ISC + cuatrimestre (01-09) + numero (01-99)
                cod = f"{codigo}{cuatri:02d}{contador[cuatri]:02d}"
                
                materia = Materia(
                    nombre=materia_nombre,
                    codigo=cod,
                    carrera_id=carrera.id,
                    creditos=0
                )
                db.session.add(materia)
                materias_created += 1
            
            db.session.commit()
            
            # Verificar
            total = Materia.query.filter_by(carrera_id=carrera.id).count()
            print(f"Materias: {total}")
    
    print(f"\n=== TOTAL: {materias_created} materias ===")

if __name__ == '__main__':
    import_all_materias()