from pathlib import Path
import pandas as pd


# Localiza a pasta principal do projeto
projeto = Path(__file__).resolve().parent.parent

# Monta o caminho do CSV processado
arquivo_csv = (
    projeto
    / "dados"
    / "processados"
    / "faturamento_todos_anos.csv"
)

# Lê o CSV e converte a coluna "data" para datas
df = pd.read_csv(arquivo_csv, parse_dates=["data"])

# Mostra as primeiras linhas da tabela
print("Primeiras linhas:")
print(df.head())

# Mostra os tipos e a quantidade de dados em cada coluna
print("\nInformações da tabela:")
df.info()

# Soma o faturamento por ano
print("\nFaturamento por ano:")
print(df.groupby("ano")["faturamento"].sum().round(2))