#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EXPORT MYSQL - Portal de Alumnos
Genera un dump .sql compatible con MySQL / phpMyAdmin a partir de la base
SQLite local (backend/instance/portal.db). Solo lectura sobre SQLite.

Uso:
    python export_mysql.py [--salida portal_mysql.sql]

Salida: CREATE TABLE + INSERTs + índices + FKs + AUTO_INCREMENT, todo con
sintaxis MySQL (backticks, ENGINE=InnoDB, utf8mb4). Importable desde
phpMyAdmin o con: mysql -u user -p db < portal_mysql.sql

NOTA: el dump contiene password_hash (hasheados) y la config SMTP de la
tabla config. Es un respaldo íntegro; manejarlo como información sensible.
"""
import os
import re
import sqlite3
import sys
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "instance", "portal.db")

# Columnas que pueden superar 64KB -> MySQL TEXT no alcanza, usar MEDIUMTEXT
LONG_TEXT_COLUMNS = {
    ("wiki_pages", "body_markdown"),
    ("wiki_revisions", "body_markdown"),
}

TYPE_MAP = {
    "INTEGER": "INT",
    "TEXT": "TEXT",
    "REAL": "DOUBLE",
    "BLOB": "LONGBLOB",
    "NUMERIC": "DECIMAL(10,4)",
    "BOOLEAN": "TINYINT(1)",
    "DATE": "DATE",
    "DATETIME": "DATETIME",
    "TIMESTAMP": "DATETIME",
    "VARCHAR": "VARCHAR",
    "JSON": "JSON",
}

FK_ACTIONS = {
    "NO ACTION": "RESTRICT",
    "CASCADE": "CASCADE",
    "SET NULL": "SET NULL",
    "SET DEFAULT": "SET DEFAULT",
    "RESTRICT": "RESTRICT",
}


def sqlite_type_to_mysql(declared, table, column):
    """Convierte el tipo declarado por SQLite a un tipo MySQL."""
    dt = (declared or "TEXT").upper()
    if (table, column) in LONG_TEXT_COLUMNS:
        return "MEDIUMTEXT"
    if dt.startswith("VARCHAR"):
        m = re.match(r"VARCHAR\((\d+)\)", dt)
        if m:
            return f"VARCHAR({m.group(1)})"
        return "VARCHAR(255)"
    if dt.startswith("CHAR"):
        m = re.match(r"CHAR\((\d+)\)", dt)
        if m:
            return f"CHAR({m.group(1)})"
        return "CHAR(255)"
    if dt.startswith("DECIMAL") or dt.startswith("NUMERIC"):
        m = re.match(r"(DECIMAL|NUMERIC)\((\d+)(,(\d+))?\)", dt)
        if m:
            return f"DECIMAL({m.group(2)},{m.group(4) or 0})"
        return "DECIMAL(10,4)"
    return TYPE_MAP.get(dt, "TEXT")


def esc(value):
    """Escapa un valor Python para un literal SQL MySQL."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    s = str(value)
    # Quitar fracción de segundos (MySQL DATETIME default fsp=0 no la acepta)
    s = re.sub(r"\.\d{6}$", "", s)
    return "'" + s.replace("'", "''") + "'"


def esc_default(dflt):
    """Normaliza el DEFAULT que devuelve SQLite (literal con comillas) a MySQL."""
    if dflt is None:
        return None
    d = str(dflt)
    if d == "NULL":
        return "NULL"
    # Literal string SQLite: 'valor' -> quitar comillas envolventes y escapar
    if len(d) >= 2 and d[0] == "'" and d[-1] == "'":
        return esc(d[1:-1])
    # Palabras clave / expresiones: pasar tal cual (CURRENT_TIMESTAMP, etc.)
    return d


def collect_schema(cur):
    """Devuelve schema: {tabla: {cols, pk, autoincrement, indexes, fks}}"""
    tables = {}
    for (name,) in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall():
        cols = []
        pk_cols = []
        for cid, cname, ctype, notnull, dflt, pk in cur.execute(
            f"PRAGMA table_info(`{name}`)").fetchall():
            cols.append({"name": cname, "type": ctype, "notnull": bool(notnull),
                         "default": dflt, "pk": pk})
            if pk:
                pk_cols.append((pk, cname))
        pk_cols.sort()
        # Detectar AUTOINCREMENT en el SQL de creación
        (sql,) = cur.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (name,)).fetchone()
        autoincrement = bool(sql and "AUTOINCREMENT" in sql.upper())
        # Índices
        indexes = []
        for _seq, iname, unique, origin, _partial in cur.execute(
            f"PRAGMA index_list(`{name}`)").fetchall():
            if origin == "pk":
                continue
            cols_idx = [r[2] for r in cur.execute(
                f"PRAGMA index_info(`{iname}`)").fetchall()]
            indexes.append({"name": iname, "unique": bool(unique),
                            "columns": cols_idx})
        # FKs
        fks = []
        for row in cur.execute(f"PRAGMA foreign_key_list(`{name}`)").fetchall():
            fks.append({"column": row[3], "ref_table": row[2],
                        "ref_column": row[4], "on_delete": row[6],
                        "on_update": row[5]})
        tables[name] = {"cols": cols, "pk": [c for _, c in pk_cols],
                        "autoincrement": autoincrement,
                        "indexes": indexes, "fks": fks}
    return tables


