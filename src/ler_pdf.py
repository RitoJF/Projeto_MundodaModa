from pathlib import Path
import re

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

    
    resultado_ano = re.search(r"(20\d{2})", arquivo_pdf.stem)

    if not resultado_ano:
        print(f"Ano não encontrado no nome: {arquivo_pdf.name}")
        return pd.DataFrame()

    ano = int(resultado_ano.group(1))
    registros = []

    
    with pdfplumber.open(arquivo_pdf) as pdf:
        texto = "\n".join(
            pagina.extract_text() or ""
            for pagina in pdf.pages
        )

    
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

            
            if pd.notna(data):
                registros.append(
                    {
                        "data": data,
                        "ano": ano,
                        "mes": numero_mes,
                        "dia": dia,
                        "faturamento": valor,
                    }
                )

    return pd.DataFrame(registros)


arquivos_pdf = sorted(pasta_pdfs.glob("faturamento_*.pdf"))

if not arquivos_pdf:
    raise FileNotFoundError(
        f"Nenhum PDF encontrado na pasta: {pasta_pdfs}"
    )

tabelas = []

for arquivo_pdf in arquivos_pdf:
    print(f"Lendo: {arquivo_pdf.name}")

    tabela = extrair_pdf(arquivo_pdf)

    if not tabela.empty:
        tabelas.append(tabela)

if not tabelas:
    raise ValueError("Nenhum dado foi extraído dos PDFs.")

df = pd.concat(tabelas, ignore_index=True)
df = df.sort_values("data")


print("\nPrimeiras linhas:")
print(df.head())

print("\nFaturamento por ano:")
print(df.groupby("ano")["faturamento"].sum().round(2))

pasta_processados = projeto / "dados" / "processados"
pasta_processados.mkdir(parents=True, exist_ok=True)

arquivo_saida = pasta_processados / "faturamento_todos_anos.csv"
df.to_csv(arquivo_saida, index=False, encoding="utf-8-sig")

print(f"\nArquivo salvo em: {arquivo_saida}")