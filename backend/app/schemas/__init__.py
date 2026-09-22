from pydantic import ValidationError


def mensaje_de_error(exc: ValidationError, etiquetas: dict[str, str]) -> str:
    """Traduce los errores de Pydantic a un mensaje en castellano para mostrar en el formulario."""
    partes = []
    for err in exc.errors():
        campo = etiquetas.get(str(err["loc"][0]), str(err["loc"][0])) if err["loc"] else "Formulario"
        tipo = err["type"]
        if tipo in ("missing", "string_too_short"):
            partes.append(f"{campo}: es obligatorio.")
        elif tipo == "string_too_long":
            partes.append(f"{campo}: máximo {err['ctx']['max_length']} caracteres.")
        elif tipo in ("greater_than", "greater_than_equal"):
            partes.append(f"{campo}: tiene que ser mayor a {err['ctx'].get('gt', err['ctx'].get('ge'))}.")
        else:
            partes.append(f"{campo}: valor inválido.")
    return " ".join(partes)
