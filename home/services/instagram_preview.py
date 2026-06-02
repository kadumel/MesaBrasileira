from home.utils.link_preview import baixar_para_imagefield, buscar_miniatura


def aplicar_miniatura_instagram(
    instance,
    url: str,
    *,
    url_field: str = "thumbnail_url",
    image_field: str = "thumbnail",
    guardar_ficheiro: bool = True,
) -> bool:
    """
    Preenche url_field e opcionalmente image_field com a miniatura do link.
    Devolve True se encontrou imagem.
    """
    thumb_url = buscar_miniatura(url)
    if not thumb_url:
        return False

    setattr(instance, url_field, thumb_url)

    if guardar_ficheiro:
        try:
            baixar_para_imagefield(instance, image_field, thumb_url)
        except Exception:
            pass

    return True
