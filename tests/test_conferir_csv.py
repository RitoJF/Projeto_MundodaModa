from contextlib import redirect_stdout
from decimal import Decimal
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from analise import conferir_csv


def texto_pdf():
    return (
        "PERÍODO DE 01/01/2026 À 01/02/2026\n"
        "01 " + " ".join(["0,00"] * 12) + "\n"
        + " ".join(["0,30", "0,20"] + ["0,00"] * 10)
        + "\nTOTAL GERAL: 0,50\n"
    )


def pdf_simulado(texto):
    pdf = MagicMock()
    pdf.__enter__.return_value.pages = [
        MagicMock(extract_text=MagicMock(return_value=texto))
    ]
    return pdf


def dados_csv():
    datas = pd.date_range("2026-01-01", "2026-02-01")
    valores = [Decimal("0.00")] * len(datas)
    valores[0], valores[1], valores[-1] = map(Decimal, ["0.10", "0.20", "0.20"])
    return pd.DataFrame({"data": datas, "faturamento": valores})


class ConferenciaTest(unittest.TestCase):
    def conferir(self, dados):
        with patch.object(
            conferir_csv.pdfplumber, "open",
            return_value=pdf_simulado(texto_pdf()),
        ):
            return conferir_csv.conferir_relatorio(Path("faturamento_2026.pdf"), dados)[0]

    def test_soma_exata_com_mes_parcial_e_meses_sem_cobertura(self):
        self.assertEqual(self.conferir(dados_csv()), [])

    def test_deslocamento_entre_meses_com_total_inalterado(self):
        dados = dados_csv()
        dados.loc[0, "faturamento"] += Decimal("0.01")
        dados.loc[len(dados) - 1, "faturamento"] -= Decimal("0.01")
        erros = self.conferir(dados)
        self.assertEqual(len(erros), 2)
        self.assertIn("janeiro: esperado R$ 0,30; calculado R$ 0,31", erros)
        self.assertIn("fevereiro: esperado R$ 0,20; calculado R$ 0,19", erros)

    def test_divergencia_de_um_centavo_no_total_geral(self):
        dados = dados_csv()
        dados.loc[0, "faturamento"] += Decimal("0.01")
        self.assertIn(
            "total geral: esperado R$ 0,50; calculado R$ 0,51", self.conferir(dados)
        )

    def test_referencias_ausentes_ilegíveis_ou_ambiguas(self):
        original = texto_pdf()
        for texto in (
            original.replace("TOTAL GERAL: 0,50", ""),
            original.replace("TOTAL GERAL: 0,50", "TOTAL GERAL: ilegível"),
            original.replace("0,30 0,20", "ilegível 0,20"),
            original.replace("PERÍODO DE", ""),
            original + "TOTAL GERAL: 0,50\n",
        ):
            with self.subTest(texto=texto), patch.object(
                conferir_csv.pdfplumber, "open", return_value=pdf_simulado(texto)
            ):
                with self.assertRaises(ValueError):
                    conferir_csv.ler_referencias(Path("relatorio.pdf"))

    def test_datas_ausentes_duplicadas_ou_fora_da_cobertura(self):
        dados = dados_csv()
        fora = dados.copy()
        fora.loc[len(fora) - 1, "data"] = pd.Timestamp("2026-02-02")
        for alterado in (dados.iloc[1:], pd.concat([dados, dados.iloc[:1]]), fora):
            with self.subTest(dados=alterado):
                self.assertTrue(any("cobertura" in erro for erro in self.conferir(alterado)))

    def test_leitura_csv_preserva_centavos_e_rejeita_valores_invalidos(self):
        with TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "dados.csv"
            caminho.write_text("data,faturamento\n2026-01-01,1234.56\n")
            self.assertEqual(conferir_csv.ler_csv(caminho).iloc[0]["faturamento"], Decimal("1234.56"))
            for valor in ("0.001", "Infinity", "NaN", "ilegível"):
                with self.subTest(valor=valor):
                    caminho.write_text(f"data,faturamento\n2026-01-01,{valor}\n")
                    with self.assertRaises(ValueError):
                        conferir_csv.ler_csv(caminho)

    def test_comando_retorna_erro_e_identifica_pdf(self):
        with TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            pdf = raiz / "faturamento_2026.pdf"
            pdf.touch()
            csv = raiz / "dados.csv"
            dados_csv().to_csv(csv, index=False)
            for texto, esperado in (
                (texto_pdf(), 0),
                (texto_pdf().replace("TOTAL GERAL: 0,50", "TOTAL GERAL: 0,51"), 1),
                ("Sem referências", 1),
            ):
                saida = StringIO()
                with (
                    self.subTest(texto=texto),
                    patch.object(conferir_csv, "pasta_pdfs", raiz),
                    patch.object(conferir_csv, "arquivo_csv", csv),
                    patch.object(conferir_csv.pdfplumber, "open", return_value=pdf_simulado(texto)),
                    redirect_stdout(saida),
                ):
                    self.assertEqual(conferir_csv.main(), esperado)
                    self.assertIn(pdf.name, saida.getvalue())


if __name__ == "__main__":
    unittest.main()
