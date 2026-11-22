from pathlib import Path
import re

import pandas as pd
import pdfplumber


# Encontra a pasta principal do projeto
projeto = Path(__file__).resolve().parent.parent

# Pasta onde estão os PDFs originais
pasta_pdfs = projeto / "dados" / "originais"

# Colunas mensais do relatório, na mesma ordem do PDF
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

    # Obtém o ano pelo nome do arquivo, por exemplo: faturamento_2023.pdf
    resultado_ano = re.search(r"(20\d{2})", arquivo_pdf.stem)

    if not resultado_ano:
        print(f"Ano não encontrado no nome: {arquivo_pdf.name}")
        return pd.DataFrame()

    ano = int(resultado_ano.group(1))
    registros = []

    # Lê o texto de todas as páginas do PDF
    with pdfplumber.open(arquivo_pdf) as pdf:
        texto = "\n".join(
            pagina.extract_text() or ""
            for pagina in pdf.pages
        )

    # Analisa cada linha extraída do PDF
    for linha in texto.splitlines():
        resultado_dia = re.match(r"^\s*(\d{2})\s+", linha)

        # Ignora cabeçalhos, totais e outras linhas que não começam com um dia
        if not resultado_dia:
            continue

        dia = int(resultado_dia.group(1))

        # Procura os valores monetários da linha
        valores = re.findall(r"\d[\d.]*,\d{2}", linha)

        # Cada dia deve ter 12 valores, um para cada mês
        if len(valores) != 12:
            continue

        # Converte valores como "1.156,94" para o número 1156.94
        valores = [
            float(valor.replace(".", "").replace(",", "."))
            for valor in valores
        ]

        # Associa cada valor ao mês correspondente
        for numero_mes, valor in enumerate(valores, start=1):
            data = pd.to_datetime(
                f"{ano}-{numero_mes:02d}-{dia:02d}",
                errors="coerce",
            )

            # Ignora datas inválidas, como 31 de abril
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


# Procura os PDFs com nomes como faturamento_2023.pdf
arquivos_pdf = sorted(pasta_pdfs.glob("faturamento_*.pdf"))

if not arquivos_pdf:
    raise FileNotFoundError(
        f"Nenhum PDF encontrado na pasta: {pasta_pdfs}"
    )

tabelas = []

# Processa cada PDF encontrado
for arquivo_pdf in arquivos_pdf:
    print(f"Lendo: {arquivo_pdf.name}")

    tabela = extrair_pdf(arquivo_pdf)

    if not tabela.empty:
        tabelas.append(tabela)

if not tabelas:
    raise ValueError("Nenhum dado foi extraído dos PDFs.")

# Junta os dados dos anos em uma única tabela
df = pd.concat(tabelas, ignore_index=True)
df = df.sort_values("data")

# Mostra uma amostra e os totais anuais
print("\nPrimeiras linhas:")
print(df.head())

print("\nFaturamento por ano:")
print(df.groupby("ano")["faturamento"].sum().round(2))

# Salva o resultado na pasta de dados processados
pasta_processados = projeto / "dados" / "processados"
pasta_processados.mkdir(parents=True, exist_ok=True)

arquivo_saida = pasta_processados / "faturamento_todos_anos.csv"
df.to_csv(arquivo_saida, index=False, encoding="utf-8-sig")

print(f"\nArquivo salvo em: {arquivo_saida}")