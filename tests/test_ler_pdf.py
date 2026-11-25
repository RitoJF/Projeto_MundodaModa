from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from src import ler_pdf


def simular_pdf(texto):
    pdf = MagicMock()
    pdf.__enter__.return_value.pages = [
        MagicMock(extract_text=MagicMock(return_value=texto))
    ]
    return pdf


def linha(dia, valor="0,00"):
    return f"{dia:02d} " + " ".join([valor] * 12)


class ExtracaoTest(unittest.TestCase):
    def extrair(self, texto):
        with patch.object(ler_pdf.pdfplumber, "open", return_value=simular_pdf(texto)):
            return ler_pdf.extrair_pdf(Path("faturamento_1999.pdf"))

    def test_periodo_inclusivo_com_zeros_e_ano_do_cabecalho(self):
        df = self.extrair(
            "PERÍODO DE 15/02/2024 À 02/03/2024\n"
            + "\n".join(linha(dia) for dia in range(1, 32))
        )
        self.assertEqual(
            list(df.sort_values("data")["data"]),
            list(pd.date_range("2024-02-15", "2024-03-02")),
        )
        self.assertTrue(df["faturamento"].eq(0).all())
        self.assertTrue(df["ano"].eq(2024).all())

    def test_cabecalhos_invalidos_identificam_arquivo(self):
        for cabecalho in (
            "Sem cabeçalho",
            "PERÍODO DE ??/01/2026 À 01/08/2026",
            "PERÍODO DE 31/02/2026 À 01/08/2026",
            "PERÍODO DE 02/08/2026 À 01/08/2026",
            "PERÍODO DE 01/01/2025 À 01/08/2026",
        ):
            with self.subTest(cabecalho=cabecalho):
                with self.assertRaisesRegex(ValueError, "faturamento_1999.pdf"):
                    self.extrair(cabecalho + "\n" + linha(1))

    def test_sem_dados_no_periodo_identifica_arquivo(self):
        with self.assertRaisesRegex(ValueError, "faturamento_1999.pdf"):
            self.extrair("PERÍODO DE 01/01/2026 À 01/08/2026")

    def test_erro_em_segundo_pdf_preserva_csv(self):
        with TemporaryDirectory() as pasta:
            projeto = Path(pasta)
            originais = projeto / "dados/originais"
            originais.mkdir(parents=True)
            for ano in (2025, 2026):
                (originais / f"faturamento_{ano}.pdf").touch()
            saida = projeto / "dados/processados/faturamento_todos_anos.csv"
            saida.parent.mkdir(parents=True)
            saida.write_bytes(b"ultimo csv valido\n")
            documentos = [
                simular_pdf("PERÍODO DE 01/01/2025 À 31/12/2025\n" + linha(1)),
                simular_pdf("Cabeçalho ilegível\n" + linha(1)),
            ]
            with (
                patch.object(ler_pdf, "projeto", projeto),
                patch.object(ler_pdf, "pasta_pdfs", originais),
                patch.object(ler_pdf.pdfplumber, "open", side_effect=documentos),
                redirect_stdout(StringIO()),
            ):
                with self.assertRaisesRegex(ValueError, "faturamento_2026.pdf"):
                    ler_pdf.main()
            self.assertEqual(saida.read_bytes(), b"ultimo csv valido\n")

    def test_falha_de_gravacao_preserva_csv_e_remove_temporario(self):
        with TemporaryDirectory() as pasta:
            projeto = Path(pasta)
            originais = projeto / "dados/originais"
            originais.mkdir(parents=True)
            (originais / "faturamento_2026.pdf").touch()
            saida = projeto / "dados/processados/faturamento_todos_anos.csv"
            saida.parent.mkdir(parents=True)
            saida.write_bytes(b"ultimo csv valido\n")
            with (
                patch.object(ler_pdf, "projeto", projeto),
                patch.object(ler_pdf, "pasta_pdfs", originais),
                patch.object(
                    ler_pdf.pdfplumber, "open",
                    return_value=simular_pdf(
                        "PERÍODO DE 01/01/2026 À 01/08/2026\n" + linha(1)
                    ),
                ),
                patch.object(pd.DataFrame, "to_csv", side_effect=OSError("disco cheio")),
                redirect_stdout(StringIO()),
            ):
                with self.assertRaises(OSError):
                    ler_pdf.main()
            self.assertEqual(saida.read_bytes(), b"ultimo csv valido\n")
            self.assertEqual(
                set(saida.parent.iterdir()),
                {saida, saida.parent / "status_importacao.json"},
            )


