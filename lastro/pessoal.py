"""Detecção de dado pessoal pelo formato dos valores (card LST-41): CPF, CNPJ, e-mail e telefone.

Não basta o nome da coluna: o Explorador olha uma amostra dos valores. Para não acusar código de produto,
CEP ou identificador numérico:
- CPF e CNPJ só contam com dígitos verificadores válidos;
- telefone exige DDD válido e o formato de celular (9 na frente, 11 dígitos) ou fixo (2 a 5, 10 dígitos);
- a coluna só é marcada se pelo menos 80% dos valores da amostra baterem.
Valores numéricos que perderam o zero à esquerda (CPF digitado como número) são completados antes da conta.
"""

from __future__ import annotations

import re

LIMIAR = 0.8
MIN_VALORES = 2
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
DDD_VALIDOS = {11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 24, 27, 28, 31, 32, 33, 34, 35, 37, 38, 41, 42, 43, 44, 45, 46,
               47, 48, 49, 51, 53, 54, 55, 61, 62, 63, 64, 65, 66, 67, 68, 69, 71, 73, 74, 75, 77, 79, 81, 82, 83, 84, 85,
               86, 87, 88, 89, 91, 92, 93, 94, 95, 96, 97, 98, 99}
NOMES = {"cpf": "CPF", "cnpj": "CNPJ", "email": "e-mail", "telefone": "telefone"}


def _digitos(v: str) -> str:
    return re.sub(r"\D", "", v)


def cpf_valido(v: str, numerico: bool = False) -> bool:
    d = _digitos(v)
    if numerico and 9 <= len(d) < 11:
        d = d.zfill(11)
    if len(d) != 11 or len(set(d)) == 1:
        return False
    for n in (9, 10):
        soma = sum(int(d[i]) * (n + 1 - i) for i in range(n))
        if (soma * 10 % 11) % 10 != int(d[n]):
            return False
    return True


def cnpj_valido(v: str, numerico: bool = False) -> bool:
    d = _digitos(v)
    if numerico and 12 <= len(d) < 14:
        d = d.zfill(14)
    if len(d) != 14 or len(set(d)) == 1:
        return False
    for n, pesos in ((12, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]), (13, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])):
        resto = sum(int(d[i]) * pesos[i] for i in range(n)) % 11
        if (0 if resto < 2 else 11 - resto) != int(d[n]):
            return False
    return True


def telefone_valido(v: str) -> bool:
    d = _digitos(v)
    if len(d) in (12, 13) and d.startswith("55"):
        d = d[2:]
    if len(d) not in (10, 11) or int(d[:2]) not in DDD_VALIDOS:
        return False
    return d[2] == "9" if len(d) == 11 else d[2] in "2345"


def email_valido(v: str) -> bool:
    return bool(EMAIL.match(v.strip()))


def detectar(valores: list, numerico: bool = False) -> str | None:
    """Tipo de dado pessoal da coluna ('cpf', 'cnpj', 'email', 'telefone') ou None."""
    vs = [str(v).strip() for v in valores if v is not None and str(v).strip()]
    if len(vs) < MIN_VALORES:
        return None
    if numerico:  # 12345678909.0 → 12345678909
        vs = [v.removesuffix(".0") for v in vs]
    testes = (("email", email_valido), ("cnpj", lambda v: cnpj_valido(v, numerico)),
              ("cpf", lambda v: cpf_valido(v, numerico)), ("telefone", telefone_valido))
    for tipo, ok in testes:
        if sum(1 for v in vs if ok(v)) >= LIMIAR * len(vs):
            return tipo
    return None


def aviso(colunas: dict[str, str]) -> list[str]:
    return [f"A coluna '{c}' parece ter {NOMES[t]}: ela ficou fora do painel." for c, t in colunas.items()]
