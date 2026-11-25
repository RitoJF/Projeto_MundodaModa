from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import pandas as pd

from src import ler_pdf
from src.status_importacao import ler_status
from test_ler_pdf import linha, simular_pdf


def relatorio(inicio, fim, dias):
    return (
        f"PERÍODO DE {inicio} À {fim}\n"
        + "\n".join(linha(dia) for dia in dias)
        + "\n" + " ".join(["0,00"] * 12)
        + "\nTOTAL GERAL: 0,00\n"
    )


class SobreposicaoTest(unittest.TestCase):
    def test_bloqueia_copias_intervalos_contidos_e_limite_comum(self):
        for inicio, fim, conflito in (
            ("01/01/2026", "05/01/2026", "01/01/2026 a 05/01/2026"),
            ("02/01/2026", "03/01/2026", "02/01/2026 a 03/01/2026"),
            ("05/01/2026", "07/01/2026", "05/01/2026 a 05/01/2026"),
        ):
            with self.subTest(inicio=inicio, fim=fim):
                periodos = [
                    (pd.to_datetime(inicio, dayfirst=True), pd.to_datetime(fim, dayfirst=True), Path("novo.pdf")),
                    (pd.Timestamp("2026-01-01"), pd.Timestamp("2026-01-05"), Path("antigo.pdf")),
                ]
                with self.assertRaises(ValueError) as erro:
                    ler_pdf.validar_sobreposicao(periodos)
                self.assertIn("antigo.pdf", str(erro.exception))
                self.assertIn("novo.pdf", str(erro.exception))
                self.assertIn(conflito, str(erro.exception))

    def test_periodos_adjacentes_nao_tem_sobreposicao(self):
        ler_pdf.validar_sobreposicao([
            (pd.Timestamp("2026-08-01"), pd.Timestamp("2026-08-31"), Path("agosto.pdf")),
            (pd.Timestamp("2026-01-01"), pd.Timestamp("2026-07-31"), Path("janeiro_julho.pdf")),
        ])

    def test_importacao_bloqueia_pelo_cabecalho_mesmo_com_datas_ausentes(self):
        # Nenhuma linha extraída se repete, mas os dois cabeçalhos cobrem 03/01.
        documentos = {
            "faturamento_2026_a.pdf": relatorio("01/01/2026", "03/01/2026", [1, 2]),
            "faturamento_2026_b.pdf": relatorio("03/01/2026", "04/01/2026", [4]),
        }
        self.verificar_importacao(documentos, sobreposicao=True)

    def test_importacao_bloqueia_relatorio_duplicado_com_todos_os_valores_zero(self):
        texto = relatorio("01/01/2026", "02/01/2026", [1, 2])
        self.verificar_importacao({
            "faturamento_2026.pdf": texto,
            "faturamento_2026_copia.pdf": texto,
        }, sobreposicao=True)

    def test_anos_distintos_importam_normalmente(self):
        self.verificar_importacao({
            f"faturamento_{ano}.pdf": relatorio(f"01/01/{ano}", f"02/01/{ano}", [1, 2])
            for ano in (2025, 2026)
        }, sobreposicao=False)

    def verificar_importacao(self, documentos, sobreposicao):
        with TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            originais = raiz / "dados/originais"
            originais.mkdir(parents=True)
            for nome in documentos:
                (originais / nome).touch()
            csv = raiz / "dados/processados/faturamento_todos_anos.csv"
            csv.parent.mkdir(parents=True)
            anterior = b"ultimo csv valido\n"
            csv.write_bytes(anterior)

            def abrir(caminho):
                return simular_pdf(documentos[caminho.name])

            with (
                patch.object(ler_pdf, "projeto", raiz),
                patch.object(ler_pdf, "pasta_pdfs", originais),
                patch.object(ler_pdf.pdfplumber, "open", side_effect=abrir),
                redirect_stdout(StringIO()),
            ):
                if sobreposicao:
                    with patch.object(pd.DataFrame, "to_csv") as gravar:
                        with self.assertRaisesRegex(ValueError, "sobreposição") as erro:
                            ler_pdf.main()
                        gravar.assert_not_called()
                    for nome in documentos:
                        self.assertIn(nome, str(erro.exception))
                    self.assertEqual(csv.read_bytes(), anterior)
                else:
                    ler_pdf.main()
                    self.assertEqual(len(pd.read_csv(csv)), 4)
            status = ler_status(csv.with_name("status_importacao.json"))
            self.assertEqual(
                status["ultima_tentativa"]["resultado"],
                "falha" if sobreposicao else "sucesso",
            )
            self.assertEqual(
                set(csv.parent.iterdir()), {csv, csv.with_name("status_importacao.json")}
            )


if __name__ == "__main__":
    unittest.main()
