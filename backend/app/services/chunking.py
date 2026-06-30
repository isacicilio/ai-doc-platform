# app/services/chunking.py
from app.config import settings


def _split_keeping_separators(text: str, separators: list[str]) -> list[str]:
    """
    Quebra o texto tentando os separadores na ordem dada (do mais "forte" pro
    mais "fraco"): primeiro parágrafos, depois quebras de linha, frases, e por
    fim espaços. Retorna as menores unidades que conseguimos isolar.
    """
    # Caso base: sem mais separadores pra tentar, devolve o texto como está.
    if not separators:
        return [text]

    sep = separators[0]
    resto = separators[1:]

    # Se o separador atual não existe no texto, pula pro próximo nível.
    if sep == "":
        # "" significa "quebre caractere a caractere" — último recurso.
        return list(text)
    if sep not in text:
        return _split_keeping_separators(text, resto)

    partes: list[str] = []
    for pedaco in text.split(sep):
        if not pedaco:
            continue
        # Se o pedaço ainda é grande demais, quebra mais fundo (recursão).
        if len(pedaco) > settings.chunk_size:
            partes.extend(_split_keeping_separators(pedaco, resto))
        else:
            partes.append(pedaco)
    return partes


def chunk_text(text: str) -> list[str]:
    """
    Divide um texto em chunks de até chunk_size caracteres, com chunk_overlap
    de sobreposição entre chunks vizinhos, respeitando fronteiras naturais
    (parágrafos > linhas > frases > palavras).
    """
    text = text.strip()
    if not text:
        return []

    # Ordem dos separadores: do mais semântico (parágrafo) ao mais cru (char).
    separators = ["\n\n", "\n", ". ", " ", ""]
    unidades = _split_keeping_separators(text, separators)

    chunks: list[str] = []
    atual = ""

    for unidade in unidades:
        # Cabe no chunk atual? Then acumula (com um espaço de junção).
        if len(atual) + len(unidade) + 1 <= settings.chunk_size:
            atual = f"{atual} {unidade}".strip()
        else:
            # Não cabe: fecha o chunk atual e começa um novo.
            if atual:
                chunks.append(atual)
            # O novo chunk começa com o overlap (cauda do chunk anterior) +
            # a unidade atual, pra não perder contexto na fronteira.
            if chunks and settings.chunk_overlap > 0:
                cauda = chunks[-1][-settings.chunk_overlap:]
                atual = f"{cauda} {unidade}".strip()
            else:
                atual = unidade

    # Não esquece o último chunk acumulado.
    if atual:
        chunks.append(atual)

    return chunks