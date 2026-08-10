import re


def normalizar_telefone(raw_phone: str) -> str:
    """
    Normaliza número de telefone conforme PRD §6.3:
    Remove tudo que não é dígito. Se resultar em 10 ou 11 dígitos sem prefixo 55,
    adiciona o prefixo 55 (Brasil DDI).
    
    Exemplos:
    - "(85) 98812-4477" -> "5585988124477"
    - "8588124477"       -> "558588124477"
    - "+5585988124477"   -> "5585988124477"
    """
    if not raw_phone:
        return ""

    # Remove todos os caracteres não-dígitos
    digitos = re.sub(r"\D", "", str(raw_phone))

    # Se tiver 10 ou 11 dígitos e não começar com '55', adiciona '55'
    if len(digitos) in (10, 11) and not digitos.startswith("55"):
        digitos = f"55{digitos}"

    return digitos
