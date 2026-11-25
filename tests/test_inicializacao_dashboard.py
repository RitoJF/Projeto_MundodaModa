import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


class InicializacaoDashboardTest(unittest.TestCase):
    def test_execucao_fora_da_raiz_localiza_modulos_do_projeto(self):
        app = Path(__file__).resolve().parent.parent / "dashboard/app.py"
        codigo = """
import sys
import pandas as pd
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

# Dispensa PDFs e CSV locais para testar a inicialização.
with patch('pandas.read_csv', side_effect=FileNotFoundError):
    painel = AppTest.from_file(sys.argv[1]).run(timeout=30)
assert not painel.exception, [(e.message, e.stack_trace) for e in painel.exception]
assert 'Ainda não há dados disponíveis' in painel.error[0].value
"""
        with TemporaryDirectory() as pasta:
            ambiente = dict(os.environ, MPLCONFIGDIR=pasta)
            ambiente.pop("PYTHONPATH", None)
            resultado = subprocess.run(
                [sys.executable, "-c", codigo, str(app)],
                cwd=pasta, env=ambiente, capture_output=True, text=True, timeout=60,
            )
        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)


if __name__ == "__main__":
    unittest.main()