def write_dump(out, cur, tables):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    out.write("-- ========================================================\n")
    out.write("-- Portal de Alumnos - Dump MySQL (phpMyAdmin compatible)\n")
    out.write(f"-- Generado: {now} desde SQLite (backend/instance/portal.db)\n")
    out.write("-- Contiene datos sensibles (hashes de contraseña y config SMTP).\n")
    out.write("-- ========================================================\n")
    out.write("SET NAMES utf8mb4;\n")
    out.write("SET FOREIGN_KEY_CHECKS = 0;\n")
    out.write("SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';\n\n")

    for table, meta in tables.items():
        cols = meta["cols"]
        # --- CREATE TABLE ---
        out.write(f"-- ----------------------------------------------------\n")
        out.write(f"-- Tabla: `{table}`\n")
        out.write(f"-- ----------------------------------------------------\n")
        out.write(f"DROP TABLE IF EXISTS `{table}`;\n")
        out.write(f"CREATE TABLE `{table}` (\n")
        lines = []
        for c in cols:
            t = sqlite_type_to_mysql(c["type"], table, c["name"])
            parts = [f"`{c['name']}` {t}"]
            # SQLite: INTEGER PRIMARY KEY = rowid implícito (auto-increment).
            # En MySQL eso es AUTO_INCREMENT, aunque el DDL no diga AUTOINCREMENT.
            is_int_pk = c["pk"] and len(meta["pk"]) == 1 and (
                (c["type"] or "").upper().startswith("INT"))
            if is_int_pk:
                parts.append("NOT NULL AUTO_INCREMENT")
            else:
                if c["notnull"]:
                    parts.append("NOT NULL")
                dflt = esc_default(c["default"])
                if dflt is not None:
                    parts.append(f"DEFAULT {dflt}")
            lines.append("  " + " ".join(parts))
        if meta["pk"]:
            if not (len(meta["pk"]) == 1 and
                    any(c["pk"] and (c["type"] or "").upper().startswith("INT")
                        for c in cols)):
                lines.append("  PRIMARY KEY (`" + "`, `".join(meta["pk"]) + "`)")
        # FKs inline
        for fk in meta["fks"]:
            on_del = FK_ACTIONS.get(fk["on_delete"] or "NO ACTION", "RESTRICT")
            on_up = FK_ACTIONS.get(fk["on_update"] or "NO ACTION", "RESTRICT")
            lines.append(
                f"  CONSTRAINT `fk_{table}_{fk['column']}` FOREIGN KEY "
                f"(`{fk['column']}`) REFERENCES `{fk['ref_table']}` "
                f"(`{fk['ref_column']}`) ON DELETE {on_del} ON UPDATE {on_up}")
        out.write(",\n".join(lines))
        out.write("\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 "
                  "COLLATE=utf8mb4_unicode_ci;\n\n")

        # --- Índices únicos (no PK) ---
        for idx in meta["indexes"]:
            idx_sql = (f"CREATE {'UNIQUE ' if idx['unique'] else ''}INDEX "
                       f"`{idx['name']}` ON `{table}` "
                       f"(`" + "`, `".join(idx["columns"]) + "`);\n")
            out.write(idx_sql)
        if meta["indexes"]:
            out.write("\n")

        # --- INSERTs ---
        rows = cur.execute(f"SELECT * FROM `{table}`").fetchall()
        if rows:
            colnames = ", ".join(f"`{c['name']}`" for c in cols)
            batch = []
            for r in rows:
                vals = ", ".join(esc(v) for v in r)
                batch.append(f"({vals})")
            # Insertar en bloques razonables para phpMyAdmin
            for i in range(0, len(batch), 500):
                chunk = batch[i:i + 500]
                out.write(f"INSERT INTO `{table}` ({colnames}) VALUES\n")
                out.write(",\n".join(chunk))
                out.write(";\n")
            out.write("\n")

        # --- Restaurar AUTO_INCREMENT (tablas con PK entera = rowid sqlite) ---
        pk_is_int = (len(meta["pk"]) == 1 and any(
            c["pk"] and (c["type"] or "").upper().startswith("INT")
            for c in cols))
        if pk_is_int and rows:
            pk = meta["pk"][0]
            max_id = max(r[cols.index(next(c for c in cols if c["name"] == pk))]
                         for r in rows if r[cols.index(
                             next(c for c in cols if c["name"] == pk))] is not None) or 0
            out.write(f"ALTER TABLE `{table}` AUTO_INCREMENT = {max_id + 1};\n\n")

    out.write("SET FOREIGN_KEY_CHECKS = 1;\n")
    out.write("-- Fin del dump --\n")


def main():
    salida = "portal_mysql.sql"
    if len(sys.argv) > 1 and sys.argv[1] == "--salida":
        salida = sys.argv[2]
    if not os.path.exists(DB_PATH):
        print(f"NO existe la base: {DB_PATH}")
        return 1

    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    cur = con.cursor()
    tables = collect_schema(cur)

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), salida)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        write_dump(f, cur, tables)

    # Verificación de conteos
    print(f"Dump generado: {out_path}")
    total_rows = 0
    for table in tables:
        n = cur.execute(f"SELECT COUNT(*) FROM `{table}`").fetchone()[0]
        total_rows += n
        print(f"  {table}: {n} filas")
    print(f"Total: {total_rows} filas en {len(tables)} tablas")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())