from pathlib import Path
import sys

import pandas as pd
import streamlit as st

projeto = Path(__file__).resolve().parent.parent
if str(projeto) not in sys.path:
    sys.path.insert(0, str(projeto))

from dashboard.cobertura import resumir_periodos
from dashboard.graficos import barras, formatar_reais, linhas
from src.status_importacao import formatar_data, ler_status



st.set_page_config(
    page_title="MundoModa | Faturamento",
    page_icon="👜",
    layout="wide",
)


st.markdown(
    """
    <style>
    :root {
        color-scheme: dark;
    }

    .stApp {
        background-color: #0e1117;
        color: #f1f3f8;
    }

    [data-testid="stHeader"] {
        background-color: #0e1117;
    }

    [data-testid="stSidebar"] {
        background-color: #22232d;
        border-right: 1px solid #30313b;
    }

    [data-testid="stSidebar"] > div:first-child {
        background-color: #22232d;
    }

    .block-container {
        max-width: 1500px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: #f4f5f8;
        letter-spacing: -0.02em;
    }

    h1 {
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .dashboard-title {
        text-align: center;
        font-family: "Segoe UI", "Trebuchet MS", Arial, sans-serif;
        font-size: 2.55rem;
        font-weight: 750;
        letter-spacing: -0.035em;
        padding-top: 0.25rem;
        margin-bottom: 0.25rem;
    }

    .dashboard-subtitle {
        text-align: center;
        color: #a4a8b5;
        font-size: 1rem;
        margin-top: 0;
        margin-bottom: 1.5rem;
    }

    [data-testid="stCaptionContainer"] {
        color: #a4a8b5;
    }

    [data-testid="stMetric"] {
        background: #252630;
        border: 1px solid #30323e;
        border-radius: 10px;
        padding: 18px 20px;
    }

    [data-testid="stMetricLabel"] {
        color: #b7bac5;
    }

    [data-testid="stMetricValue"] {
        color: #f7f8fa;
        font-weight: 700;
    }

    [data-testid="stMetricDelta"] {
        color: #68d391;
    }

    [data-testid="stSidebar"] label {
        color: #e4e6eb;
    }

    [data-baseweb="select"] > div {
        background-color: #181a22;
        border-color: #3a3c48;
        color: #f1f3f8;
    }

    hr {
        border-color: #2c2e38;
    }

    .stElementContainer:has([data-testid="stVegaLiteChart"])
    [data-testid="stElementToolbar"] {
        display: none;
    }

    [data-testid="stAlert"] {
        background-color: #1d2928;
        border: 1px solid #31534b;
        color: #d8f3e7;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


arquivo_csv = (
    projeto
    / "dados"
    / "processados"
    / "faturamento_todos_anos.csv"
)


try:
    df = pd.read_csv(arquivo_csv, parse_dates=["data"])
except FileNotFoundError:
    df = None

try:
    status_importacao = ler_status(projeto / "dados/processados/status_importacao.json")
    ultima_tentativa = status_importacao.get("ultima_tentativa", {})
    ultima_valida = status_importacao.get("ultima_atualizacao_valida")
    data_valida = formatar_data(ultima_valida) if ultima_valida else None
    if ultima_tentativa.get("resultado") == "falha":
        data_falha = formatar_data(ultima_tentativa["data_hora"])
        st.warning(f"Não foi possível atualizar os dados na tentativa de {data_falha}.")
        if df is not None:
            st.caption(
                "Os dados da última atualização válida foram mantidos. "
                + (f"Atualizados em {data_valida}." if data_valida else
                   "A data dessa atualização ainda não foi registrada.")
            )
    elif data_valida:
        st.caption(f"Última atualização válida: {data_valida} (horário de Campo Grande).")
except (OSError, ValueError, KeyError, TypeError, AttributeError):
    st.warning("Não foi possível consultar o status da atualização dos dados.")

if df is None:
    st.error("Ainda não há dados disponíveis. Aguarde uma atualização bem-sucedida.")
    st.stop()

nomes_meses = [
    "Janeiro", "Fevereiro", "Março", "Abril",
    "Maio", "Junho", "Julho", "Agosto",
    "Setembro", "Outubro", "Novembro", "Dezembro",
]


resumo_mensal = resumir_periodos(df, "M")
resumo_anual = resumir_periodos(df, "Y")


st.markdown(
    '<h1 class="dashboard-title">Faturamento da loja Mundo da Moda</h1>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="dashboard-subtitle">Acompanhamento anual e mensal do faturamento da loja</p>',
    unsafe_allow_html=True,
)


anos_disponiveis = sorted(df["ano"].unique())
indice_ano_inicial = len(anos_disponiveis) - 1
ano_selecionado = st.sidebar.selectbox(
    "Selecione o ano",
    anos_disponiveis,
    index=indice_ano_inicial,
)

df_ano = df[df["ano"] == ano_selecionado]
meses_ano = resumo_mensal[resumo_mensal.index.year == ano_selecionado]
meses_disponiveis = [nomes_meses[periodo.month - 1] for periodo in meses_ano.index]
mes_selecionado_nome = st.sidebar.selectbox(
    "Mês para análise diária",
    meses_disponiveis,
)
mes_selecionado = nomes_meses.index(mes_selecionado_nome) + 1

cobertura_ano = resumo_anual.loc[pd.Period(str(ano_selecionado), freq="Y")]
status_ano = "ano completo" if cobertura_ano["completo"] else "ano parcial"
st.info(
    f"Cobertura de {ano_selecionado}: "
    f"{cobertura_ano['inicio']:%d/%m/%Y} a {cobertura_ano['fim']:%d/%m/%Y} "
    f"({status_ano}; {cobertura_ano['dias_cobertos']} dias cobertos)."
)
st.caption("Períodos parciais incluem somente os dias cobertos pelos relatórios.")

faturamento_mensal = meses_ano.set_axis(meses_ano.index.month)["faturamento"]
rotulos_meses = [
    nomes_meses[periodo.month - 1] + (" (parcial)" if not linha["completo"] else "")
    for periodo, linha in meses_ano.iterrows()
]

faturamento_total = faturamento_mensal.sum()
media_mensal = meses_ano.loc[meses_ano["completo"], "faturamento"].mean()
melhor_mes_numero = faturamento_mensal.idxmax()
melhor_mes_nome = rotulos_meses[list(faturamento_mensal.index).index(melhor_mes_numero)]

coluna1, coluna2, coluna3 = st.columns(3)

coluna1.metric(
    "Faturamento no período",
    formatar_reais(faturamento_total),
)

coluna2.metric(
    "Média dos meses completos",
    formatar_reais(media_mensal) if pd.notna(media_mensal) else "Sem mês completo",
)

coluna3.metric(
    "Mês de maior faturamento",
    melhor_mes_nome,
    formatar_reais(faturamento_mensal.max()),
)

st.divider()


coluna_mensal, coluna_trimestral = st.columns(2)

with coluna_mensal:
    st.subheader("Faturamento por mês")

    st.altair_chart(
        barras(rotulos_meses, faturamento_mensal.values, "#6C63FF",
               contexto=str(ano_selecionado)),
        width="stretch", theme=None,
    )


with coluna_trimestral:
    st.subheader("Faturamento por trimestre")

    trimestres_ano = resumir_periodos(df_ano, "Q")
    faturamento_trimestral = trimestres_ano.set_axis(
        trimestres_ano.index.quarter
    )["faturamento"]
    nomes_trimestres = [
        f"{periodo.quarter}º trimestre" + (" (parcial)" if not linha["completo"] else "")
        for periodo, linha in trimestres_ano.iterrows()
    ]

    st.altair_chart(
        barras(nomes_trimestres, faturamento_trimestral.values, "#35A178",
               contexto=str(ano_selecionado)),
        width="stretch", theme=None,
    )


st.divider()


st.subheader("Comparação mensal entre os anos")

faturamento_por_ano_mes = resumo_mensal[resumo_mensal["completo"]].copy()
faturamento_por_ano_mes["ano"] = faturamento_por_ano_mes.index.year
faturamento_por_ano_mes["mes"] = faturamento_por_ano_mes.index.month

# Mantém lacunas em meses que não têm cobertura completa.
series_comparacao = []
for ano, dados_ano in faturamento_por_ano_mes.groupby("ano"):
    serie = dados_ano.set_index("mes").reindex(range(1, 13))
    serie["ano"] = ano
    series_comparacao.append(serie.reset_index())
dados_comparacao = (
    pd.concat(series_comparacao, ignore_index=True)
    if series_comparacao else pd.DataFrame(columns=["mes", "ano", "faturamento"])
)
st.altair_chart(linhas(dados_comparacao, nomes_meses), width="stretch", theme=None)

st.caption(
    "A comparação usa somente meses completos de cada ano. "
    "Meses parciais ou sem cobertura não entram nas linhas nem são tratados como zero."
)

st.divider()


st.subheader(f"Média histórica por dia do mês — {mes_selecionado_nome.lower()}")
dados_mes = df[df["mes"] == mes_selecionado].copy()


media_por_dia = dados_mes.groupby("dia")["faturamento"].mean().sort_index()

if media_por_dia.empty:
    st.warning("Não há dados disponíveis para esse mês.")
else:
    dia_maior_media = media_por_dia.idxmax()
    dia_menor_media = media_por_dia.idxmin()

    cores_dias = [
        "#34D399" if dia == dia_maior_media
        else "#F87171" if dia == dia_menor_media
        else "#5B8FF9"
        for dia in media_por_dia.index
    ]

    anos_usados = ", ".join(
        str(ano) for ano in sorted(dados_mes["ano"].unique())
    )
    st.altair_chart(
        barras(
            [str(dia) for dia in media_por_dia.index], media_por_dia.values, cores_dias,
            titulo="Média de faturamento por dia do mês nos anos disponíveis",
            titulo_y="Faturamento médio", contexto=f"Anos: {anos_usados}",
        ),
        width="stretch", theme=None,
    )

    st.caption(
        f"Maior média: dia {dia_maior_media} ({formatar_reais(media_por_dia.max())}). "
        f"Menor média: dia {dia_menor_media} ({formatar_reais(media_por_dia.min())}). "
        f"Anos considerados: {anos_usados}."
    )

st.divider()


st.subheader(f"Faturamento por dia da semana — {ano_selecionado}")
dias_semana = [
    "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira",
    "Sexta-feira", "Sábado", "Domingo",
]
resumo_semanal = (
    df_ano.groupby(df_ano["data"].dt.dayofweek)
    .agg(
        mediana=("faturamento", "median"),
        datas_cobertas=("data", "nunique"),
        dias_com_zero=("faturamento", lambda valores: valores.eq(0).sum()),
    )
    .reindex(range(7))
)
resumo_semanal[["datas_cobertas", "dias_com_zero"]] = (
    resumo_semanal[["datas_cobertas", "dias_com_zero"]].fillna(0).astype(int)
)
dias_com_dados = resumo_semanal[resumo_semanal["datas_cobertas"] > 0]

st.altair_chart(
    barras(
        [dias_semana[dia] for dia in dias_com_dados.index],
        dias_com_dados["mediana"].values, "#5B8FF9",
        titulo=f"Mediana de faturamento por dia da semana em {ano_selecionado}",
        titulo_y="Faturamento mediano", contexto=str(ano_selecionado),
        extras={
            "Datas cobertas": dias_com_dados["datas_cobertas"],
            "Dias com faturamento zero": dias_com_dados["dias_com_zero"],
        },
    ),
    width="stretch", theme=None,
)

tabela_semanal = resumo_semanal.set_axis(dias_semana).rename(columns={
    "mediana": "Mediana", "datas_cobertas": "Datas cobertas",
    "dias_com_zero": "Dias com faturamento zero",
}).rename_axis("Dia da semana").reset_index()
st.dataframe(
    tabela_semanal.style.format({"Mediana": formatar_reais}, na_rep="Sem dados"),
    hide_index=True,
)
st.caption(
    f"A análise usa todas as datas cobertas de {ano_selecionado}, "
    "incluindo dias com faturamento zero no cálculo da mediana. "
    "Dias da semana sem datas cobertas aparecem como sem dados. "
    "O filtro de mês se aplica ao gráfico histórico acima."
)

st.divider()


st.subheader("Sazonalidade e planejamento de estoque")
anos_completos = resumo_anual.index[resumo_anual["completo"]].year
df_anos_completos = df[df["ano"].isin(anos_completos)]

if df_anos_completos.empty:
    st.warning("São necessários dados de anos completos para analisar a sazonalidade.")
else:
    totais_mensais_anuais = (
        df_anos_completos.groupby(["ano", "mes"])["faturamento"]
        .sum()
        .reset_index()
    )
    media_historica_mensal = (
        totais_mensais_anuais.groupby("mes")["faturamento"]
        .mean()
        .reindex(range(1, 13), fill_value=0)
    )

    mes_pico = media_historica_mensal.idxmax()
    mes_menor = media_historica_mensal.idxmin()
    cores_sazonais = [
        "#34D399" if mes == mes_pico
        else "#F87171" if mes == mes_menor
        else "#6C63FF"
        for mes in media_historica_mensal.index
    ]

    anos_completos_usados = ", ".join(
        str(ano) for ano in sorted(df_anos_completos["ano"].unique())
    )
    st.altair_chart(
        barras(
            nomes_meses, media_historica_mensal.values, cores_sazonais,
            titulo="Faturamento médio por mês nos anos completos",
            titulo_y="Faturamento médio", contexto=f"Anos completos: {anos_completos_usados}",
        ),
        width="stretch", theme=None,
    )

    mes_anterior_ao_pico = 12 if mes_pico == 1 else mes_pico - 1

    st.info(
        f"Nos anos completos ({anos_completos_usados}), "
        f"{nomes_meses[mes_pico - 1]} teve o maior faturamento médio "
        f"({formatar_reais(media_historica_mensal.max())}). "
        f"Esse pico histórico serve de referência para programar uma revisão do estoque. "
        f"{nomes_meses[mes_anterior_ao_pico - 1]} pode ser um mês para essa revisão, "
        "antecipando-a conforme o prazo de entrega dos fornecedores. "
        "Para decidir quais produtos repor e em qual quantidade, consulte as vendas "
        "por produto, incluindo as quantidades vendidas, e o estoque disponível de cada item."
    )
