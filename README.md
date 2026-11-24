# Projeto Mundo da Moda

Dashboard de faturamento da loja a partir de relatórios anuais em PDF.
O projeto extrai os valores diários, gera um CSV, confere os totais com os
relatórios e apresenta os resultados em um painel Streamlit.

## Pré-requisitos

- Python 3 com `pip` e suporte a ambientes virtuais (`venv`).
- Git, para clonar o repositório.
- Relatórios de faturamento em PDF com texto selecionável, no formato
  descrito em [Preparar os PDFs](#preparar-os-pdfs).

O fluxo foi validado em Linux com Python 3.14.4, incluindo instalação em
ambiente novo, extração, conferência, testes e execução do painel via AppTest.

Execute os comandos abaixo na pasta raiz do projeto. No Linux/macOS,
use `python3` para criar o ambiente; no Windows, use `py`.
Após ativar o ambiente, use `python` nos dois sistemas.

## Obter o projeto

```bash
git clone https://github.com/RitoJF/Projeto_MundodaModa.git
cd Projeto_MundodaModa
```

Se você já tem o projeto no computador, abra um terminal nessa pasta.

## Instalar as dependências

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

No Prompt de Comando (`cmd`), ative com `.venv\Scripts\activate.bat`.

As dependências incluem `pandas`, `pdfplumber`, `matplotlib` e `streamlit`.
O `pdfplumber` faz a leitura dos PDFs.

## Preparar os PDFs

Crie a pasta `dados/originais/`.

No Linux/macOS:

```bash
mkdir -p dados/originais
```

No Windows (PowerShell):

```powershell
New-Item -ItemType Directory -Force dados/originais
```

Copie os relatórios para essa pasta, com um arquivo por ano e nomes como:

```text
dados/originais/
├── faturamento_2023.pdf
├── faturamento_2024.pdf
├── faturamento_2025.pdf
└── faturamento_2026.pdf
```

O script procura arquivos com o padrão `faturamento_*.pdf`. Se os arquivos
baixados começarem com `VEN`, confira o ano no cabeçalho de cada relatório
antes de renomeá-los. Evite manter cópias duplicadas do mesmo ano.

O formato esperado contém:

- Cabeçalho com o período, como
  `PERÍODO DE 01/01/2026 À 01/08/2026`, dentro de um único ano.
- Tabela com os dias nas linhas e os doze meses nas colunas, com valores
  como `1.234,56`.
- Uma linha com os doze totais mensais e o campo `TOTAL GERAL` no rodapé.

PDFs digitalizados como imagem precisam de reconhecimento de texto antes
da leitura; o projeto não executa OCR.

Os PDFs originais e o CSV gerado são ignorados pelo Git. Eles não acompanham
o clone do repositório: disponibilize os relatórios localmente.

## Processar os relatórios

Com o ambiente virtual ativo, execute:

```bash
python src/ler_pdf.py
```

O script lê todos os PDFs encontrados e gera:

```text
dados/processados/faturamento_todos_anos.csv
```

O CSV contém as colunas `data`, `ano`, `mes`, `dia` e `faturamento`.
Somente datas dentro do período do cabeçalho são incluídas, com as datas
inicial e final. Dias com faturamento zero dentro da cobertura são mantidos.

Se um período estiver ausente, ilegível ou inválido, o script interrompe
a extração e identifica o arquivo que precisa de revisão. O último CSV
válido é preservado; a substituição acontece somente após a extração e
a gravação completas.

Ao receber um relatório atualizado, substitua o PDF do ano correspondente,
execute a extração novamente e faça a conferência abaixo.

## Conferir os valores

```bash
python analise/conferir_csv.py
```

O comando compara os totais mensais e gerais do CSV com os valores impressos
nos PDFs, com precisão de centavos. Também verifica se as datas do CSV
correspondem à cobertura dos relatórios.

- Código de saída `0`: a conferência passou, com mensagens `OK` por PDF.
- Código de saída `1`: há divergência, referência ilegível ou outro erro
  detectado pela conferência.

Uma divergência de valores informa o PDF, o mês ou total geral, o valor
esperado e o calculado. Revise as mensagens antes de usar os dados do painel.

## Iniciar o dashboard

Depois de gerar e conferir o CSV, execute:

```bash
python -m streamlit run dashboard/app.py
```

Acesse [o dashboard local](http://localhost:8501) no navegador. Para encerrar
o servidor, pressione `Ctrl+C` no terminal. Ao abrir outro terminal,
ative novamente o ambiente virtual antes de executar os comandos.

O painel apresenta:

- Cobertura do ano selecionado e identificação de meses e trimestres parciais.
- Faturamento do período, média dos meses completos e mês de maior receita.
- Comparação mensal entre anos usando somente meses completos; períodos
  parciais ou sem cobertura não são preenchidos com zero.
- Média histórica por dia do mês, com indicação dos anos considerados.
  O filtro de mês se aplica a essa visão histórica.
- Mediana por dia da semana no ano selecionado, quantidade de datas cobertas
  e dias com faturamento zero. Os zeros entram no cálculo; dias sem
  cobertura aparecem como sem dados.
- Sazonalidade calculada somente com anos completos. Os picos históricos
  orientam a revisão do estoque; a decisão de reposição requer vendas por
  produto, quantidades vendidas e estoque disponível de cada item.

## Executar os testes

```bash
python -m unittest discover -s tests -v
```

Os testes verificam extração, cobertura, conferência de valores e
comportamentos do painel com AppTest. Os PDFs reais não são necessários
para executar a suíte; são necessários para processar e conferir os dados
da loja e abrir o painel com esses dados.

## Estrutura do projeto

```text
Projeto_MundodaModa/
├── analise/
│   └── conferir_csv.py       # Conferência dos totais e das datas
├── dashboard/
│   ├── app.py               # Painel Streamlit
│   └── cobertura.py         # Cálculo dos períodos completos e parciais
├── dados/                   # Dados locais
│   ├── originais/           # PDFs de entrada
│   └── processados/         # CSV gerado pela extração
├── src/
│   └── ler_pdf.py           # Extração dos valores diários
├── tests/                   # Testes automatizados
├── requirements.txt         # Dependências Python
└── task-mundo-da-moda.md     # Tarefas e validações realizadas
```

Para sair do ambiente virtual, execute:

```bash
deactivate
```
