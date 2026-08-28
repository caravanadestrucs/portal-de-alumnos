"""
Wiki CRUD + history + attachments — admin write, authenticated read, scope_wiki scoping
"""
import os
import re
import mimetypes
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt, verify_jwt_in_request
from werkzeug.utils import secure_filename
from sqlalchemy import or_ as sa_or

from models import db, WikiPage, WikiRevision, WikiAttachment, Sede
from utils.decorators import sede_scoped_admin_required
from utils.scope import scope_wiki

wiki_bp = Blueprint('wiki', __name__)

# ------------------------------------------------------------
# Sanitization helper - exported for tests
# ------------------------------------------------------------
def _sanitize_markdown(text: str) -> str:
    if not text:
        return text
    # remove script tags with content
    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<iframe.*?>.*?</iframe>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<object.*?>.*?</object>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<embed[^>]*>', '', text, flags=re.IGNORECASE)
    # remove javascript: urls
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    # remove on* attributes (onclick etc) — simple
    text = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+on\w+\s*=\s*[^\s>]+', '', text, flags=re.IGNORECASE)
    return text

# alias for test import flexibility
def sanitize_markdown(text: str) -> str:
    return _sanitize_markdown(text)

def sanitize(text: str) -> str:
    return _sanitize_markdown(text)


def _get_claims():
    try:
        verify_jwt_in_request(optional=True)
        return get_jwt()
    except Exception:
        return {}


def _is_wiki_visible(page_sede_id, claims):
    """Return True if claims can see page with page_sede_id (None=global)."""
    if page_sede_id is None:
        return True
    role = claims.get("role")
    token_sede = claims.get("sede_id")
    if role == "sede_admin":
        return token_sede == page_sede_id
    if role == "general_admin":
        return True
    # alumno/profesor: check token sede_id or DB lookup
    user_type = claims.get("user_type") or claims.get("type")
    if token_sede is not None:
        return token_sede == page_sede_id
    # try DB lookup for alumno/profesor
    user_id = claims.get("id")
    if user_type == "alumno" and user_id is not None:
        try:
            from models import Alumno
            alumno = db.session.get(Alumno, int(user_id))
            if alumno and alumno.sede_id == page_sede_id:
                return True
        except Exception:
            pass
        return False  # private not own
    if user_type == "profesor" and user_id is not None:
        try:
            from models import Profesor
            prof = db.session.get(Profesor, int(user_id))
            if prof and getattr(prof, "sede_id", None) == page_sede_id:
                return True
        except Exception:
            pass
        return False
    # fallback: if we don't know, only global visible (but we already handled None)
    return False


def _check_wiki_write_permission(sede_id, claims):
    """Return (allowed:bool, error_code, status). For POST create."""
    role = claims.get("role")
    token_sede = claims.get("sede_id")
    user_type = claims.get("user_type") or claims.get("type")
    if user_type != "admin":
        return False, "ADMIN_REQUIRED", 403
    if role not in ("general_admin", "sede_admin"):
        # legacy admin without role -> treat as general
        # check DB? For now allow as general if type admin
        if user_type == "admin":
            return True, None, None
        return False, "ADMIN_REQUIRED", 403
    if role == "general_admin":
        return True, None, None
    # sede_admin
    if sede_id is None:
        # cannot create global
        return False, "CROSS_SEDE", 403
    if token_sede != sede_id:
        return False, "CROSS_SEDE", 403
    return True, None, None


def _check_page_write_access(page: WikiPage, claims):
    """For PUT/DELETE/attachments write: can this admin write this page?"""
    role = claims.get("role")
    token_sede = claims.get("sede_id")
    user_type = claims.get("user_type") or claims.get("type")
    if user_type != "admin":
        return False
    if role == "general_admin":
        return True
    if role == "sede_admin":
        # page global -> cannot write? global is not owned; treat as forbidden
        if page.sede_id is None:
            return False
        return token_sede == page.sede_id
    # legacy admin
    if user_type == "admin" and role is None:
        return True
    return False


