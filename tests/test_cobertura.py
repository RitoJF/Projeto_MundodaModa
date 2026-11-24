from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd
from streamlit.testing.v1 import AppTest

from dashboard.cobertura import resumir_periodos


def base(inicio, fim):
    datas = pd.date_range(inicio, fim)
    return pd.DataFrame({
        "data": datas, "ano": datas.year, "mes": datas.month,
        "dia": datas.day, "faturamento": 0.0,
    })


class CoberturaTest(unittest.TestCase):
    def test_mes_trimestre_e_ano_parciais(self):
        dados = base("2026-01-01", "2026-08-01")
        mensal = resumir_periodos(dados, "M")
        self.assertEqual(list(mensal.index.month), list(range(1, 9)))
        self.assertTrue(mensal.iloc[:7]["completo"].all())
        self.assertFalse(mensal.iloc[-1]["completo"])
        self.assertEqual(mensal.iloc[-1]["dias_cobertos"], 1)
        trimestral = resumir_periodos(dados, "Q")
        self.assertEqual(list(trimestral["completo"]), [True, True, False])
        self.assertFalse(resumir_periodos(dados, "Y").iloc[0]["completo"])

    def test_ano_bissexto_completo_com_zeros(self):
        dados = base("2024-01-01", "2024-12-31")
        self.assertTrue(resumir_periodos(dados, "Y").iloc[0]["completo"])
        fevereiro = resumir_periodos(dados, "M").iloc[1]
        self.assertTrue(fevereiro["completo"])
        self.assertEqual(fevereiro["dias_cobertos"], 29)

    def test_lacuna_nao_e_compensada_por_duplicata(self):
        dados = base("2025-01-01", "2025-12-31")
        dados = pd.concat([dados.iloc[1:], dados.iloc[1:2]])
        self.assertFalse(resumir_periodos(dados, "M").iloc[0]["completo"])
        self.assertFalse(resumir_periodos(dados, "Q").iloc[0]["completo"])
        self.assertFalse(resumir_periodos(dados, "Y").iloc[0]["completo"])

    def test_relatorio_com_inicio_no_meio_do_ano(self):
        resumo = resumir_periodos(base("2027-05-15", "2027-06-30"), "M")
        self.assertEqual(list(resumo.index.month), [5, 6])
        self.assertEqual(list(resumo["completo"]), [False, True])

    def executar_painel(self, dados):
        graficos = []

        def capturar(figura, **kwargs):
            eixo = figura.axes[0]
            graficos.append({
                "rotulos": [rotulo.get_text() for rotulo in eixo.get_xticklabels()],
                "linhas": [list(linha.get_ydata()) for linha in eixo.lines],
            })

        with (
            patch("pandas.read_csv", return_value=dados),
            patch("streamlit.pyplot", side_effect=capturar),
        ):
            app = AppTest.from_file(str(Path("dashboard/app.py").resolve())).run(timeout=30)
        self.assertFalse(app.exception)
        return app, graficos

    def test_painel_identifica_parciais_e_compara_apenas_meses_completos(self):
        dados = pd.concat([
            base("2025-01-01", "2025-12-31"),
            base("2026-01-01", "2026-08-01"),
        ])
        app, graficos = self.executar_painel(dados)
        self.assertIn("01/08/2026 (ano parcial; 213 dias cobertos)", app.info[0].value)
        self.assertEqual(app.selectbox[1].options[-1], "Agosto")
        self.assertEqual(graficos[0]["rotulos"][-1], "Agosto (parcial)")
        self.assertEqual(graficos[1]["rotulos"][-1], "3º trimestre (parcial)")
        self.assertTrue(all(pd.isna(v) for v in graficos[2]["linhas"][-1][7:]))
        self.assertIn("anos completos (2025)", app.info[-1].value)

    def test_nova_cobertura_atualiza_filtros_e_sazonalidade(self):
        app, graficos = self.executar_painel(base("2027-01-01", "2027-09-01"))
        self.assertEqual(app.selectbox[0].value, 2027)
        self.assertEqual(app.selectbox[1].options[-1], "Setembro")
        self.assertEqual(graficos[0]["rotulos"][-1], "Setembro (parcial)")
        self.assertTrue(any("anos completos" in aviso.value for aviso in app.warning))
        app, graficos = self.executar_painel(base("2027-01-01", "2027-12-31"))
        self.assertIn("ano completo; 365 dias", app.info[0].value)
        self.assertEqual(app.selectbox[1].options[-1], "Dezembro")
        self.assertEqual(graficos[1]["rotulos"][-1], "4º trimestre")
        self.assertIn("anos completos (2027)", app.info[-1].value)


if __name__ == "__main__":
    unittest.main()
