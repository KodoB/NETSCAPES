def formatear_tamano(total_bytes: int) -> str:
    """
    Convierte una cantidad de bytes al string más legible, escalando
    automáticamente la unidad:
      < 1 KB   -> B
      < 1 MB   -> KB
      < 1 GB   -> MB
      >= 1 GB  -> GB
    """
    if total_bytes < 1024:
        return f"{total_bytes} B"
    elif total_bytes < 1024 ** 2:
        return f"{total_bytes / 1024:.1f} KB"
    elif total_bytes < 1024 ** 3:
        return f"{total_bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{total_bytes / (1024 ** 3):.2f} GB"
