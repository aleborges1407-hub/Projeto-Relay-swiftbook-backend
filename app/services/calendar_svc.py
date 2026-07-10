def create_event(*args, **kwargs):
    return {
        "success": True,
        "message": "Evento criado"
    }


def get_events(*args, **kwargs):
    return []


def delete_event(*args, **kwargs):
    return {
        "success": True,
        "message": "Evento removido"
    }
