import pandas as pd


def resumir_periodos(df, frequencia):
    """Soma os valores e verifica a presença de cada dia do período."""
    resumo = df.groupby(df["data"].dt.to_period(frequencia)).agg(
        faturamento=("faturamento", "sum"),
        inicio=("data", "min"),
        fim=("data", "max"),
        dias_cobertos=("data", "nunique"),
    )
    dias_esperados = (
        resumo.index.end_time.normalize() - resumo.index.start_time
    ).days + 1
    resumo["completo"] = resumo["dias_cobertos"].to_numpy() == dias_esperados
    return resumo
