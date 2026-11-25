from datetime import datetime
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from zoneinfo import ZoneInfo


fuso = ZoneInfo("America/Campo_Grande")


def ler_status(caminho):
    if not caminho.exists():
        return {}
    status = json.loads(caminho.read_text(encoding="utf-8"))
    if not isinstance(status, dict):
        raise ValueError("Formato inválido do status de importação")
    return status


def registrar_resultado(caminho, sucesso, detalhe=None):
    try:
        status = ler_status(caminho)
    except ValueError:
        status = {}

    agora = datetime.now(fuso).isoformat(timespec="seconds")
    status["ultima_tentativa"] = {
        "resultado": "sucesso" if sucesso else "falha",
        "data_hora": agora,
        "detalhe": detalhe,
    }
    if sucesso:
        status["ultima_atualizacao_valida"] = agora

    caminho.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=caminho.parent, suffix=".json", delete=False) as arquivo:
        temporario = Path(arquivo.name)
    try:
        temporario.write_text(
            json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        temporario.replace(caminho)
    finally:
        temporario.unlink(missing_ok=True)


def formatar_data(valor):
    data = datetime.fromisoformat(valor)
    if data.tzinfo is None:
        raise ValueError("O status não informa o fuso horário")
    return data.astimezone(fuso).strftime("%d/%m/%Y às %H:%M:%S")
