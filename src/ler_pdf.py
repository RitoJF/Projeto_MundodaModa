from pathlib import Path
import re
from tempfile import NamedTemporaryFile

import pandas as pd
import pdfplumber



projeto = Path(__file__).resolve().parent.parent


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


def main():
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
    # Substitui o CSV somente após concluir a extração e a gravação.
    with NamedTemporaryFile(
        dir=pasta_processados, suffix=".csv", delete=False
    ) as temporario:
        caminho_temporario = Path(temporario.name)
    try:
        df.to_csv(caminho_temporario, index=False, encoding="utf-8-sig")
        caminho_temporario.replace(arquivo_saida)
    finally:
        caminho_temporario.unlink(missing_ok=True)

    print(f"\nArquivo salvo em: {arquivo_saida}")


if __name__ == "__main__":
    main()
