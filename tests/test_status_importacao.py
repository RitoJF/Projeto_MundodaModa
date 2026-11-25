from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import pandas as pd
from streamlit.testing.v1 import AppTest

from src import ler_pdf
from src.status_importacao import formatar_data, ler_status, registrar_resultado
from test_ler_pdf import simular_pdf


class StatusImportacaoTest(unittest.TestCase):
    def test_sucesso_falha_e_recuperacao_preservam_status_e_csv(self):
        texto = (
            "PERÍODO DE 01/01/2026 À 01/01/2026\n"
            "01 " + " ".join(["0,00"] * 12) + "\n"
            + " ".join(["0,00"] * 12) + "\nTOTAL GERAL: 0,00\n"
        )
        with TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            originais = raiz / "dados/originais"
            originais.mkdir(parents=True)
            (originais / "faturamento_2026.pdf").touch()
            caminho = raiz / "dados/processados/status_importacao.json"
            csv = caminho.with_name("faturamento_todos_anos.csv")
            with (
                patch.object(ler_pdf, "projeto", raiz),
                patch.object(ler_pdf, "pasta_pdfs", originais),
                patch.object(ler_pdf.pdfplumber, "open") as abrir,
                redirect_stdout(StringIO()),
            ):
                abrir.return_value = simular_pdf(texto)
                ler_pdf.main()
                valido = csv.read_bytes()
                sucesso = ler_status(caminho)
                abrir.return_value = simular_pdf(texto.replace("TOTAL GERAL: 0,00", "TOTAL GERAL: 0,01"))
                with self.assertRaises(ValueError):
                    ler_pdf.main()
                falha = ler_status(caminho)
                self.assertEqual(csv.read_bytes(), valido)
                self.assertEqual(falha["ultima_atualizacao_valida"], sucesso["ultima_atualizacao_valida"])
                self.assertEqual(falha["ultima_tentativa"]["resultado"], "falha")
                self.assertIn("faturamento_2026.pdf", falha["ultima_tentativa"]["detalhe"])
                abrir.return_value = simular_pdf(texto)
                ler_pdf.main()
                recuperado = ler_status(caminho)
                self.assertEqual(recuperado["ultima_tentativa"]["resultado"], "sucesso")
                self.assertIsNone(recuperado["ultima_tentativa"]["detalhe"])

    def test_primeira_falha_nao_inventa_atualizacao_valida(self):
        with TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            with (
                patch.object(ler_pdf, "projeto", raiz),
                patch.object(ler_pdf, "pasta_pdfs", raiz / "inexistente"),
            ):
                with self.assertRaises(FileNotFoundError):
                    ler_pdf.main()
            status = ler_status(raiz / "dados/processados/status_importacao.json")
            self.assertEqual(status["ultima_tentativa"]["resultado"], "falha")
            self.assertNotIn("ultima_atualizacao_valida", status)

    def test_status_corrompido_pode_ser_substituido(self):
        with TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "status.json"
            caminho.write_text("arquivo interrompido")
            registrar_resultado(caminho, sucesso=True)
            self.assertEqual(ler_status(caminho)["ultima_tentativa"]["resultado"], "sucesso")
            self.assertEqual(list(caminho.parent.iterdir()), [caminho])

    def test_data_convertida_para_campo_grande(self):
        self.assertEqual(formatar_data("2026-11-25T18:00:00+00:00"), "25/11/2026 às 14:00:00")

    def test_painel_exibe_falha_sem_detalhe_tecnico_e_remove_aviso_no_sucesso(self):
        status = {
            "ultima_tentativa": {
                "resultado": "falha", "data_hora": "2026-11-25T15:00:00-04:00",
                "detalhe": "TECNICO: faturamento_2026.pdf janeiro esperado 0,31",
            },
            "ultima_atualizacao_valida": "2026-11-24T14:00:00-04:00",
        }
        datas = pd.date_range("2026-01-01", "2026-01-02")
        dados = pd.DataFrame({
            "data": datas, "ano": datas.year, "mes": datas.month,
            "dia": datas.day, "faturamento": [0., 10.],
        })
        with (
            patch("src.status_importacao.ler_status", return_value=status),
            patch("pandas.read_csv", return_value=dados),
            patch("streamlit.altair_chart"),
        ):
            app = AppTest.from_file(str(Path("dashboard/app.py").resolve())).run(timeout=30)
            self.assertFalse(app.exception)
            self.assertTrue(any("Não foi possível atualizar" in v.value for v in app.warning))
            legendas = " ".join(v.value for v in app.caption)
            self.assertIn("última atualização válida foram mantidos", legendas)
            self.assertIn("24/11/2026 às 14:00:00", legendas)
            self.assertNotIn("TECNICO", legendas + " ".join(v.value for v in app.warning))
            status["ultima_tentativa"]["resultado"] = "sucesso"
            status["ultima_atualizacao_valida"] = "2026-11-25T15:30:00-04:00"
            app.run(timeout=30)
            self.assertFalse(app.exception)
            self.assertFalse(any("Não foi possível atualizar" in v.value for v in app.warning))
            self.assertTrue(any("25/11/2026 às 15:30:00" in v.value for v in app.caption))

    def test_painel_sem_csv_mostra_mensagem_e_para_sem_excecao(self):
        with (
            patch("src.status_importacao.ler_status", return_value={}),
            patch("pandas.read_csv", side_effect=FileNotFoundError),
        ):
            app = AppTest.from_file(str(Path("dashboard/app.py").resolve())).run(timeout=30)
        self.assertFalse(app.exception)
        self.assertIn("Ainda não há dados disponíveis", app.error[0].value)
        self.assertEqual(len(app.selectbox), 0)


if __name__ == "__main__":
    unittest.main()
