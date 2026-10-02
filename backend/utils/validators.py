"""Domain validators for sede-scoped rules (Slice 1 Task 6)."""


class SameSedeError(ValueError):
    pass


def validate_same_sede(profesor, grupo):
    ps = getattr(profesor, 'sede_id', None)
    gs = getattr(grupo, 'sede_id', None)
    if ps is None or gs is None or int(ps) != int(gs):
        raise SameSedeError(f"profesor sede {ps} != grupo sede {gs}")
    return True
