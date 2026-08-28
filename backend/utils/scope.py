"""
scope helpers for sede multitenancy
"""
from flask import request
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from sqlalchemy import or_ as sa_or, false as sa_false
from models import db


def scope_by_sede(query, column):
    """
    Row-level filter by sede.

    - sede_admin: WHERE column == token.sede_id (enforced, no bypass)
    - general_admin: if ?sede_id param present, filter to that sede, else no filter (sees all)
    - fallback (no role / legacy admin token): treat as general_admin
    """
    try:
        verify_jwt_in_request()
        claims = get_jwt()
    except Exception:
        return query

    role = claims.get("role")
    sede_id = claims.get("sede_id")

    # sede_admin is strictly scoped
    if role == "sede_admin":
        # if sede_id missing, return empty (safety)
        if sede_id is None:
            return query.filter(sa_false())
        return query.filter(column == sede_id)

    # general_admin (or legacy admin without role) can optionally filter
    if role == "general_admin" or ((claims.get("user_type") or claims.get("type")) == "admin" and role is None):
        qs_sede = request.args.get("sede_id", type=int)
        if qs_sede is not None:
            return query.filter(column == qs_sede)
        return query

    # non-admin (alumno/profesor) — for admin-scoped routes this should not be called;
    # return query unchanged; callers will handle 403 via decorators
    return query


def scope_wiki(query, column):
    """
    Wiki visibility: global (NULL) + caller's sede.
    - sede_admin: global OR own sede
    - general_admin: global + all (or global + ?sede_id if filtered)
    - alumno/profesor: global + own sede (if sede_id on token), else just global
    Placeholder for Phase 3 — not used in PR1 but required for decorator scope.
    """
    try:
        verify_jwt_in_request()
        claims = get_jwt()
    except Exception:
        return query.filter(column.is_(None))

    role = claims.get("role")
    sede_id = claims.get("sede_id")

    if role == "sede_admin":
        if sede_id is None:
            return query.filter(column.is_(None))
        return query.filter(sa_or(column.is_(None), column == sede_id))

    if role == "general_admin" or ((claims.get("user_type") or claims.get("type")) == "admin" and role is None):
        qs_sede = request.args.get("sede_id", type=int)
        if qs_sede is not None:
            return query.filter(sa_or(column.is_(None), column == qs_sede))
        return query

    # alumno/profesor: try to show global + own sede if known
    # For PR1, alumno token has no sede_id, so just global
    if sede_id is not None:
        return query.filter(sa_or(column.is_(None), column == sede_id))
    return query.filter(column.is_(None))
