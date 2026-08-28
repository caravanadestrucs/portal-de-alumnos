# Wiki Manuals Specification

## Purpose
Sede-scoped markdown wiki; global NULL or private; revisions/attachments iterative.

## Requirements

### Requirement: Wiki Data Model and Sede Scoping
MUST provide `WikiPage(id,sede_id FK NULL,title,slug,body_markdown,created_by)` + `WikiRevision` + `WikiAttachment`; NULL=global; `scope_wiki` returns global+caller.

#### Scenario: Global visible
- GIVEN page NULL slug reg
- WHEN TEO and HUA list
- THEN both see it

#### Scenario: Private isolated
- GIVEN page TEO slug manual-teo
- WHEN HUA list
- THEN not contained

### Requirement: Access Control and Lifecycle
MUST allow write admin-only; read authenticated; POST/PUT create revision; history GET.

#### Scenario: Create revision
- GIVEN sede_admin TEO POST {sede_id:1,slug:guia,body:# Hola}
- WHEN created
- THEN 201 one revision

#### Scenario: Auth read
- GIVEN page exists alumno token GET
- WHEN request
- THEN 200; anon 401

#### Scenario: Cross-sede write 403
- GIVEN HUA page sede_admin TEO PUT
- WHEN request
- THEN 403

### Requirement: Slug Uniqueness and Attachments
MUST enforce UNIQUE(sede_id,slug) per sede; sanitize markdown; attachments multipart on disk; UI list/detail/edit/history.

#### Scenario: Duplicate per sede
- GIVEN TEO guia exists
- WHEN create guia TEO again
- THEN 409; HUA guia 201

#### Scenario: Attachment
- GIVEN page guia TEO upload manual.pdf
- WHEN POST attachments
- THEN 201 and GET lists it
