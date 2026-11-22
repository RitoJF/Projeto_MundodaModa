from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import pandas as pd
import streamlit as st



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

    [data-testid="stAlert"] {
        background-color: #1d2928;
        border: 1px solid #31534b;
        color: #d8f3e7;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


plt.rcParams.update(
    {
        "figure.facecolor": "#0e1117",
        "axes.facecolor": "#0e1117",
        "axes.edgecolor": "#454754",
        "axes.labelcolor": "#c7cad3",
        "text.color": "#f1f3f8",
        "xtick.color": "#c7cad3",
        "ytick.color": "#c7cad3",
        "grid.color": "#30323c",
        "legend.facecolor": "#20222b",
        "legend.edgecolor": "#3a3c48",
    }
)


projeto = Path(__file__).resolve().parent.parent
arquivo_csv = (
    projeto
    / "dados"
    / "processados"
    / "faturamento_todos_anos.csv"
)


df = pd.read_csv(arquivo_csv, parse_dates=["data"])

nomes_meses = [
    "Janeiro", "Fevereiro", "Março", "Abril",
    "Maio", "Junho", "Julho", "Agosto",
    "Setembro", "Outubro", "Novembro", "Dezembro",
]


ultimo_mes_disponivel_por_ano = {2026: 7}


def formatar_reais(valor):
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )



def formatar_eixo_reais(valor, posicao):
    return f"R$ {valor:,.0f}".replace(",", ".")



st.markdown(
    '<h1 class="dashboard-title">Faturamento da loja Mundo da Moda</h1>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="dashboard-subtitle">Acompanhamento anual e mensal do faturamento da loja</p>',
    unsafe_allow_html=True,
)


anos_disponiveis = sorted(df["ano"].unique())
indice_ano_inicial = (
    anos_disponiveis.index(2026)
    if 2026 in anos_disponiveis
    else len(anos_disponiveis) - 1
)
ano_selecionado = st.sidebar.selectbox(
    "Selecione o ano",
    anos_disponiveis,
    index=indice_ano_inicial,
)

mes_selecionado_nome = st.sidebar.selectbox(
    "Mês para análise diária",
    nomes_meses,
)
mes_selecionado = nomes_meses.index(mes_selecionado_nome) + 1

df_ano = df[df["ano"] == ano_selecionado]


faturamento_mensal = (
    df_ano.groupby("mes")["faturamento"]
    .sum()
    .reindex(range(1, 13), fill_value=0)
)


if ano_selecionado in ultimo_mes_disponivel_por_ano:
    ultimo_mes = ultimo_mes_disponivel_por_ano[ano_selecionado]
    faturamento_mensal = faturamento_mensal.loc[1:ultimo_mes]
    st.info("Os dados de 2026 estão disponíveis de janeiro a julho.")


faturamento_total = faturamento_mensal.sum()
media_mensal = faturamento_mensal.mean()
melhor_mes_numero = faturamento_mensal.idxmax()
melhor_mes_nome = nomes_meses[melhor_mes_numero - 1]

coluna1, coluna2, coluna3 = st.columns(3)

coluna1.metric(
    "Faturamento no período",
    formatar_reais(faturamento_total),
)

