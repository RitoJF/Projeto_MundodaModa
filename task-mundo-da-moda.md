# Tasks de melhoria do projeto Mundo da Moda

## Objetivo

Melhorar a extração dos PDFs, a conferência dos valores e a apresentação
dos períodos disponíveis no dashboard.

## Preparação concluída

- [x] Instalar as dependências no ambiente virtual `.venv`.
- [x] Copiar os quatro PDFs para `dados/originais/`, com nomes de
  `faturamento_2023.pdf` a `faturamento_2026.pdf`.
- [x] Executar a extração atual e gerar
  `dados/processados/faturamento_todos_anos.csv`.

A extração foi executada com sucesso. A conferência automática dos valores
com os totais impressos nos PDFs ainda faz parte da Task 02.

## Ordem de execução

Executar 01 → 02 → 03 → 04. As tarefas 05 e 06 podem ser realizadas depois.
Marcar cada critério somente após verificar o comportamento descrito.
Os números esperados abaixo são critérios a validar durante a implementação.

Próxima tarefa: **02 — Conferir os valores extraídos com os PDFs**.

## Task 01 — Respeitar a cobertura informada no PDF

Status: concluída na branch `task/01-cobertura-pdf`.

Arquivo principal: src/ler_pdf.py

Extrair as datas de início e fim do cabeçalho de cada relatório e manter no CSV somente registros dentro desse intervalo, incluindo as duas datas. Isso permite distinguir dias cobertos com faturamento zero de dias sobre os quais o relatório não informa nada.

### Critérios de aceite

- [x] O PDF atual de 2026 gera 213 registros, de 01/01/2026 a 01/08/2026, incluindo os 71 dias com faturamento zero dentro da cobertura.
- [x] A base consolidada dos quatro PDFs tem 1.309 linhas. Os quatro totais anuais permanecem iguais aos dos relatórios.
- [x] Um relatório com cobertura diferente é processado sem alterar o código. Se o cabeçalho estiver ausente ou ilegível, o script informa qual arquivo precisa de revisão e preserva o último CSV válido.

### Validação realizada

- `.venv/bin/python -m unittest discover -s tests -v`: cinco testes passaram.
- Extração dos quatro PDFs reais: 1.309 registros, sem datas duplicadas.
- Em 2026: 213 datas consecutivas de 01/01 a 01/08, com 71 zeros.
- Os quatro totais anuais conferem com o campo `TOTAL GERAL` dos PDFs.
- Testes com outra cobertura, ano bissexto, cabeçalhos inválidos e falha de
  gravação confirmaram o filtro de datas e a preservação do CSV anterior.

## Task 02 — Conferir os valores extraídos com os PDFs

Status: pendente.

Arquivo principal: analise/conferir_csv.py

Comparar automaticamente os totais mensais e gerais extraídos com os valores impressos nos PDFs. A conferência por mês permite detectar valores deslocados entre meses, mesmo quando o total geral continua correto.

### Critérios de aceite

- [ ] Os quatro relatórios atuais passam na conferência, incluindo os meses cobertos pelo relatório parcial de 2026.
- [ ] Uma divergência identifica o PDF, o mês ou total geral, o valor esperado e o valor calculado. O comando termina com erro quando há divergência ou quando o valor de referência não pode ser lido.
- [ ] A comparação é feita com precisão de centavos.

## Task 03 — Calcular a cobertura do painel a partir dos dados

Status: pendente.

Depende da Task 01. Arquivo principal: dashboard/app.py

Usar as datas cobertas para determinar os períodos disponíveis e detectar meses, trimestres e anos parciais. Isso permite receber novos relatórios sem atualizar manualmente as exceções de 2026.

### Critérios de aceite

- [ ] A cobertura aparece no painel. Agosto de 2026 aparece como parcial quando exibido, e setembro a dezembro de 2026 não aparecem como faturamento zero.
- [ ] Comparações mensais lado a lado usam meses completos ou exibem períodos parciais com identificação explícita. Uma comparação de acumulado usa a mesma janela nos dois anos.
- [ ] A sazonalidade histórica inclui apenas anos completos. Quando um relatório atualizado amplia a cobertura, os novos períodos ficam disponíveis sem alteração no painel.

## Task 04 — Esclarecer o gráfico diário e analisar dias da semana

Status: pendente.

Depende das Tasks 01 e 03. Arquivo principal: dashboard/app.py

Identificar o gráfico atual como uma média histórica por dia do mês e indicar quais anos entram nele. Acrescentar uma visão por dia da semana para responder quais dias costumam faturar mais no ano selecionado.

### Critérios de aceite

- [ ] O gráfico histórico indica em título ou legenda que usa vários anos e informa quais foram considerados.
- [ ] A nova visão respeita o filtro de ano e apresenta, por dia da semana, a mediana e a quantidade de datas cobertas.
- [ ] Zeros dentro da cobertura entram no cálculo. A legenda usa “dias com faturamento zero” enquanto a loja não confirmar o calendário de funcionamento.

## Task 05 — Ajustar o texto de sazonalidade e estoque

Status: pendente.

Arquivo principal: dashboard/app.py

Explicar que meses de receita historicamente mais alta são uma referência para programar a revisão do estoque. Para decidir quais itens reforçar e em qual quantidade, a loja precisa consultar vendas por produto e estoque disponível.

### Critérios de aceite

- [ ] A mensagem cita os anos usados e relaciona os picos históricos a uma possível data de revisão do estoque.
- [ ] O texto explica quais dados adicionais são necessários para decidir a reposição por produto.

## Task 06 — Gerar um ZIP de entrega enxuto

Status: pendente.

Arquivos principais: README.md e requirements.txt

Montar um pacote com o código e as instruções para recriar o ambiente. Incluir dados reais somente se forem adequados ao destinatário da entrega.

### Critérios de aceite

- [ ] O ZIP inclui código, README e dependências, sem .venv, .git ou __pycache__.
- [ ] O README indica onde colocar os PDFs, como processar os dados, como executar a conferência e como iniciar o painel.
- [ ] A instalação e a abertura do painel são verificadas em um ambiente virtual novo com os arquivos destinados à entrega.
