from pathlib import Path
import re
import sys
from tempfile import NamedTemporaryFile

import pandas as pd
import pdfplumber



projeto = Path(__file__).resolve().parent.parent

# Permite reutilizar a conferência também com `python src/ler_pdf.py`.
if __package__ in (None, ""):
    sys.path.insert(0, str(projeto))

from analise.conferir_csv import conferir_relatorio, ler_csv
from src.status_importacao import registrar_resultado


pasta_pdfs = projeto / "dados" / "originais"


meses = [
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
]


def extrair_pdf(arquivo_pdf):
    """Extrai os valores diários de um PDF e devolve uma tabela."""

    
    registros = []

    
    with pdfplumber.open(arquivo_pdf) as pdf:
        texto = "\n".join(
            pagina.extract_text() or ""
            for pagina in pdf.pages
        )

    periodo = re.search(
        r"PER[IÍ]ODO\s+DE\s+(\d{2}/\d{2}/\d{4})\s+[ÀÁA]\s+"
        r"(\d{2}/\d{2}/\d{4})",
        texto,
        flags=re.IGNORECASE,
    )
    if not periodo:
        raise ValueError(
            f"Revise {arquivo_pdf.name}: período ausente ou ilegível no cabeçalho."
        )

    try:
        inicio, fim = (
            pd.to_datetime(data, format="%d/%m/%Y")
            for data in periodo.groups()
        )
    except ValueError as erro:
        raise ValueError(
            f"Revise {arquivo_pdf.name}: data inválida no período do cabeçalho."
        ) from erro

    if inicio > fim or inicio.year != fim.year:
        raise ValueError(
            f"Revise {arquivo_pdf.name}: o período deve estar em ordem "
            "e pertencer a um único ano."
        )

    ano = inicio.year

    
    for linha in texto.splitlines():
        resultado_dia = re.match(r"^\s*(\d{2})\s+", linha)

        
        if not resultado_dia:
            continue

        dia = int(resultado_dia.group(1))

        
        valores = re.findall(r"\d[\d.]*,\d{2}", linha)

        
        if len(valores) != 12:
            continue

        
        valores = [
            float(valor.replace(".", "").replace(",", "."))
            for valor in valores
        ]

        
        for numero_mes, valor in enumerate(valores, start=1):
            data = pd.to_datetime(
                f"{ano}-{numero_mes:02d}-{dia:02d}",
                errors="coerce",
            )

            
            if pd.notna(data) and inicio <= data <= fim:
                registros.append(
                    {
                        "data": data,
                        "ano": ano,
                        "mes": numero_mes,
                        "dia": dia,
                        "faturamento": valor,
                    }
                )

    if not registros:
        raise ValueError(
            f"Revise {arquivo_pdf.name}: nenhum dado extraído dentro do período."
        )

    return pd.DataFrame(registros)


def importar():
    arquivos_pdf = sorted(pasta_pdfs.glob("faturamento_*.pdf"))

    if not arquivos_pdf:
        raise FileNotFoundError(
            f"Nenhum PDF encontrado na pasta: {pasta_pdfs}"
        )

    tabelas = []

    for arquivo_pdf in arquivos_pdf:
        print(f"Lendo: {arquivo_pdf.name}")

        tabela = extrair_pdf(arquivo_pdf)
        tabelas.append(tabela)

    df = pd.concat(tabelas, ignore_index=True)
    df = df.sort_values("data")

    print("\nPrimeiras linhas:")
    print(df.head())

    print("\nFaturamento por ano:")
    print(df.groupby("ano")["faturamento"].sum().round(2))

    pasta_processados = projeto / "dados" / "processados"
    pasta_processados.mkdir(parents=True, exist_ok=True)

    arquivo_saida = pasta_processados / "faturamento_todos_anos.csv"
    # Valida o arquivo temporário antes de substituir o último CSV válido.
    with NamedTemporaryFile(
        dir=pasta_processados, suffix=".csv", delete=False
    ) as temporario:
        caminho_temporario = Path(temporario.name)
    try:
        df.to_csv(caminho_temporario, index=False, encoding="utf-8-sig")
        dados_conferencia = ler_csv(caminho_temporario)
        for arquivo_pdf in arquivos_pdf:
            try:
                erros, _ = conferir_relatorio(arquivo_pdf, dados_conferencia)
            except Exception as erro:
                raise ValueError(
                    f"Importação cancelada: {arquivo_pdf.name}: "
                    f"não foi possível conferir o relatório: {erro}. "
                    "O CSV anterior foi preservado."
                ) from erro
            if erros:
                raise ValueError(
                    f"Importação cancelada: {arquivo_pdf.name}: "
                    + "; ".join(erros)
                    + ". O CSV anterior foi preservado."
                )
            print(f"Conferido: {arquivo_pdf.name}")
        caminho_temporario.replace(arquivo_saida)
    finally:
        caminho_temporario.unlink(missing_ok=True)

    print(f"\nArquivo salvo em: {arquivo_saida}")


def main():
    caminho_status = projeto / "dados/processados/status_importacao.json"
    try:
        importar()
    except Exception as erro:
        try:
            registrar_resultado(caminho_status, sucesso=False, detalhe=str(erro))
        except OSError as erro_status:
            print(f"Não foi possível registrar a falha: {erro_status}", file=sys.stderr)
        raise
    else:
        try:
            registrar_resultado(caminho_status, sucesso=True)
        except OSError as erro:
            raise OSError(
                f"O CSV foi atualizado, mas não foi possível registrar o status: {erro}"
            ) from erro


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        raise SystemExit(1)