coluna2.metric(
    "Média mensal no período",
    formatar_reais(media_mensal),
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

    fig_mensal, ax_mensal = plt.subplots(figsize=(9, 5))

    ax_mensal.bar(
        faturamento_mensal.index,
        faturamento_mensal.values,
        color="#6C63FF",
    )
    ax_mensal.set_xticks(faturamento_mensal.index)
    ax_mensal.set_xticklabels(
        [nomes_meses[numero - 1] for numero in faturamento_mensal.index],
        rotation=35,
        ha="right",
    )
    ax_mensal.yaxis.set_major_formatter(
        FuncFormatter(formatar_eixo_reais)
    )
    ax_mensal.set_ylabel("Faturamento")
    ax_mensal.grid(axis="y", alpha=0.25)
    fig_mensal.tight_layout()

    st.pyplot(fig_mensal, use_container_width=True)
    plt.close(fig_mensal)


with coluna_trimestral:
    st.subheader("Faturamento por trimestre")

    faturamento_trimestral = (
        df_ano.assign(trimestre=df_ano["data"].dt.quarter)
        .groupby("trimestre")["faturamento"]
        .sum()
        .reindex(range(1, 5), fill_value=0)
    )

    if ano_selecionado in ultimo_mes_disponivel_por_ano:
        ultimo_trimestre = (ultimo_mes_disponivel_por_ano[ano_selecionado] - 1) // 3 + 1
        faturamento_trimestral = faturamento_trimestral.loc[1:ultimo_trimestre]

    nomes_trimestres = [
        f"{numero}º trimestre"
        for numero in faturamento_trimestral.index
    ]

    if ano_selecionado in ultimo_mes_disponivel_por_ano:
        nomes_trimestres[-1] += " *"

    fig_trimestral, ax_trimestral = plt.subplots(figsize=(9, 5))

    ax_trimestral.bar(
        faturamento_trimestral.index,
        faturamento_trimestral.values,
        color="#35A178",
    )
    ax_trimestral.set_xticks(faturamento_trimestral.index)
    ax_trimestral.set_xticklabels(nomes_trimestres)
    ax_trimestral.yaxis.set_major_formatter(
        FuncFormatter(formatar_eixo_reais)
    )
    ax_trimestral.set_ylabel("Faturamento")
    ax_trimestral.grid(axis="y", alpha=0.25)
    fig_trimestral.tight_layout()

    st.pyplot(fig_trimestral, use_container_width=True)
    plt.close(fig_trimestral)

    if ano_selecionado in ultimo_mes_disponivel_por_ano:
        st.caption("* Terceiro trimestre parcial: inclui somente julho.")

st.divider()


st.subheader("Comparação mensal entre os anos")

faturamento_por_ano_mes = (
    df.groupby(["ano", "mes"], as_index=False)["faturamento"]
    .sum()
)

fig_comparacao, ax_comparacao = plt.subplots(figsize=(12, 5))

for ano, dados_ano in faturamento_por_ano_mes.groupby("ano"):
    dados_ano = dados_ano.sort_values("mes")

    
    if ano in ultimo_mes_disponivel_por_ano:
        ultimo_mes = ultimo_mes_disponivel_por_ano[ano]
        dados_ano = dados_ano[dados_ano["mes"] <= ultimo_mes]

    ax_comparacao.plot(
        dados_ano["mes"],
        dados_ano["faturamento"],
        marker="o",
        linewidth=2,
        label=str(ano),
    )

ax_comparacao.set_xticks(range(1, 13))
ax_comparacao.set_xticklabels(nomes_meses, rotation=35, ha="right")
ax_comparacao.yaxis.set_major_formatter(
    FuncFormatter(formatar_eixo_reais)
)
ax_comparacao.set_ylabel("Faturamento")
ax_comparacao.grid(alpha=0.25)
ax_comparacao.legend(title="Ano")
fig_comparacao.tight_layout()

st.pyplot(fig_comparacao, use_container_width=True)
plt.close(fig_comparacao)

st.caption(
    "A linha de 2026 mostra somente janeiro a julho, conforme os dados disponíveis."
)

st.divider()


st.subheader(f"Faturamento por dia de {mes_selecionado_nome.lower()}")
dados_mes = df[df["mes"] == mes_selecionado].copy()


for ano_parcial, ultimo_mes in ultimo_mes_disponivel_por_ano.items():
    if mes_selecionado > ultimo_mes:
        dados_mes = dados_mes[dados_mes["ano"] != ano_parcial]

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

    fig_dias, ax_dias = plt.subplots(figsize=(12, 4.5))
    ax_dias.bar(media_por_dia.index, media_por_dia.values, color=cores_dias)
    ax_dias.set_title("Média de faturamento por dia do mês nos anos disponíveis")
    ax_dias.set_xlabel("Dia do mês")
    ax_dias.set_ylabel("Faturamento médio")
    ax_dias.set_xticks(media_por_dia.index)
    ax_dias.yaxis.set_major_formatter(FuncFormatter(formatar_eixo_reais))
    ax_dias.grid(axis="y", alpha=0.25)
    fig_dias.tight_layout()

    st.pyplot(fig_dias, use_container_width=True)
    plt.close(fig_dias)

    anos_usados = ", ".join(
        str(ano) for ano in sorted(dados_mes["ano"].unique())
    )
    st.caption(
        f"Maior média: dia {dia_maior_media} ({formatar_reais(media_por_dia.max())}). "
        f"Menor média: dia {dia_menor_media} ({formatar_reais(media_por_dia.min())}). "
        f"Anos considerados: {anos_usados}."
    )

st.divider()


st.subheader("Sazonalidade e planejamento de estoque")
df_anos_completos = df[~df["ano"].isin(ultimo_mes_disponivel_por_ano)]

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

    fig_sazonal, ax_sazonal = plt.subplots(figsize=(12, 4.5))
    ax_sazonal.bar(
        media_historica_mensal.index,
        media_historica_mensal.values,
        color=cores_sazonais,
    )
    ax_sazonal.set_title("Faturamento médio por mês nos anos completos")
    ax_sazonal.set_xlabel("Mês")
    ax_sazonal.set_ylabel("Faturamento médio")
    ax_sazonal.set_xticks(range(1, 13))
    ax_sazonal.set_xticklabels(nomes_meses, rotation=30, ha="right")
    ax_sazonal.yaxis.set_major_formatter(FuncFormatter(formatar_eixo_reais))
    ax_sazonal.grid(axis="y", alpha=0.25)
    fig_sazonal.tight_layout()

    st.pyplot(fig_sazonal, use_container_width=True)
    plt.close(fig_sazonal)

    anos_completos_usados = ", ".join(
        str(ano) for ano in sorted(df_anos_completos["ano"].unique())
    )
    mes_anterior_ao_pico = 12 if mes_pico == 1 else mes_pico - 1

    st.info(
        f"Nos anos completos ({anos_completos_usados}), "
        f"{nomes_meses[mes_pico - 1]} teve o maior faturamento médio "
        f"({formatar_reais(media_historica_mensal.max())}). "
        f"Vale planejar o reforço do estoque antes desse pico; "
        f"{nomes_meses[mes_anterior_ao_pico - 1]} pode ser um mês para iniciar esse planejamento, "
        "ajustando ao prazo de entrega do fornecedor e ao estoque atual. "
        "A análise usa faturamento como sinal de procura, não quantidade vendida ou margem."
    )
