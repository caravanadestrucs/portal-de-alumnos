"""
Seed Wiki pages — idempotent initial content.

Creates 5 pages:
  - Global (sede_id NULL): reglamento-general, manual-alumno, manual-profesor
  - Sede TEO (sede_id=TEO.id): guia-teotitlan
  - Sede HUA (sede_id=HUA.id): guia-huautla

Usage:
  python scripts/seed_wiki.py
  python scripts/seed_wiki.py --check   # verify counts without writing
"""
import sys
import pathlib

BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

WIKI_PAGES = [
    {
        "slug": "reglamento-general",
        "title": "Reglamento General",
        "sede_codigo": None,
        "body_markdown": """# Reglamento General

## Introduccion

Este reglamento establece las normas academicas y administrativas de la Universidad Felipe Villanueva.

## Objetivos

- Garantizar la calidad educativa
- Fomentar el respeto y la convivencia
- Regular los procesos de evaluacion y titulacion

## Normas Generales

1. Asistir puntualmente a clases y evaluaciones.
2. Respetar a docentes, personal administrativo y companeros.
3. Entregar trabajos y practicas en tiempo y forma.
4. Mantener actualizada la informacion de contacto en el portal.
5. Consultar periodicamente calificaciones y adeudos.

## Proceso de Evaluacion

1. Revisar el calendario academico publicado en el portal.
2. Presentar evaluaciones ordinarias y extraordinarias segun corresponda.
3. Solicitar revision de calificacion dentro de los plazos establecidos.

## Contacto

Para dudas, acudir a la coordinacion academica de tu sede o escribir a soporte academico.
""",
    },
    {
        "slug": "manual-alumno",
        "title": "Manual de Alumno",
        "sede_codigo": None,
        "body_markdown": """# Manual de Alumno

## Bienvenida

Bienvenido al Portal de Calificaciones. Este manual te guiara en el uso basico de la plataforma.

## Primeros Pasos

1. Ingresa con tu correo institucional y contrasena proporcionada.
2. Cambia tu contrasena temporal en el primer acceso si se te solicita.
3. Verifica que tus datos personales sean correctos.

## Consultar Calificaciones

1. Accede a **Mis Calificaciones** desde el menu principal.
2. Selecciona el periodo academico.
3. Revisa asistencia, practicas y calificacion final por materia.

## Pagos y Requisitos

1. Entra a **Mis Pagos** para ver adeudos y notas de remision.
2. Consulta **Requisitos** para verificar servicio social, idiomas y documentacion.

## Soporte

Si olvidaste tu contrasena, usa *Olvidaste tu contrasena* en la pantalla de inicio de sesion.
""",
    },
    {
        "slug": "manual-profesor",
        "title": "Manual de Profesor",
        "sede_codigo": None,
        "body_markdown": """# Manual de Profesor

## Acceso

1. Ingresa con tu correo institucional y contrasena.
2. Si es tu primer acceso, sigue las instrucciones para activar tu cuenta.

## Gestion de Calificaciones

1. Ve a **Calificaciones** en el panel de profesor.
2. Selecciona el grupo y materia asignada.
3. Registra asistencia, practicas y calificacion final dentro del periodo habilitado.

## Grupos y Alumnos

1. Consulta los grupos asignados en **Mis Grupos**.
2. Verifica la lista de integrantes por grupo.

## Recomendaciones

- Guarda los cambios frecuentemente.
- Respeta las fechas de cierre de captura.
- Contacta a la coordinacion si detectas inconsistencias en la asignacion.
""",
    },
    {
        "slug": "guia-teotitlan",
        "title": "Guia Teotitlan",
        "sede_codigo": "TEO",
        "body_markdown": """# Guia Teotitlan

## Sede Teotitlan de Flores Magon, Oaxaca

Bienvenido a la sede Teotitlan. Esta guia reune informacion practica para alumnos y docentes.

## Ubicacion y Contacto

- **Direccion:** Teotitlan de Flores Magon, Oaxaca
- **Codigo de sede:** TEO
- **Horario de atencion:** Lunes a viernes, 08:00 a 16:00

## Servicios

1. Control escolar y ventanilla de tramites.
2. Biblioteca y salas de estudio.
3. Laboratorios por carrera.

## Pasos para Tramites

1. Acude a control escolar con identificacion y numero de control.
2. Solicita el formato correspondiente.
3. Da seguimiento en el portal en la seccion de tramites.

## Nota

Esta pagina es visible solo para usuarios de la sede Teotitlan y administradores generales.
""",
    },
    {
        "slug": "guia-huautla",
        "title": "Guia Huautla",
        "sede_codigo": "HUA",
        "body_markdown": """# Guia Huautla

## Sede Huautla de Jimenez, Oaxaca

Bienvenido a la sede Huautla. Aqui encontraras informacion especifica de esta sede.

## Ubicacion y Contacto

- **Direccion:** Huautla de Jimenez, Oaxaca
- **Codigo de sede:** HUA
- **Horario de atencion:** Lunes a viernes, 08:00 a 15:30

## Servicios

1. Atencion a alumnos y docentes.
2. Coordinacion de practicas profesionales.
3. Apoyo para servicio social.

## Pasos para Tramites

1. Presentate en la coordinacion con tu documentacion.
2. Completa el formato de solicitud.
3. Consulta el estado en el portal.

## Nota

Esta pagina es visible solo para usuarios de la sede Huautla y administradores generales.
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
        # If missing, create via seed_sedes
        if "TEO" not in sede_map or "HUA" not in sede_map:
            from scripts.seed_sedes import seed_sedes
            seed_sedes()
            sede_map = {s.codigo: s.id for s in Sede.query.all()}

        admin = db.session.get(Admin, 1)
        created_by = admin.id if admin else None
        if created_by is None:
            # fallback: first admin
            first = Admin.query.first()
            created_by = first.id if first else None

        created = []
        skipped = []
        for definition in WIKI_PAGES:
            codigo = definition["sede_codigo"]
            sede_id = sede_map.get(codigo) if codigo else None
            slug = definition["slug"]

            # Idempotency check: slug + sede_id unique
            if sede_id is None:
                existing = WikiPage.query.filter(WikiPage.sede_id.is_(None), WikiPage.slug == slug).first()
            else:
                existing = WikiPage.query.filter_by(sede_id=sede_id, slug=slug).first()

            if existing:
                skipped.append(f"{slug} (sede_id={sede_id})")
                if verbose:
                    print(f"[skip] {slug} sede_id={sede_id} already exists id={existing.id}")
                continue

            page = WikiPage(
                sede_id=sede_id,
                slug=slug,
                title=definition["title"],
                body_markdown=definition["body_markdown"],
                created_by=created_by,
            )
            db.session.add(page)
            db.session.flush()  # get id

            rev = WikiRevision(
                page_id=page.id,
                title=definition["title"],
                body_markdown=definition["body_markdown"],
                created_by=created_by,
            )
            db.session.add(rev)
            created.append(f"{slug} (sede_id={sede_id}) id={page.id}")
            if verbose:
                print(f"[create] {slug} sede_id={sede_id} -> id {page.id}")

        if created:
            db.session.commit()
            if verbose:
                print(f"[seed_wiki] created {len(created)} pages")
        else:
            if verbose:
                print("[seed_wiki] no new pages to create")

        # Verification
        total = WikiPage.query.count()
        if verbose:
            print(f"[verify] total wiki_pages = {total} (expected 5)")
            # scope_wiki verification: simulate queries
            from utils.scope import scope_wiki
            from flask_jwt_extended import create_access_token

            # Helper to test scope_wiki for different roles
            def count_for_claims(claims, description):
                # Simulate JWT claims without actual token by directly filtering like scope_wiki does
                # We will manually apply same logic as scope_wiki for verification: call scope_wiki with mocked JWT
                # Easiest: create token and test via app test client? But simpler: direct logic
                # We create a token and query via API? Instead we directly test visibility function
                from routes.wiki import _is_wiki_visible

            # Manual visibility counts
            pages = WikiPage.query.all()
            def visible_for(role, sede_id):
                count = 0
                for p in pages:
                    claims = {"role": role, "sede_id": sede_id, "user_type": "admin" if role in ("general_admin","sede_admin") else "alumno"}
                    from routes.wiki import _is_wiki_visible
                    if _is_wiki_visible(p.sede_id, claims):
                        count += 1
                return count

            print(f"[scope] general_admin sees {visible_for('general_admin', None)} pages (expected 5)")
            print(f"[scope] sede_admin TEO (sede_id=1) sees {visible_for('sede_admin', 1)} pages (expected 4: 3 global + TEO)")
            print(f"[scope] sede_admin HUA (sede_id=2) sees {visible_for('sede_admin', 2)} pages (expected 4: 3 global + HUA)")

        return {"created": created, "skipped": skipped, "total": total}


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
                print(f"  id={p.id} slug={p.slug} sede_id={p.sede_id} title={p.title}")
            if total != 5:
                print("[check] WARNING expected 5")
            else:
                print("[check] OK 5 pages")
        return

    result = seed_wiki(verbose=True)
    print(f"[done] created={len(result['created'])} skipped={len(result['skipped'])} total={result['total']}")


if __name__ == "__main__":
    main()