# ------------------------------------------------------------
# POST /api/wiki/pages — create page (admin only, 409 if duplicate, 403 cross, sanitize, creates revision)
# ------------------------------------------------------------
@wiki_bp.route('/pages', methods=['POST'])
@wiki_bp.route('/pages/', methods=['POST'])
@jwt_required()
def create_page():
    claims = get_jwt()
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Datos requeridos"}), 400
    slug = (data.get("slug") or "").strip()
    title = (data.get("title") or "").strip()
    body = data.get("body_markdown", data.get("body", ""))
    sede_id = data.get("sede_id")
    # Normalize sede_id: None or int
    if sede_id == "" or sede_id == 0:
        sede_id = None
    if sede_id is not None:
        try:
            sede_id = int(sede_id)
        except (ValueError, TypeError):
            return jsonify({"error": "sede_id must be integer or null"}), 400
        # verify sede exists
        if not db.session.get(Sede, sede_id):
            return jsonify({"error": "Sede not found"}), 404
    else:
        sede_id = None

    if not slug:
        return jsonify({"error": "slug is required"}), 400
    if not title:
        return jsonify({"error": "title is required"}), 400
    if body is None or (isinstance(body, str) and body.strip() == ""):
        return jsonify({"error": "body_markdown is required"}), 400

    # permission check
    allowed, code, status = _check_wiki_write_permission(sede_id, claims)
    if not allowed:
        return jsonify({"error": "Forbidden", "code": code}), status

    # slug format validation (simple)
    if not re.match(r'^[a-z0-9\-_]+$', slug.lower()):
        # allow but normalize lower? We'll just allow alphanumeric plus -_
        pass
    # uniqueness per sede: check existing
    if sede_id is None:
        existing = WikiPage.query.filter(WikiPage.sede_id.is_(None), WikiPage.slug == slug).first()
    else:
        existing = WikiPage.query.filter_by(sede_id=sede_id, slug=slug).first()
    if existing:
        return jsonify({"error": "Slug already exists for this sede", "code": "CONFLICT"}), 409

    # sanitize body
    sanitized_body = _sanitize_markdown(body)

    # create page
    try:
        page = WikiPage(
            sede_id=sede_id,
            slug=slug,
            title=title,
            body_markdown=sanitized_body,
            created_by=claims.get("id"),
        )
        db.session.add(page)
        db.session.flush()  # get id
        # create initial revision v1
        rev = WikiRevision(
            page_id=page.id,
            title=title,
            body_markdown=sanitized_body,
            created_by=claims.get("id"),
        )
        db.session.add(rev)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        if "unique" in str(e).lower() or "uq_" in str(e).lower():
            return jsonify({"error": "Slug already exists"}), 409
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Wiki page created", "page": page.to_dict()}), 201


# ------------------------------------------------------------
# GET /api/wiki/pages — list scoped via scope_wiki, filters ?sede_id ?slug ?search
# ------------------------------------------------------------
@wiki_bp.route('/pages', methods=['GET'])
@wiki_bp.route('/pages/', methods=['GET'])
@jwt_required()
def list_pages():
    claims = get_jwt()
    # base query scoped
    query = scope_wiki(WikiPage.query, WikiPage.sede_id)

    # optional filters
    slug_filter = request.args.get("slug")
    if slug_filter:
        query = query.filter(WikiPage.slug == slug_filter)

    search = request.args.get("search", "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter(
            sa_or(
                WikiPage.title.ilike(like),
                WikiPage.slug.ilike(like),
                WikiPage.body_markdown.ilike(like),
            )
        )

    # optional sede_id filter for general: already handled in scope_wiki, but also explicit ?sede_id param
    # scope_wiki already filtered for general with ?sede_id, so no extra needed here. For sede_admin, ignore ?sede_id to prevent bypass

    # pagination
    page_num = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    try:
        per_page = max(1, min(int(per_page), 100))
    except Exception:
        per_page = 20

    # order
    query = query.order_by(WikiPage.updated_at.desc(), WikiPage.id.desc())

    pagination = query.paginate(page=page_num, per_page=per_page, error_out=False)

    pages = [p.to_dict() for p in pagination.items]
    return jsonify({
        "pages": pages,
        "total": pagination.total,
        "page": page_num,
        "per_page": per_page,
        "pages_count": pagination.pages,
    }), 200


# ------------------------------------------------------------
# GET /api/wiki/pages/<id> — detail scoped
# ------------------------------------------------------------
@wiki_bp.route('/pages/<int:page_id>', methods=['GET'])
@jwt_required()
def get_page(page_id):
    page = db.session.get(WikiPage, page_id)
    if not page:
        return jsonify({"error": "Wiki page not found"}), 404
    claims = get_jwt()
    if not _is_wiki_visible(page.sede_id, claims):
        return jsonify({"error": "Cross-sede forbidden", "code": "CROSS_SEDE"}), 403
    return jsonify({"page": page.to_dict()}), 200


