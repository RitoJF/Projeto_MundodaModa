from pathlib import Path
import pandas as pd



projeto = Path(__file__).resolve().parent.parent


arquivo_csv = (
    projeto
    / "dados"
    / "processados"
    / "faturamento_todos_anos.csv"
)


df = pd.read_csv(arquivo_csv, parse_dates=["data"])


print("Primeiras linhas:")
print(df.head())


print("\nInformações da tabela:")
df.info()


print("\nFaturamento por ano:")
print(df.groupby("ano")["faturamento"].sum().round(2))