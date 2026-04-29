"""
Modelos de datos para el Portal de Calificaciones
Universidad Felipe Villanueva
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Admin(db.Model):
    """Modelo de Administrador"""
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    notas_remision = db.relationship('NotaRemision', backref='creado_por', lazy='dynamic')
    
    def set_password(self, password):
        """Establece la contraseña hasheada con bcrypt"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica la contraseña"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'nombre': self.nombre,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Carrera(db.Model):
    """Modelo de Carrera"""
    __tablename__ = 'carreras'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
    activa = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    materias = db.relationship('Materia', backref='carrera', lazy='dynamic')
    alumnos = db.relationship('Alumno', backref='carrera', lazy='dynamic')
    
    def to_dict(self, include_materias=False):
        data = {
            'id': self.id,
            'nombre': self.nombre,
            'codigo': self.codigo,
            'descripcion': self.descripcion,
            'activa': self.activa,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_materias:
            data['materias'] = [m.to_dict() for m in self.materias.all()]
        return data


class Materia(db.Model):
    """Modelo de Materia"""
    __tablename__ = 'materias'
    
    id = db.Column(db.Integer, primary_key=True)
    carrera_id = db.Column(db.Integer, db.ForeignKey('carreras.id'), nullable=False)
    nombre = db.Column(db.String(150), nullable=False)
    codigo = db.Column(db.String(20), nullable=False)
    creditos = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    calificaciones = db.relationship('Calificacion', backref='materia', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'carrera_id': self.carrera_id,
            'nombre': self.nombre,
            'codigo': self.codigo,
            'creditos': self.creditos,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Alumno(db.Model):
    """Modelo de Alumno"""
    __tablename__ = 'alumnos'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_control = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido_paterno = db.Column(db.String(100), nullable=False)
    apellido_materno = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    carrera_id = db.Column(db.Integer, db.ForeignKey('carreras.id'), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Requisitos de Titulación
    servicio_social = db.Column(db.Boolean, default=False)
    examen_idiomas = db.Column(db.Boolean, default=False)
    credenciales_completas = db.Column(db.Boolean, default=False)
    documentacion_completa = db.Column(db.Boolean, default=False)
    
    # Relaciones
    calificaciones = db.relationship('Calificacion', backref='alumno', lazy='dynamic')
    practicas = db.relationship('PracticaProfesional', backref='alumno', lazy='dynamic')
    notas_remision = db.relationship('NotaRemision', backref='alumno', lazy='dynamic')
    
    def set_password(self, password):
        """Establece la contraseña hasheada con bcrypt"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica la contraseña"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def nombre_completo(self):
        """Retorna el nombre completo del alumno"""
        parts = [self.nombre, self.apellido_paterno]
        if self.apellido_materno:
            parts.append(self.apellido_materno)
        return ' '.join(parts)
    
    def to_dict(self, include_carrera=True):
        data = {
            'id': self.id,
            'numero_control': self.numero_control,
            'nombre': self.nombre,
            'apellido_paterno': self.apellido_paterno,
            'apellido_materno': self.apellido_materno,
            'nombre_completo': self.nombre_completo,
            'email': self.email,
            'carrera_id': self.carrera_id,
            'activo': self.activo,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'servicio_social': self.servicio_social,
            'examen_idiomas': self.examen_idiomas,
            'credenciales_completas': self.credenciales_completas,
            'documentacion_completa': self.documentacion_completa,
        }
        if include_carrera and self.carrera:
            data['carrera'] = self.carrera.to_dict()
        return data
    
    def to_dict_public(self):
        """Versión pública para el portal del alumno"""
        return {
            'id': self.id,
            'numero_control': self.numero_control,
            'nombre': self.nombre,
            'apellido_paterno': self.apellido_paterno,
            'apellido_materno': self.apellido_materno,
            'nombre_completo': self.nombre_completo,
            'email': self.email,
            'carrera': self.carrera.nombre if self.carrera else None,
            'servicio_social': self.servicio_social,
            'examen_idiomas': self.examen_idiomas,
            'credenciales_completas': self.credenciales_completas,
            'documentacion_completa': self.documentacion_completa,
        }


class Calificacion(db.Model):
    """Modelo de Calificación"""
    __tablename__ = 'calificaciones'
    
    id = db.Column(db.Integer, primary_key=True)
    alumno_id = db.Column(db.Integer, db.ForeignKey('alumnos.id'), nullable=False)
    materia_id = db.Column(db.Integer, db.ForeignKey('materias.id'), nullable=False)
    
    # Asistencia (5 periodos)
    asistencia_1 = db.Column(db.Integer, default=0)  # 0-1
    asistencia_2 = db.Column(db.Integer, default=0)
    asistencia_3 = db.Column(db.Integer, default=0)
    asistencia_4 = db.Column(db.Integer, default=0)
    asistencia_5 = db.Column(db.Integer, default=0)
    
    # Prácticas (0-20)
    practica_1 = db.Column(db.Float, default=0)
    practica_2 = db.Column(db.Float, default=0)
    
    # Extra (recuperación, ordinario, etc.)
    extra_1 = db.Column(db.Float, default=0)
    extra_2 = db.Column(db.Float, default=0)
    
    # Calificación final (0-20)
    calificacion_final = db.Column(db.Float, default=0)
    
    periodo = db.Column(db.String(20))  # ej: "Enero-Abril 2026"
    anio = db.Column(db.Integer)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones únicas para evitar duplicados
    __table_args__ = (
        db.UniqueConstraint('alumno_id', 'materia_id', 'periodo', 'anio', name='uq_calificacion_unique'),
    )
    
    @property
    def promedio_asistencia(self):
        """Calcula el promedio de asistencia"""
        total = self.asistencia_1 + self.asistencia_2 + self.asistencia_3 + self.asistencia_4 + self.asistencia_5
        return round(total / 5 * 100, 1) if total > 0 else 0
    
    @property
    def promedio_practicas(self):
        """Calcula el promedio de prácticas"""
        if self.practica_1 > 0 and self.practica_2 > 0:
            return round((self.practica_1 + self.practica_2) / 2, 1)
        elif self.practica_1 > 0:
            return self.practica_1
        elif self.practica_2 > 0:
            return self.practica_2
        return 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'alumno_id': self.alumno_id,
            'materia_id': self.materia_id,
            'materia': self.materia.to_dict() if self.materia else None,
            'asistencia': {
                '1': self.asistencia_1,
                '2': self.asistencia_2,
                '3': self.asistencia_3,
                '4': self.asistencia_4,
                '5': self.asistencia_5
            },
            'promedio_asistencia': self.promedio_asistencia,
            'practica_1': self.practica_1,
            'practica_2': self.practica_2,
            'extra_1': self.extra_1,
            'extra_2': self.extra_2,
            'promedio_practicas': self.promedio_practicas,
            'calificacion_final': self.calificacion_final,
            'periodo': self.periodo,
            'anio': self.anio,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PracticaProfesional(db.Model):
    """Modelo de Práctica Profesional"""
    __tablename__ = 'practicas_profesionales'
    
    id = db.Column(db.Integer, primary_key=True)
    alumno_id = db.Column(db.Integer, db.ForeignKey('alumnos.id'), nullable=False)
    numero_practica = db.Column(db.Integer, nullable=False)  # 1 o 2
    
    nombre_empresa = db.Column(db.String(200))
    horas = db.Column(db.Integer, default=480)
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, en_curso, completada
    
    reporte_entregado = db.Column(db.Boolean, default=False)
    validada = db.Column(db.Boolean, default=False)
    observaciones = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('alumno_id', 'numero_practica', name='uq_practica_unique'),
    )
    
    @property
    def esta_completada(self):
        """Verifica si la práctica está completada y validada"""
        return self.reporte_entregado and self.validada
    
    def to_dict(self):
        return {
            'id': self.id,
            'alumno_id': self.alumno_id,
            'numero_practica': self.numero_practica,
            'nombre_empresa': self.nombre_empresa,
            'horas': self.horas,
            'estado': self.estado,
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'reporte_entregado': self.reporte_entregado,
            'validada': self.validada,
            'esta_completada': self.esta_completada,
            'observaciones': self.observaciones,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class NotaRemision(db.Model):
    """Modelo de Nota de Remisión (Pagos)"""
    __tablename__ = 'notas_remision'
    
    id = db.Column(db.Integer, primary_key=True)
    alumno_id = db.Column(db.Integer, db.ForeignKey('alumnos.id'), nullable=False)
    
    concepto = db.Column(db.String(255), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    
    fecha_emision = db.Column(db.Date, default=datetime.utcnow)
    fecha_corte = db.Column(db.Date)  # Fecha límite para pagar sin mora
    pagada = db.Column(db.Boolean, default=False)
    fecha_pago = db.Column(db.Date)
    
    created_by_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def intereses_mora(self):
        """Calcula los intereses por mora (5 pesos por día después de fecha_corte)"""
        if self.pagada or not self.fecha_corte or not self.fecha_pago:
            return 0
        
        if self.fecha_pago <= self.fecha_corte:
            return 0
        
        dias_retraso = (self.fecha_pago - self.fecha_corte).days
        if dias_retraso > 0:
            return dias_retraso * 5
        return 0
    
    @property
    def monto_total(self):
        """Monto total incluyendo intereses por mora"""
        return self.monto + self.intereses_mora
    
    def to_dict(self):
        return {
            'id': self.id,
            'alumno_id': self.alumno_id,
            'alumno': self.alumno.to_dict_public() if self.alumno else None,
            'concepto': self.concepto,
            'monto': self.monto,
            'fecha_emision': self.fecha_emision.isoformat() if self.fecha_emision else None,
            'fecha_corte': self.fecha_corte.isoformat() if self.fecha_corte else None,
            'pagada': self.pagada,
            'fecha_pago': self.fecha_pago.isoformat() if self.fecha_pago else None,
            'intereses_mora': self.intereses_mora,
            'monto_total': self.monto_total,
            'created_by': self.creado_por.nombre if self.creado_por else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# ============================================================
# MODELO DE PROFESOR
# ============================================================
class Profesor(db.Model):
    """Modelo de Profesor"""
    __tablename__ = 'profesores'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_empleado = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido_paterno = db.Column(db.String(100), nullable=False)
    apellido_materno = db.Column(db.String(100))
    titulo = db.Column(db.String(50))  # Dr., Mtro., Lic., Ing., etc.
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    asignaciones = db.relationship('Asignacion', backref='profesor', lazy='dynamic')
    
    def set_password(self, password):
        """Establece la contraseña hasheada"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica la contraseña"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'numero_empleado': self.numero_empleado,
            'nombre': self.nombre,
            'apellido_paterno': self.apellido_paterno,
            'apellido_materno': self.apellido_materno,
            'nombre_completo': f"{self.titulo or ''} {self.nombre} {self.apellido_paterno}".strip(),
            'titulo': self.titulo,
            'email': self.email,
            'activo': self.activo,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# ============================================================
# MODELO DE GRUPO
# ============================================================
class Grupo(db.Model):
    """Modelo de Grupo"""
    __tablename__ = 'grupos'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)  #ej: "A", "B"
    carrera_id = db.Column(db.Integer, db.ForeignKey('carreras.id'), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    carrera = db.relationship('Carrera', backref='grupos')
    asignaciones = db.relationship('Asignacion', backref='grupo', lazy='dynamic')
    integrantes = db.relationship('GrupoIntegrante', backref='grupo', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'carrera_id': self.carrera_id,
            'carrera': self.carrera.to_dict() if self.carrera else None,
            'activo': self.activo,
            'total_integrantes': self.integrantes.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# ============================================================
# MODELO DE INTEGRANTE DE GRUPO
# ============================================================
class GrupoIntegrante(db.Model):
    """Alumnos que pertenecen a un grupo"""
    __tablename__ = 'grupo_integrantes'
    
    id = db.Column(db.Integer, primary_key=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos.id'), nullable=False)
    alumno_id = db.Column(db.Integer, db.ForeignKey('alumnos.id'), nullable=False)
    fecha_agregado = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    alumno = db.relationship('Alumno', backref='grupos_asociados')
    
    def to_dict(self):
        return {
            'id': self.id,
            'grupo_id': self.grupo_id,
            'alumno_id': self.alumno_id,
            'alumno': self.alumno.to_dict_public() if self.alumno else None,
            'fecha_agregado': self.fecha_agregado.isoformat() if self.fecha_agregado else None
        }


# ============================================================
# MODELO DE ASIGNACION
# ============================================================
class Asignacion(db.Model):
    """Asignación de profesor a materia para un grupo"""
    __tablename__ = 'asignaciones'
    
    id = db.Column(db.Integer, primary_key=True)
    profesor_id = db.Column(db.Integer, db.ForeignKey('profesores.id'), nullable=False)
    materia_id = db.Column(db.Integer, db.ForeignKey('materias.id'), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos.id'), nullable=False)
    
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    materia = db.relationship('Materia', backref='asignaciones')
    
    def puede_editar_calificaciones(self):
        """Verifica si actualmente está dentro del período de gestión de calificaciones"""
        from datetime import date
        today = date.today()
        return self.activo and self.fecha_inicio <= today <= self.fecha_fin
    
    def to_dict(self):
        return {
            'id': self.id,
            'profesor_id': self.profesor_id,
            'profesor': self.profesor.to_dict() if self.profesor else None,
            'materia_id': self.materia_id,
            'materia': self.materia.to_dict() if self.materia else None,
            'grupo_id': self.grupo_id,
            'grupo': self.grupo.to_dict() if self.grupo else None,
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'puede_editar': self.puede_editar_calificaciones(),
            'activo': self.activo,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


def init_db(app):
    """Inicializa la base de datos con la aplicación"""
    db.init_app(app)
    
    with app.app_context():
        # Crear tablas
        db.create_all()
        
        # Crear admin por defecto si no existe
        if not Admin.query.first():
            admin = Admin(
                username='admin',
                email='admin@universidadfv.edu.mx',
                nombre='Administrador Principal'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('✅ Admin por defecto creado: admin@universidadfv.edu.mx / admin123')