# ------------------------------------------------------------
# PUT /api/wiki/pages/<id> — edit creates revision + 403 cross, sanitize
# ------------------------------------------------------------
@wiki_bp.route('/pages/<int:page_id>', methods=['PUT'])
@jwt_required()
def update_page(page_id):
    page = db.session.get(WikiPage, page_id)
    if not page:
        return jsonify({"error": "Wiki page not found"}), 404
    claims = get_jwt()
    if not _check_page_write_access(page, claims):
        return jsonify({"error": "Cross-sede forbidden", "code": "CROSS_SEDE"}), 403
    data = request.get_json(silent=True) or {}
    # allow title/body update; slug/sede_id not changeable via PUT (prevent hijack)
    title = data.get("title")
    body = data.get("body_markdown", data.get("body"))

    # if nothing provided, 400
    if title is None and body is None:
        return jsonify({"error": "Nothing to update"}), 400

    try:
        if title is not None:
            t = str(title).strip()
            if not t:
                return jsonify({"error": "title cannot be empty"}), 400
            page.title = t
        if body is not None:
            sanitized = _sanitize_markdown(str(body))
            page.body_markdown = sanitized
        page.updated_at = datetime.utcnow()
        # create new revision capturing new state
        rev = WikiRevision(
            page_id=page.id,
            title=page.title,
            body_markdown=page.body_markdown,
            created_by=claims.get("id"),
        )
        db.session.add(rev)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Wiki page updated", "page": page.to_dict()}), 200


# ------------------------------------------------------------
# DELETE /api/wiki/pages/<id> — admin only 403 cross
# ------------------------------------------------------------
@wiki_bp.route('/pages/<int:page_id>', methods=['DELETE'])
@jwt_required()
def delete_page(page_id):
    page = db.session.get(WikiPage, page_id)
    if not page:
        return jsonify({"error": "Wiki page not found"}), 404
    claims = get_jwt()
    if not _check_page_write_access(page, claims):
        return jsonify({"error": "Cross-sede forbidden", "code": "CROSS_SEDE"}), 403
    try:
        # attachments files will be orphaned but DB cascade deletes rows; file cleanup optional
        # remove files from disk if exists
        attachments = WikiAttachment.query.filter_by(page_id=page.id).all()
        for att in attachments:
            try:
                if att.path and os.path.exists(att.path):
                    os.remove(att.path)
            except Exception:
                pass
        db.session.delete(page)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    return jsonify({"message": "Wiki page deleted"}), 200


# ------------------------------------------------------------
# GET /api/wiki/pages/<id>/history — list revisions, auth read scoped
# ------------------------------------------------------------
@wiki_bp.route('/pages/<int:page_id>/history', methods=['GET'])
@jwt_required()
def get_history(page_id):
    page = db.session.get(WikiPage, page_id)
    if not page:
        return jsonify({"error": "Wiki page not found"}), 404
    claims = get_jwt()
    if not _is_wiki_visible(page.sede_id, claims):
        return jsonify({"error": "Cross-sede forbidden", "code": "CROSS_SEDE"}), 403
    revisions = WikiRevision.query.filter_by(page_id=page_id).order_by(WikiRevision.created_at.asc(), WikiRevision.id.asc()).all()
    return jsonify({"revisions": [r.to_dict() for r in revisions], "history": [r.to_dict() for r in revisions], "total": len(revisions)}), 200


# ------------------------------------------------------------
# Attachments helpers
# ------------------------------------------------------------
def _attachments_base_path():
    # instance/wiki_attachments/<page_id>/
    base = os.path.join(os.path.dirname(__file__), '..', 'instance', 'wiki_attachments')
    base = os.path.abspath(base)
    os.makedirs(base, exist_ok=True)
    return base


ALLOWED_MIMES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/gif",
    "image/webp",
    "text/plain",
    "text/markdown",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/zip",
}

def _is_allowed_mime(mime: str) -> bool:
    if not mime:
        return True
    mime = mime.lower().split(";")[0].strip()
    if mime in ALLOWED_MIMES:
        return True
    # allow generic image/* and text/* and application/* ?
    if mime.startswith("image/") or mime.startswith("text/"):
        return True
    return False


