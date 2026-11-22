# Projeto Mundo da Moda

Dashboard de faturamento da loja a partir de relatórios em PDF.

## Executar

Processar os PDFs:

    python src/ler_pdf.py

Conferir os dados:

    python analise/conferir_csv.py

Abrir o dashboard:

    python -m streamlit run dashboard/app.py