# Portal FV - Tareas de desarrollo

Este documento enumera el estado actual de las tareas para el Portal FV (Universidad Felipe Villanueva) y sirve como punto de partida para continuar con la implementación. Actualizalo con tus avances y prioridades.

## 1) Visión general
- Objetivo: Portal para ver calificaciones, asistencias, prácticas, pagos y exportaciones; con roles de admin y alumno.
- Stack actual: Backend en Flask + SQLAlchemy, Frontend en React (Vite) + Tailwind. Plan de migración: MySQL en servidor; SQLite local para desarrollo.
- Modo de despliegue: Backend API en /api/*; Frontend separado (SPA). Autenticación vía JWT.

## 2) Progreso y estado
Completed (Hecho)
- [x] Modelos de datos en backend: Admin, Carrera, Materia, Alumno, Calificacion, PracticaProfesional, NotaRemision.
- [x] Endpoints de autenticación y usuario (login, signup, me, logout).
- [x] CRUD Básico para Carreras y Materias, ALumnos, Calificaciones (con esquema 5 asistencias, 2 prácticas,  calificación final).
- [x] Exportación de SQL/Excel (endpoints de exportación).
- [x] UI Admin: Carreras, Materias, Alumnos, Calificaciones, Pagos, Exportar.
- [x] Inicio de diseño UI Moderno Gradiente (turquesa) y mockups visuales.
- [x] Lógica de cascada al crear Materia: asignación de calificaciones vacías para todos los alumnos de la carrera.
- [x] Lógica al eliminar Materia: eliminan sus Calificaciones asociadas.
- [x] Lógica al cambiar carrera de un Alumno: se eliminan calificaciones previas.
- [x] Flujo de pagos: crear nota de remisión, ver estado y eliminar con confirmación.
- [x] Flujo de edición de Carreras con un modal (fix aplicado para carga de datos).
- [x] Doc de diseño y plan SDD-Dev (spec, design, tasks) creado y versionado.

In progress (En curso)
- [ ] Robustecer el modal de Carreras para garantizar que se carguen correctamente los campos al editar y que el submit funcione de forma fiable.
- [ ] Verificar y unificar respuestas de backend para calificaciones/pagos en el frontend (consumo de data, claves devueltas).
- [ ] Ampliar tests automatizados (sdd-verify) para cubrir flujos de carreras, calificaciones y pagos.
- [ ] Agregar validaciones y mensajes de error claros en todas las pantallas (front/back).

Pending (Pendiente)
- [ ] Añadir migraciones y pruebas de migración para la base de datos (SQLite -> MySQL).
- [ ] Comprobaciones de seguridad y validaciones de entrada (input sanitization, rate limits, logs).
- [ ] Documentar uso de la API para terceros (Swagger o OpenAPI a futuro).

## 3) Plan de verificación (alto nivel)
- [ ] Ejecutar pruebas unitarias e integrales (sdd-verify) para cada módulo: Carreras, Materias, Alumnos, Calificaciones y Pagos.
- [ ] Verificar que las operaciones CRUD funcionan en todos los endpoints y la UI refleja el estado correcto.
- [ ] Validar que las migraciones entre SQLite y MySQL no pierdan datos (backups y dumps).
- [ ] Verificar seguridad (autenticación, autorización, logs, registro de acciones).

## 4) Decisiones y su impacto
- Persistencia: SQLite para desarrollo; plan de migración a MySQL para producción.
- Frontend: React con Tailwind; interfaz de usuario enfocada en UX con diseño moderno y claro.
- Patrones: Calificaciones, Pagos, y Carreras deben mapear claramente a endpoints en el backend y a componentes en el frontend.

## 5) Archivos relevantes (resumen)
- Backend
  - backend/routes/carreras.py, backend/routes/materias.py, backend/routes/alumnos.py
- Frontend
  - frontend/src/pages/admin/Carreras.jsx
  - frontend/src/pages/admin/Pagos.jsx
  - frontend/src/pages/admin/Calificaciones.jsx
  - frontend/src/api/carreras.js
  - frontend/src/api/materias.js
  - frontend/src/api/alumnos.js
  - frontend/src/api/pagos.js
- Documentos
  - docs/superpowers/specs/ (delta specs)
  - docs/tareas/portal-fv-tareas.md (este archivo de tareas)

## 6) Cómo continuar
- Agregar/editar funcionalidades específicas en Carreras (revisión de modal, validaciones, mensajes de error).
- Completar flujos de Pagos: eliminar con confirmación, mostrar fecha de emisión y fecha de pago, y el borrado correcto.
- Añadir tests automáticos y verificar contra spec (sdd-verify).
- Mantener comunicación para revisión de cambios y próximos pasos.

> Nota: Este documento está pensado para que puedas añadir tus notas y seguir la evolución. Cuando quieras, te envió una versión actualizada o un patch para aplicar directamente en el repo.




tareas que propongo extra, 


el modulo de pagos y recibos no serefljan los actualizaciones coriigelo

necesitamos un apartado llamado grupos donde a un grupo de alumnos de les dara un nombre

necesitamos un apartado llamado asignacion profesores donde el admin dara las materias a los profesores y aa que grupos con esto tendra el fin de no internerir en materias que no le corresponden y poder dar sierto limite tambien una opcion para que el pueda editar o no dichas calificaciones del grupo y su materia impartida con el fin de evitar modificacion de datos fuera de periodos 

se necesita un rol nuevo llamado profesores y un apartado llamado profesores donde los daremos de alta con su datos relevantes 


me tienes que avisar uando termines