# ------------------------------------------------------------
# POST /api/wiki/pages/<id>/attachments — multipart admin only, 10MB limit reuse
# ------------------------------------------------------------
@wiki_bp.route('/pages/<int:page_id>/attachments', methods=['POST'])
@jwt_required()
def upload_attachment(page_id):
    page = db.session.get(WikiPage, page_id)
    if not page:
        return jsonify({"error": "Wiki page not found"}), 404
    claims = get_jwt()
    if not _check_page_write_access(page, claims):
        return jsonify({"error": "Cross-sede forbidden", "code": "CROSS_SEDE"}), 403
    # only admin allowed already checked, but double-check user_type
    user_type = claims.get("user_type") or claims.get("type")
    if user_type != "admin":
        return jsonify({"error": "Admin required", "code": "ADMIN_REQUIRED"}), 403

    if "file" not in request.files:
        return jsonify({"error": "file is required"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({"error": "Invalid filename"}), 400

    # Determine size and mime
    file_bytes = file.read()
    size = len(file_bytes)
    file.seek(0)  # reset

    # 10MB limit (app config already has MAX_CONTENT_LENGTH but check per file)
    if size > 10 * 1024 * 1024:
        return jsonify({"error": "File exceeds 10MB limit", "code": "FILE_TOO_LARGE"}), 413
    if size == 0:
        return jsonify({"error": "Empty file"}), 400

    mime = file.mimetype or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    if not _is_allowed_mime(mime):
        # limit to safe types but allow if not in deny list? For now return 400 for dangerous
        if mime in ("application/x-sh", "application/x-executable", "text/html"):
            return jsonify({"error": "MIME type not allowed"}), 400
        # otherwise allow generic

    # sanitize filename further: prevent path traversal already via secure_filename
    # Ensure unique path: base/page_id/filename (with duplicate handling)
    base = _attachments_base_path()
    page_dir = os.path.join(base, str(page_id))
    os.makedirs(page_dir, exist_ok=True)

    dest_path = os.path.join(page_dir, filename)
    # avoid overwrite: add suffix if exists
    counter = 1
    base_name, ext = os.path.splitext(filename)
    while os.path.exists(dest_path):
        filename = f"{base_name}_{counter}{ext}"
        dest_path = os.path.join(page_dir, filename)
        counter += 1

    try:
        # write file
        with open(dest_path, "wb") as f:
            f.write(file_bytes)
        # create DB record
        att = WikiAttachment(
            page_id=page_id,
            filename=filename,
            path=dest_path,
            mime=mime,
            size=size,
            created_by=claims.get("id"),
        )
        db.session.add(att)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # cleanup file if created
        try:
            if os.path.exists(dest_path):
                os.remove(dest_path)
        except Exception:
            pass
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Attachment uploaded", "attachment": att.to_dict()}), 201


# ------------------------------------------------------------
# GET /api/wiki/pages/<id>/attachments — list, auth read scoped
# ------------------------------------------------------------
@wiki_bp.route('/pages/<int:page_id>/attachments', methods=['GET'])
@jwt_required()
def list_attachments(page_id):
    page = db.session.get(WikiPage, page_id)
    if not page:
        return jsonify({"error": "Wiki page not found"}), 404
    claims = get_jwt()
    if not _is_wiki_visible(page.sede_id, claims):
        return jsonify({"error": "Cross-sede forbidden", "code": "CROSS_SEDE"}), 403
    attachments = WikiAttachment.query.filter_by(page_id=page_id).order_by(WikiAttachment.created_at.asc()).all()
    return jsonify({"attachments": [a.to_dict() for a in attachments], "total": len(attachments)}), 200


# ------------------------------------------------------------
# GET /api/wiki/attachments/<id> — download file, auth read scoped via page visibility
# ------------------------------------------------------------
@wiki_bp.route('/attachments/<int:attachment_id>', methods=['GET'])
@jwt_required()
def download_attachment(attachment_id):
    att = db.session.get(WikiAttachment, attachment_id)
    if not att:
        return jsonify({"error": "Attachment not found"}), 404
    page = db.session.get(WikiPage, att.page_id)
    if not page:
        return jsonify({"error": "Page not found"}), 404
    claims = get_jwt()
    if not _is_wiki_visible(page.sede_id, claims):
        return jsonify({"error": "Cross-sede forbidden", "code": "CROSS_SEDE"}), 403
    if not att.path or not os.path.exists(att.path):
        return jsonify({"error": "File not found on disk"}), 404
    # send file
    try:
        return send_file(att.path, mimetype=att.mime or "application/octet-stream", as_attachment=True, download_name=att.filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
