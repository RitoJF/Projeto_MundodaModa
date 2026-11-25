import altair as alt
import pandas as pd


def formatar_reais(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def aplicar_visual(grafico, titulo):
    return (
        grafico.properties(height=320, title=titulo, background="#0e1117")
        .configure_view(stroke="#454754")
        .configure_axis(
            labelColor="#c7cad3", titleColor="#c7cad3", gridColor="#30323c",
            domainColor="#454754", tickColor="#454754", labelFontSize=11,
        )
        .configure_title(color="#f1f3f8", fontSize=14, anchor="start")
        .configure_legend(labelColor="#c7cad3", titleColor="#c7cad3")
    )


def eixo_reais(titulo):
    return alt.Y(
        "faturamento:Q", title=titulo,
        axis=alt.Axis(labelExpr="'R$ ' + replace(format(datum.value, ',.0f'), /,/g, '.')"),
    )


def barras(rotulos, valores, cores, titulo="", titulo_y="Faturamento", contexto="", extras=None):
    dados = pd.DataFrame({
        "periodo": list(rotulos), "faturamento": list(valores),
        "cor": cores, "contexto": contexto,
    })
    dados["valor"] = dados["faturamento"].map(formatar_reais)
    tooltip = [
        alt.Tooltip("periodo:N", title="Período"),
        alt.Tooltip("valor:N", title=titulo_y),
        alt.Tooltip("contexto:N", title="Referência"),
    ]
    for nome, conteudo in (extras or {}).items():
        dados[nome] = list(conteudo)
        tooltip.append(alt.Tooltip(field=nome, type="quantitative", title=nome, format="d"))
    canais = dict(
        x=alt.X("periodo:N", sort=list(rotulos), title=None,
                axis=alt.Axis(labelAngle=-30, labelLimit=180, grid=False)),
        y=eixo_reais(titulo_y),
        color=alt.Color("cor:N", scale=None, legend=None),
        tooltip=tooltip,
    )
    grafico = alt.layer(
        alt.Chart().mark_bar().encode(**canais),
        # Um marcador no zero permite consultar barras sem altura.
        alt.Chart().transform_filter("datum.faturamento === 0")
        .mark_point(filled=True, opacity=0.75, size=90).encode(**canais),
        data=dados,
    )
    return aplicar_visual(grafico, titulo)


def linhas(dados, nomes_meses):
    dados = dados.copy()
    dados["periodo"] = dados["mes"].map(lambda mes: nomes_meses[mes - 1])
    dados["valor"] = dados["faturamento"].map(
        lambda valor: formatar_reais(valor) if pd.notna(valor) else "Sem mês completo"
    )
    grafico = alt.Chart(dados).mark_line(point=True).encode(
        x=alt.X("periodo:N", sort=nomes_meses, title=None,
                axis=alt.Axis(labelAngle=-30, grid=False)),
        y=eixo_reais("Faturamento"),
        color=alt.Color("ano:N", title="Ano",
                        scale=alt.Scale(range=["#5B8FF9", "#F59E0B", "#34D399", "#A78BFA"])),
        order="mes:Q",
        tooltip=[
            alt.Tooltip("ano:N", title="Ano"),
            alt.Tooltip("periodo:N", title="Mês completo"),
            alt.Tooltip("valor:N", title="Faturamento"),
        ],
    )
    return aplicar_visual(grafico, "")
