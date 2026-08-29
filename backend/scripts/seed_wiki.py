"""
Seed Wiki pages — idempotent initial content.

Creates 6 pages:
  - Global (sede_id NULL): reglamento-general, manual-alumno, manual-profesor, manual-admin
  - Sede TEO (sede_id=TEO.id): guia-teotitlan
  - Sede HUA (sede_id=HUA.id): guia-huautla

Usage:
  python scripts/seed_wiki.py
  python scripts/seed_wiki.py --check   # verify counts without writing

Idempotent: if slug+sede exists, UPDATE body_markdown/title and creates a new WikiRevision.
"""
import sys
import pathlib
from datetime import datetime

BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

WIKI_PAGES = [
    {
        "slug": "reglamento-general",
        "title": "Reglamento General",
        "sede_codigo": None,
        "body_markdown": """# Reglamento General

## Introducción

Este Reglamento regula la vida académica y administrativa de la Universidad Felipe Villanueva en todas sus sedes y modalidades. Garantiza orden, calidad y convivencia. Es obligatorio para alumnos, docentes y personal. Se actualiza cada ciclo escolar y está disponible en la Wiki del portal. La Coordinación Académica es la autoridad interpretativa. El desconocimiento no exime de cumplimiento.

## Derechos y obligaciones del alumno

**Derechos:**
- Recibir educación conforme al plan de estudios oficial.
- Ser evaluado de forma objetiva y oportuna.
- Consultar historial, calificaciones y pagos en el portal.
- Solicitar revisión de calificación en plazos establecidos.
- Recibir constancias y documentos al estar al corriente.
- Participar en actividades académicas y culturales.

**Obligaciones:**
- Asistir puntualmente y cumplir 80% de asistencia mínima por materia.
- Portar credencial y respetar instalaciones.
- Entregar trabajos y prácticas a tiempo.
- Mantener datos actualizados y revisar notificaciones.
- Conducirse con respeto y honestidad académica.
- Cubrir colegiaturas oportunamente.

## Evaluación y calificaciones

Sistema numérico de **0 a 10**, con **8.0 como mínimo aprobatorio**.

| Concepto | Detalle |
|---|---|
| Escala | 0.0 a 10.0 con un decimal |
| Mínimo aprobatorio | 8.0 |
| Asistencia mínima | 80% ordinario, 60% extraordinario |
| A1-A5 | Cinco avances parciales |
| Prácticas | 30-40% según materia |
| Examen final | 30-50% según plan |
| Extraordinario | Máximo 8.0 |
| Recursamiento | Si no aprueba el extra |

El docente registra A1-A5, prácticas, extra y final. El alumno ve el desglose en **Mis Calificaciones**. Las boletas se generan al cierre.

## Requisitos de titulación

- 100% de créditos aprobados.
- Servicio social liberado (480 h).
- Prácticas profesionales acreditadas.
- Idioma extranjero nivel A2 según carrera.
- Sin adeudos de documentos ni pagos.
- Modalidad: tesis, tesina, examen general o promedio.

## Sanciones

| Falta | Sanción |
|---|---|
| Retardo reiterado | Amonestación verbal |
| Inasistencia >20% | Pérdida de derecho a ordinario |
| Plagio | Anulación y acta |
| Falsificación | Suspensión temporal |
| Falta grave | Baja definitiva |

Las sanciones son apelables por escrito en 5 días hábiles.

## Contacto

- Teotitlán: 08:00-16:00 L-V, Control Escolar.
- Huautla: 08:00-15:30 L-V, Coordinación.
- Soporte: soporte@universidadfv.edu.mx
- Ventanilla virtual en el portal.
""",
    },
    {
        "slug": "manual-alumno",
        "title": "Manual del Alumno",
        "sede_codigo": None,
        "body_markdown": """# Manual del Alumno

## Introducción

Este manual explica cómo usar el Portal de Alumnos. Aplica a todas las carreras y sedes. Aprenderás a consultar calificaciones, pagos, requisitos y grupos, y a gestionar tu acceso. Funciona en computadora y celular. Usa Chrome o Firefox actualizado.

## 1. Acceso al portal

1. Entra a https://alumnos.felipe-villa-nueva-teotitlan.site
2. Clic en **Iniciar sesión**.
3. Ingresa correo institucional y contraseña.
4. En el primer acceso, cambia la contraseña temporal.
5. Guarda la nueva contraseña en lugar seguro.

## 2. Dashboard principal

Verás:
- Promedio general y avance de créditos.
- Alertas de adeudos o requisitos pendientes.
- Accesos a **Mis Calificaciones**, **Mis Pagos**, **Requisitos**.
- Avisos de tu sede.

## 3. Mis calificaciones

1. Ve a **Mis Calificaciones**.
2. Selecciona ciclo y semestre.
3. Tabla por materia:

| Materia | A1 | A2 | A3 | A4 | A5 | Prácticas | Extra | Final |
|---|---|---|---|---|---|---|---|---|
| Matemáticas I | 8.5 | 9.0 | 8.0 | 9.0 | 8.5 | 9.0 | - | 8.6 |

4. Clic en la materia para ver desglose y observaciones.
5. Si hay error, contacta al docente en 3 días.

## 4. Mis pagos

1. Entra a **Mis Pagos**.
2. Verás colegiaturas con estado: pagado, pendiente o vencido.
3. Cada pago muestra fecha límite, monto y referencia.
4. Descarga comprobante en PDF.

## 5. Requisitos

Listado de:
- Documentos (acta, CURP, certificado).
- Servicio social y horas.
- Prácticas profesionales.
- Idioma extranjero.
Cada uno indica avance y fecha límite.

## 6. Grupos

En **Mis Grupos** ves grupo asignado, carrera, semestre y compañeros. Determina tus materias y docentes.

## 7. Cómo recuperar contraseña

1. En login, clic en **¿Olvidaste tu contraseña?**
2. Ingresa tu correo.
3. Recibes enlace válido 30 min.
4. Crea contraseña (8+ caracteres, una mayúscula y número).
5. Si no llega, revisa spam o acude a Control Escolar.

## 8. Preguntas frecuentes (FAQ)

| Pregunta | Respuesta |
|---|---|
| ¿Cuándo se actualizan calificaciones? | Al cierre de cada parcial A1-A5 y al final. |
| ¿Puedo ver periodos anteriores? | Sí, con el selector de periodo. |
| ¿Qué significa 8 mínimo? | 8.0 o más aprueba; 7.9 no aprueba. |
| ¿No veo mis pagos? | Verifica matrícula y sede vinculada. |
| ¿Funciona sin internet? | No, requiere conexión. |
| ¿A quién contacto si falla? | Soporte por correo o ventanilla. |
""",
    },
    {
        "slug": "manual-profesor",
        "title": "Manual del Profesor",
        "sede_codigo": None,
        "body_markdown": """# Manual del Profesor

## Introducción

Manual para docentes. Explica acceso, grupos asignados, registro de calificaciones y boletas. El uso correcto garantiza que los alumnos vean resultados a tiempo.

## 1. Acceso

1. Entra al portal con tu correo institucional.
2. Usa contraseña de Coordinación Académica.
3. Cambia la contraseña temporal en el primer acceso.
4. Si no entras, verifica cuenta activa y sede asignada.

## 2. Dashboard del profesor

Verás:
- Grupos asignados del ciclo actual.
- Materias por grupo.
- Alertas de periodos de captura abiertos o por cerrar.
- Accesos a **Calificar**, **Mis Grupos**, **Boletas**.

## 3. Cómo calificar

Ruta: **Calificaciones** > ciclo > grupo > materia.

| Campo | Descripción | Rango |
|---|---|---|
| A1 | Avance 1 | 0-10 |
| A2 | Avance 2 | 0-10 |
| A3 | Avance 3 | 0-10 |
| A4 | Avance 4 | 0-10 |
| A5 | Avance 5 | 0-10 |
| Prácticas | Promedio prácticas | 0-10 |
| Extra | Extraordinario | 0-10 |
| Final | Calculado automático | 0-10 |

Pasos:
1. Selecciona alumno.
2. Ingresa 0 a 10 con un decimal (ej: 8.5).
3. El sistema calcula el final según ponderación.
4. Guarda con **Guardar cambios**. Valida mínimo 8.0.
5. Respeta fechas de cierre; fuera de periodo se bloquea.

> No dejes celdas vacías si el alumno tiene derecho; usa 0 si no presentó.

Validaciones:
- Solo calificas grupos y materias asignadas.
- No editas después del cierre sin autorización.

## 4. Grupos

En **Mis Grupos** ves código del grupo, carrera, semestre, lista de alumnos con control y estado, horario y aula. Si falta un alumno, avisa a Control Escolar.

## 5. Boletas

1. Ve a **Boletas** > grupo y periodo.
2. Genera vista previa.
3. Descarga PDF para firma.
4. Incluyen promedio, asistencias y observaciones.

## 6. Preguntas frecuentes (FAQ)

| Pregunta | Respuesta |
|---|---|
| ¿Puedo corregir después de guardar? | Sí, mientras el periodo siga abierto. |
| ¿Alumno sin derecho a examen? | Verifica 80% asistencia; reporta error. |
| ¿Olvidé contraseña? | Usa *Olvidaste tu contraseña* o pide reset. |
| ¿Calificar desde celular? | Sí, pero mejor en computadora. |
| ¿Cuándo ve el alumno la calificación? | Al guardar, en tiempo real. |
| ¿Grupo faltante? | Contacta a Coordinación con carga horaria. |
""",
    },
    {
        "slug": "manual-admin",
        "title": "Manual del Administrador",
        "sede_codigo": None,
        "body_markdown": """# Manual del Administrador

## Introducción

Para administradores del portal. Cubre alumnos, carreras, materias, grupos, calificaciones, pagos, boletas, importación, exportación, sedes, usuarios y wiki. Roles: **general_admin** (global) y **sede_admin** (solo su sede).

## Roles: general vs sede_admin

| Aspecto | general_admin | sede_admin |
|---|---|---|
| Alcance | Todas las sedes | Solo su sede |
| Crear sedes | Sí | No (403) |
| Wiki global (NULL) | Sí | No |
| Wiki de su sede | Sí | Sí |
| Ver wiki otra sede | Sí | No |
| Alumnos | Todos | Solo su sede |
| Importación | Todas | Solo su sede |
| Exportación | Todas/filtrada | Solo su sede |
| Crear admins | Sí | No |

sede_admin nunca ve ni modifica datos de otra sede.

## 1. Alumnos

Listar con filtros por sede, carrera, grupo y búsqueda. Crear con datos personales, carrera, sede y grupo. Editar permite cambio de sede/grupo. Eliminar solo sin calificaciones ni pagos. Importación vía CSV.

## 2. Carreras y materias

Carreras: nombre, código único, descripción. Materias: asociadas a carrera con clave, nombre, semestre y créditos. No se eliminan si tienen calificaciones.

## 3. Grupos

Crear por carrera, semestre y sede (código único por sede). Asignar alumnos y docentes por materia. Ver integrantes y asignaciones.

## 4. Calificaciones

Ver calificaciones de tu alcance. Desglose A1-A5, prácticas, extra y final (0-10, 8 mínimo). Correcciones solo con periodo abierto. Auditoría registra cambios.

## 5. Pagos y requisitos

Pagos: colegiatura, inscripción, estados pagado/pendiente/vencido. Requisitos: documentos, servicio social (480h), prácticas, idioma.

## 6. Boletas

Generación por grupo y periodo. Vista previa y PDF. Solo alumnos con calificaciones completas generan boleta completa.

## 7. Importación

**Importar** > subir CSV/XLSX con plantilla. Valida columnas, duplicados y sede. Límite 10MB. Errores por fila. sede_admin solo importa a su sede.

## 8. Exportación

Exportar listados a Excel (alumnos, calificaciones, pagos). Respeta filtro de sede. general_admin exporta todo o por sede.

## 9. Sedes

Solo general_admin crea/edita sedes (nombre, código, dirección, activa). sede_admin solo consulta su sede.

## 10. Usuarios y wiki

Usuarios: crear admins con role y sede (solo general_admin). Wiki: páginas markdown, **sede_id NULL** = global, slug único por sede, adjuntos 10MB, historial.

## Soporte

Dudas: Coordinación General o soporte@universidadfv.edu.mx. Ver manuales de alumno y profesor.
""",
    },
    {
        "slug": "guia-teotitlan",
        "title": "Guía Teotitlán",
        "sede_codigo": "TEO",
        "body_markdown": """# Guía Teotitlán

## Bienvenida

Sede Teotitlán de Flores Magón, Oaxaca. Sede principal de la Universidad Felipe Villanueva. Aquí cursan alumnos de varias carreras con atención de lunes a viernes en Control Escolar, biblioteca y laboratorios. Esta guía reúne dirección, contacto, horarios, carreras, grupos y servicios.

## Dirección y contacto

| Concepto | Detalle |
|---|---|
| Sede | Teotitlán de Flores Magón, Oaxaca |
| Código | TEO |
| Dirección | Calle Principal s/n, Centro, Teotitlán de Flores Magón, Oax. C.P. 68530 |
| Teléfono | 236 372 0000 (ejemplo) |
| Correo | teotitlan@universidadfv.edu.mx |
| Horario de atención | Lunes a viernes 08:00 a 16:00 |
| Portal | https://alumnos.felipe-villa-nueva-teotitlan.site |

## Carreras que se imparten

| Carrera | Código | Duración | Modalidad |
|---|---|---|---|
| Lic. en Enfermería | ENF-TEO | 8 semestres | Escolarizada |
| Lic. en Trabajo Social | TS-TEO | 8 semestres | Escolarizada |
| Lic. en Psicología | PSI-TEO | 8 semestres | Escolarizada |
| Lic. en Administración | ADM-TEO | 8 semestres | Escolarizada |

Consulta tu plan de estudios y materias en el portal > **Carreras**.

## Grupos

Los grupos se identifican por carrera, semestre y sede (ej: ENF-3TEO). Ver tu grupo en **Mis Grupos**. Si eres docente, tus grupos asignados aparecen en el dashboard. Para cambios de grupo, acude a Control Escolar con justificación.

## Servicios

- **Control Escolar y ventanilla de trámites:** Constancias, credenciales, boletas, certificados.
- **Biblioteca y salas de estudio:** 08:00-15:30, préstamo con credencial.
- **Laboratorios por carrera:** Enfermería y cómputo, con horario asignado.
- **Coordinación de prácticas y servicio social:** Asesoría y liberación.
- **Soporte del portal:** En sitio y por correo.

## Trámites paso a paso

1. Acude a Control Escolar con credencial y número de control.
2. Solicita formato (constancia, revisión, baja, etc.).
3. Entrega documentación y cubre pago si aplica.
4. Da seguimiento en el portal o en ventanilla.

> Esta página es visible solo para usuarios de la sede Teotitlán y administradores generales. Otras sedes no la ven.
""",
    },
    {
        "slug": "guia-huautla",
        "title": "Guía Huautla",
        "sede_codigo": "HUA",
        "body_markdown": """# Guía Huautla

## Bienvenida

Sede Huautla de Jiménez, Oaxaca. Extensión de la Universidad Felipe Villanueva en la Sierra Mazateca. Ofrece atención cercana a alumnos de la región, con servicios de control escolar, prácticas y servicio social. Esta guía concentra información práctica de ubicación, contacto y servicios.

## Dirección y contacto

| Concepto | Detalle |
|---|---|
| Sede | Huautla de Jiménez, Oaxaca |
| Código | HUA |
| Dirección | Carretera Huautla-Jalapa s/n, Barrio Centro, Huautla de Jiménez, Oax. C.P. 68500 |
| Teléfono | 236 381 0000 (ejemplo) |
| Correo | huautla@universidadfv.edu.mx |
| Horario de atención | Lunes a viernes 08:00 a 15:30 |
| Portal | https://alumnos.felipe-villa-nueva-teotitlan.site |

## Carreras que se imparten

| Carrera | Código | Duración | Modalidad |
|---|---|---|---|
| Lic. en Enfermería | ENF-HUA | 8 semestres | Escolarizada |
| Lic. en Trabajo Social | TS-HUA | 8 semestres | Escolarizada |
| Lic. en Pedagogía | PED-HUA | 8 semestres | Escolarizada |

Verifica materias y plan en **Carreras** dentro del portal.

## Grupos

Formato carrera+semestre+sede (ej: ENF-2HUA). Consulta tu grupo en **Mis Grupos**. Docentes ven sus grupos en **Mis Grupos** del panel profesor. Cambios de grupo requieren autorización de Coordinación.

## Servicios

- **Atención a alumnos y docentes:** Trámites, dudas y asesorías.
- **Coordinación de prácticas profesionales:** Vinculación con hospitales y centros.
- **Apoyo para servicio social:** Registro, seguimiento y liberación.
- **Biblioteca básica y sala de cómputo:** Horario 08:00-15:00.
- **Soporte del portal:** Presencial y vía correo.

## Trámites

1. Preséntate en Coordinación con identificación y número de control.
2. Completa formato de solicitud.
3. Entrega documentos y realiza pago si corresponde.
4. Consulta estado en el portal > **Requisitos** o en ventanilla.

> Esta página es privada de la sede Huautla. Solo usuarios HUA y administradores generales pueden verla. Usuarios TEO no tienen acceso.
""",
    },
]


