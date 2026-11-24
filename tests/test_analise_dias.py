from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd
from streamlit.testing.v1 import AppTest


class AnaliseDiasTest(unittest.TestCase):
    def test_mediana_contagem_zeros_e_filtro_de_ano(self):
        datas = pd.to_datetime([
            "2025-01-06", "2025-01-13",
            "2026-01-05", "2026-01-12", "2026-01-19",
        ])
        dados = pd.DataFrame({
            "data": datas, "ano": datas.year, "mes": datas.month,
            "dia": datas.day, "faturamento": [200., 400., 0., 10., 100.],
        })
        graficos = []

        def capturar(figura, **kwargs):
            eixo = figura.axes[0]
            graficos.append({
                "titulo": eixo.get_title(),
                "valores": [barra.get_height() for barra in eixo.patches],
            })

        with (
            patch("pandas.read_csv", return_value=dados),
            patch("streamlit.pyplot", side_effect=capturar),
        ):
            app = AppTest.from_file(str(Path("dashboard/app.py").resolve())).run(timeout=30)
            self.assertFalse(app.exception)
            tabela = app.dataframe[0].value
            self.assertEqual(tabela.iloc[0]["Dia da semana"], "Segunda-feira")
            self.assertEqual(tabela.iloc[0]["Mediana"], 10.)
            self.assertEqual(tabela.iloc[0]["Datas cobertas"], 3)
            self.assertEqual(tabela.iloc[0]["Dias com faturamento zero"], 1)
            self.assertTrue(tabela.iloc[1:]["Mediana"].isna().all())
            self.assertTrue(tabela.iloc[1:]["Datas cobertas"].eq(0).all())
            self.assertIn("Média histórica por dia do mês", app.subheader[3].value)
            self.assertTrue(any("Anos considerados: 2025, 2026" in c.value for c in app.caption))
            semanal = [g for g in graficos if "dia da semana" in g["titulo"]][-1]
            self.assertEqual(semanal["valores"], [10.])
            self.assertTrue(any("dias com faturamento zero" in c.value for c in app.caption))

            app.selectbox[0].select(2025).run(timeout=30)
            self.assertFalse(app.exception)
            tabela = app.dataframe[0].value
            self.assertEqual(tabela.iloc[0]["Mediana"], 300.)
            self.assertEqual(tabela.iloc[0]["Datas cobertas"], 2)
            self.assertEqual(tabela.iloc[0]["Dias com faturamento zero"], 0)
            semanal = [g for g in graficos if "dia da semana" in g["titulo"]][-1]
            self.assertIn("2025", semanal["titulo"])
            self.assertEqual(semanal["valores"], [300.])


if __name__ == "__main__":
    unittest.main()