class ValidacaoImportacaoTest(unittest.TestCase):
    def executar_importacao(self, texto, erro_esperado=None):
        with TemporaryDirectory() as pasta:
            projeto = Path(pasta)
            originais = projeto / "dados/originais"
            originais.mkdir(parents=True)
            (originais / "faturamento_2026.pdf").touch()
            saida = projeto / "dados/processados/faturamento_todos_anos.csv"
            saida.parent.mkdir(parents=True)
            anterior = b"ultimo csv valido\n"
            saida.write_bytes(anterior)
            with (
                patch.object(ler_pdf, "projeto", projeto),
                patch.object(ler_pdf, "pasta_pdfs", originais),
                patch.object(ler_pdf.pdfplumber, "open", return_value=simular_pdf(texto)),
                redirect_stdout(StringIO()),
            ):
                if erro_esperado:
                    with self.assertRaisesRegex(ValueError, erro_esperado) as erro:
                        ler_pdf.main()
                    self.assertIn("faturamento_2026.pdf", str(erro.exception))
                    self.assertIn("CSV anterior foi preservado", str(erro.exception))
                    self.assertEqual(saida.read_bytes(), anterior)
                else:
                    ler_pdf.main()
                    df = pd.read_csv(saida)
                    self.assertEqual(len(df), 2)
                    self.assertEqual(list(df["faturamento"]), [0.10, 0.20])
                self.assertEqual(
                    set(saida.parent.iterdir()),
                    {saida, saida.parent / "status_importacao.json"},
                )

    def relatorio(self):
        return (
            "PERÍODO DE 01/01/2026 À 02/01/2026\n"
            "01 0,10 " + " ".join(["0,00"] * 11) + "\n"
            "02 0,20 " + " ".join(["0,00"] * 11) + "\n"
            "0,30 " + " ".join(["0,00"] * 11) + "\n"
            "TOTAL GERAL: 0,30\n"
        )

    def test_csv_validado_substitui_anterior(self):
        self.executar_importacao(self.relatorio())

    def test_divergencia_mensal_preserva_csv(self):
        self.executar_importacao(
            self.relatorio().replace("0,30 0,00", "0,31 0,00"),
            r"janeiro: esperado R\$ 0,31; calculado R\$ 0,30",
        )

    def test_divergencia_geral_preserva_csv(self):
        self.executar_importacao(
            self.relatorio().replace("TOTAL GERAL: 0,30", "TOTAL GERAL: 0,31"),
            r"total geral: esperado R\$ 0,31; calculado R\$ 0,30",
        )

    def test_dia_zero_ausente_preserva_csv_mesmo_com_totais_corretos(self):
        texto = self.relatorio().replace("02/01/2026", "03/01/2026")
        self.executar_importacao(texto, "datas do CSV não correspondem")

    def test_dia_duplicado_preserva_csv(self):
        texto = self.relatorio().replace("TOTAL GERAL:", linha(1) + "\nTOTAL GERAL:")
        self.executar_importacao(texto, "datas do CSV não correspondem")

    def test_total_ilegivel_preserva_csv(self):
        self.executar_importacao(
            self.relatorio().replace("TOTAL GERAL: 0,30", "TOTAL GERAL: ilegível"),
            "total geral ausente, ilegível ou ambíguo",
        )


if __name__ == "__main__":
    unittest.main()