def seed_wiki(verbose=True):
    from app import create_app
    from models import db, WikiPage, WikiRevision, Sede, Admin

    app = create_app()
    with app.app_context():
        db.create_all()

        # Ensure sedes exist
        sede_map = {s.codigo: s.id for s in Sede.query.all()}
        if "TEO" not in sede_map or "HUA" not in sede_map:
            from scripts.seed_sedes import seed_sedes
            seed_sedes()
            sede_map = {s.codigo: s.id for s in Sede.query.all()}

        admin = db.session.get(Admin, 1)
        created_by = admin.id if admin else None
        if created_by is None:
            first = Admin.query.first()
            created_by = first.id if first else None

        created = []
        updated = []
        skipped = []
        for definition in WIKI_PAGES:
            codigo = definition["sede_codigo"]
            sede_id = sede_map.get(codigo) if codigo else None
            slug = definition["slug"]
            title = definition["title"]
            body = definition["body_markdown"]

            # Idempotency: slug + sede_id unique -> UPDATE if exists
            if sede_id is None:
                existing = WikiPage.query.filter(WikiPage.sede_id.is_(None), WikiPage.slug == slug).first()
            else:
                existing = WikiPage.query.filter_by(sede_id=sede_id, slug=slug).first()

            if existing:
                # Check if content differs
                if existing.body_markdown != body or existing.title != title:
                    existing.title = title
                    existing.body_markdown = body
                    existing.updated_at = datetime.utcnow()
                    # Create new revision for the update
                    rev = WikiRevision(
                        page_id=existing.id,
                        title=title,
                        body_markdown=body,
                        created_by=created_by,
                    )
                    db.session.add(rev)
                    db.session.flush()
                    updated.append(f"{slug} (sede_id={sede_id}) id={existing.id}")
                    if verbose:
                        print(f"[update] {slug} sede_id={sede_id} id={existing.id} -> updated ({len(body)} chars)")
                else:
                    skipped.append(f"{slug} (sede_id={sede_id})")
                    if verbose:
                        print(f"[skip] {slug} sede_id={sede_id} already up-to-date id={existing.id}")
                continue

            page = WikiPage(
                sede_id=sede_id,
                slug=slug,
                title=title,
                body_markdown=body,
                created_by=created_by,
            )
            db.session.add(page)
            db.session.flush()  # get id

            rev = WikiRevision(
                page_id=page.id,
                title=title,
                body_markdown=body,
                created_by=created_by,
            )
            db.session.add(rev)
            created.append(f"{slug} (sede_id={sede_id}) id={page.id}")
            if verbose:
                print(f"[create] {slug} sede_id={sede_id} -> id {page.id} ({len(body)} chars)")

        if created or updated:
            db.session.commit()
            if verbose:
                print(f"[seed_wiki] created {len(created)} updated {len(updated)} total {len(created)+len(updated)} pages")
        else:
            if verbose:
                print("[seed_wiki] no new pages to create")

        # Verification
        total = WikiPage.query.count()
        if verbose:
            print(f"[verify] total wiki_pages = {total} (expected 6)")
            for p in WikiPage.query.order_by(WikiPage.sede_id, WikiPage.slug).all():
                print(f"  id={p.id} slug={p.slug} sede_id={p.sede_id} len={len(p.body_markdown)} title={p.title}")
            # length check
            short = [p for p in WikiPage.query.all() if len(p.body_markdown or "") < 1500]
            if short:
                print(f"[verify] WARNING {len(short)} pages <1500 chars: {[s.slug for s in short]}")
            else:
                print("[verify] all pages >=1500 chars OK")
            # scope verification via _is_wiki_visible
            pages = WikiPage.query.all()
            def visible_for(role, sede_id):
                count = 0
                for p in pages:
                    claims = {"role": role, "sede_id": sede_id, "user_type": "admin" if role in ("general_admin","sede_admin") else "alumno"}
                    from routes.wiki import _is_wiki_visible
                    if _is_wiki_visible(p.sede_id, claims):
                        count += 1
                return count

            # Resolve actual sede ids for accurate expectation
            teo_id = sede_map.get("TEO")
            hua_id = sede_map.get("HUA")
            print(f"[scope] general_admin sees {visible_for('general_admin', None)} pages (expected 6)")
            print(f"[scope] sede_admin TEO (sede_id={teo_id}) sees {visible_for('sede_admin', teo_id)} pages (expected 5: 4 global + TEO)")
            print(f"[scope] sede_admin HUA (sede_id={hua_id}) sees {visible_for('sede_admin', hua_id)} pages (expected 5: 4 global + HUA)")
            # Also show old expectation for compatibility
            print(f"[scope] note: prompt says TEO 4 (3+1), but with manual-admin global count is 4+1=5")

        return {"created": created, "updated": updated, "skipped": skipped, "total": total}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Seed wiki pages")
    parser.add_argument("--check", action="store_true", help="Only verify, do not create")
    args = parser.parse_args()

    if args.check:
        from app import create_app
        from models import db, WikiPage
        app = create_app()
        with app.app_context():
            total = WikiPage.query.count()
            print(f"[check] total wiki_pages = {total}")
            for p in WikiPage.query.order_by(WikiPage.sede_id, WikiPage.slug).all():
                print(f"  id={p.id} slug={p.slug} sede_id={p.sede_id} len={len(p.body_markdown)} title={p.title}")
            if total != 6:
                print("[check] WARNING expected 6")
            else:
                print("[check] OK 6 pages")
            short = [p for p in WikiPage.query.all() if len(p.body_markdown or "") < 1500]
            if short:
                print(f"[check] FAIL {len(short)} pages <1500: {[p.slug for p in short]}")
            else:
                print("[check] OK all pages >=1500 chars")
        return

    result = seed_wiki(verbose=True)
    print(f"[done] created={len(result['created'])} updated={len(result['updated'])} skipped={len(result['skipped'])} total={result['total']}")


if __name__ == "__main__":
    main()
