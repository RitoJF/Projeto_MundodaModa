from decimal import Decimal, InvalidOperation
from pathlib import Path
import re

import pandas as pd
import pdfplumber


projeto = Path(__file__).resolve().parent.parent
arquivo_csv = projeto / "dados/processados/faturamento_todos_anos.csv"
pasta_pdfs = projeto / "dados/originais"
meses = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]
valor_pdf = r"-?(?:\d{1,3}(?:\.\d{3})+|\d+),\d{2}"


def reais(valor):
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def ler_referencias(arquivo_pdf):
    """Lê o período e os totais impressos, sem recalcular as linhas diárias."""
    with pdfplumber.open(arquivo_pdf) as pdf:
        texto = "\n".join(pagina.extract_text() or "" for pagina in pdf.pages)

    periodo = re.search(
        r"PER[IÍ]ODO\s+DE\s+(\d{2}/\d{2}/\d{4})\s+[ÀÁA]\s+"
        r"(\d{2}/\d{2}/\d{4})", texto, flags=re.IGNORECASE,
    )
    if not periodo:
        raise ValueError("período ausente ou ilegível no cabeçalho")
    inicio, fim = (
        pd.to_datetime(data, format="%d/%m/%Y") for data in periodo.groups()
    )
    if inicio > fim or inicio.year != fim.year:
        raise ValueError("período inválido para um relatório anual")

    # A linha de totais contém somente os doze valores, sem o número do dia.
    linhas_mensais = [
        re.findall(valor_pdf, linha)
        for linha in texto.splitlines()
        if re.fullmatch(rf"\s*{valor_pdf}(?:\s+{valor_pdf}){{11}}\s*", linha)
    ]
    totais_gerais = re.findall(
        rf"^\s*TOTAL GERAL:\s*({valor_pdf})\s*$", texto,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if len(linhas_mensais) != 1:
        raise ValueError("totais mensais ausentes, ilegíveis ou ambíguos")
    if len(totais_gerais) != 1:
        raise ValueError("total geral ausente, ilegível ou ambíguo")

    mensais = [
        Decimal(valor.replace(".", "").replace(",", "."))
        for valor in linhas_mensais[0]
    ]
    geral = Decimal(totais_gerais[0].replace(".", "").replace(",", "."))
    return inicio, fim, mensais, geral


def ler_csv(caminho):
    df = pd.read_csv(caminho, parse_dates=["data"], dtype={"faturamento": str})
    # Lê diretamente como Decimal para evitar erros de soma de ponto flutuante.
    try:
        df["faturamento"] = df["faturamento"].map(Decimal)
        if not df["faturamento"].map(
            lambda valor: valor.is_finite() and valor == valor.quantize(Decimal("0.01"))
        ).all():
            raise ValueError("valores devem ser finitos e ter precisão de centavos")
    except (InvalidOperation, TypeError, ValueError) as erro:
        raise ValueError(f"Faturamento inválido no CSV: {erro}") from erro
    df["data"] = pd.to_datetime(df["data"], errors="raise")
    if df["data"].isna().any():
        raise ValueError("CSV contém datas ausentes")
    return df


def conferir_relatorio(arquivo_pdf, df):
    inicio, fim, mensais, geral = ler_referencias(arquivo_pdf)
    dados = df[df["data"].dt.year == inicio.year]
    erros = []
    datas_esperadas = pd.date_range(inicio, fim)
    if (dados["data"].duplicated().any()
            or set(dados["data"]) != set(datas_esperadas)):
        erros.append("datas do CSV não correspondem à cobertura do relatório")

    for mes, esperado in enumerate(mensais, start=1):
        calculado = sum(
            dados.loc[dados["data"].dt.month == mes, "faturamento"], Decimal("0")
        )
        if calculado != esperado:
            erros.append(
                f"{meses[mes - 1]}: esperado {reais(esperado)}; "
                f"calculado {reais(calculado)}"
            )
    calculado = sum(dados["faturamento"], Decimal("0"))
    if calculado != geral:
        erros.append(
            f"total geral: esperado {reais(geral)}; calculado {reais(calculado)}"
        )
    return erros, inicio.year


def main():
    arquivos = sorted(pasta_pdfs.glob("faturamento_*.pdf"))
    if not arquivos:
        print(f"ERRO: nenhum PDF encontrado em {pasta_pdfs}")
        return 1
    try:
        df = ler_csv(arquivo_csv)
    except (OSError, ValueError, KeyError) as erro:
        print(f"ERRO: {arquivo_csv.name}: {erro}")
        return 1

    falhou = False
    anos_conferidos = set()
    for arquivo in arquivos:
        try:
            erros, ano = conferir_relatorio(arquivo, df)
        except Exception as erro:
            # Falhas de leitura de um PDF não impedem conferir os demais.
            print(f"ERRO: {arquivo.name}: referência não pôde ser lida: {erro}")
            falhou = True
            continue
        anos_conferidos.add(ano)
        if erros:
            falhou = True
            for erro in erros:
                print(f"ERRO: {arquivo.name}: {erro}")
        else:
            print(f"OK: {arquivo.name}: 12 totais mensais e total geral conferem.")

    anos_sem_pdf = set(df["data"].dt.year) - anos_conferidos
    if anos_sem_pdf:
        print(f"ERRO: anos do CSV sem referência conferida: {sorted(anos_sem_pdf)}")
        falhou = True
    return 1 if falhou else 0


if __name__ == "__main__":
    raise SystemExit(main())
