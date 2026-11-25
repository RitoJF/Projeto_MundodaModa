import json
from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd
from streamlit.testing.v1 import AppTest

from dashboard.graficos import barras, linhas


class GraficosInterativosTest(unittest.TestCase):
    def test_painel_emite_os_seis_graficos_com_hover(self):
        datas = pd.date_range("2025-01-01", "2026-08-01")
        dados = pd.DataFrame({
            "data": datas, "ano": datas.year, "mes": datas.month,
            "dia": datas.day, "faturamento": 0.,
        })
        with patch("pandas.read_csv", return_value=dados):
            app = AppTest.from_file(str(Path("dashboard/app.py").resolve())).run(timeout=30)
        self.assertFalse(app.exception)
        graficos = app.get("vega_lite_chart")
        self.assertEqual(len(graficos), 6)
        for elemento in graficos:
            spec = json.loads(elemento.proto.spec)
            camada = spec["layer"][0] if "layer" in spec else spec
            self.assertIn("valor", [t["field"] for t in camada["encoding"]["tooltip"]])
        mensal = json.loads(graficos[0].proto.spec)
        self.assertEqual(mensal["layer"][0]["encoding"]["x"]["sort"][-1], "Agosto (parcial)")

    def test_hover_mostra_reais_e_identifica_periodo_parcial(self):
        grafico = barras(
            ["Maio", "Agosto (parcial)"], [177493.89, 0], "#6C63FF", contexto="2026"
        )
        self.assertEqual(list(grafico.data["valor"]), ["R$ 177.493,89", "R$ 0,00"])
        self.assertEqual(grafico.data.iloc[1]["periodo"], "Agosto (parcial)")
        self.assertTrue(grafico.data["contexto"].eq("2026").all())
        spec = grafico.to_dict()
        for camada in spec["layer"]:
            self.assertIn("valor", [t["field"] for t in camada["encoding"]["tooltip"]])
        self.assertEqual(spec["layer"][1]["transform"][0]["filter"], "datum.faturamento === 0")
        self.assertEqual(spec["background"], "#0e1117")
        self.assertTrue(grafico.data["cor"].eq("#6C63FF").all())

    def test_hover_semanal_inclui_contagens(self):
        grafico = barras(
            ["Segunda-feira"], [10], "#5B8FF9", titulo_y="Faturamento mediano",
            contexto="2026", extras={"Datas cobertas": [3], "Dias com faturamento zero": [1]},
        )
        tooltip = grafico.to_dict()["layer"][0]["encoding"]["tooltip"]
        campos = [t["field"] for t in tooltip]
        self.assertIn("Datas cobertas", campos)
        self.assertIn("Dias com faturamento zero", campos)
        self.assertEqual(grafico.data.iloc[0]["Datas cobertas"], 3)
        self.assertEqual(grafico.data.iloc[0]["Dias com faturamento zero"], 1)

    def test_comparacao_preserva_lacunas_e_tooltip_com_ano(self):
        dados = pd.DataFrame({
            "ano": [2026, 2026, 2026], "mes": [1, 2, 3],
            "faturamento": [100.25, float("nan"), 0.],
        })
        grafico = linhas(dados, ["Janeiro", "Fevereiro", "Março"])
        self.assertTrue(pd.isna(grafico.data.iloc[1]["faturamento"]))
        self.assertEqual(grafico.data.iloc[0]["valor"], "R$ 100,25")
        self.assertEqual(grafico.data.iloc[2]["valor"], "R$ 0,00")
        spec = grafico.to_dict()
        self.assertEqual(spec["mark"]["type"], "line")
        self.assertTrue(spec["mark"]["point"])
        self.assertEqual([t["field"] for t in spec["encoding"]["tooltip"]], ["ano", "periodo", "valor"])

    def test_comparacao_sem_meses_completos_gera_spec_valida(self):
        dados = pd.DataFrame(columns=["ano", "mes", "faturamento"])
        linhas(dados, ["Janeiro"]).to_dict()


if __name__ == "__main__":
    unittest.main()
