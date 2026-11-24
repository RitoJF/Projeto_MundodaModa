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

A extração e a conferência automática dos totais mensais e gerais foram
executadas com sucesso para os quatro PDFs atuais.

## Ordem de execução

Executar 01 → 02 → 03 → 04. As tarefas 05 e 06 podem ser realizadas depois.
Marcar cada critério somente após verificar o comportamento descrito.
Os números esperados abaixo são critérios a validar durante a implementação.

Próxima tarefa: **06 — Gerar um ZIP de entrega enxuto**.

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

Status: concluída na branch `task/02-conferencia-valores`.

Arquivo principal: analise/conferir_csv.py

Comparar automaticamente os totais mensais e gerais extraídos com os valores impressos nos PDFs. A conferência por mês permite detectar valores deslocados entre meses, mesmo quando o total geral continua correto.

### Critérios de aceite

- [x] Os quatro relatórios atuais passam na conferência, incluindo os meses cobertos pelo relatório parcial de 2026.
- [x] Uma divergência identifica o PDF, o mês ou total geral, o valor esperado e o valor calculado. O comando termina com erro quando há divergência ou quando o valor de referência não pode ser lido.
- [x] A comparação é feita com precisão de centavos.

### Validação realizada

- `.venv/bin/python analise/conferir_csv.py`: os 48 totais mensais e os
  quatro totais gerais conferem; código de saída 0.
- `.venv/bin/python -m unittest discover -s tests -v`: 12 testes passaram,
  incluindo os cinco testes da Task 01.
- Testes de valores deslocados entre meses, diferença de um centavo,
  referências ilegíveis ou ausentes e datas incompatíveis com a cobertura.
- Execução do comando em uma cópia temporária do CSV com alteração de
  R$ 0,01: código de saída 1, com PDF, mês e valores esperado e calculado.
- Valores monetários lidos e somados como `Decimal`, sem arredondar
  diferenças na comparação.

## Task 03 — Calcular a cobertura do painel a partir dos dados

Status: concluída na branch `task/03-cobertura-dashboard`.

Depende da Task 01. Arquivo principal: dashboard/app.py

Usar as datas cobertas para determinar os períodos disponíveis e detectar meses, trimestres e anos parciais. Isso permite receber novos relatórios sem atualizar manualmente as exceções de 2026.

### Critérios de aceite

- [x] A cobertura aparece no painel. Agosto de 2026 aparece como parcial quando exibido, e setembro a dezembro de 2026 não aparecem como faturamento zero.
- [x] Comparações mensais lado a lado usam meses completos ou exibem períodos parciais com identificação explícita. Uma comparação de acumulado usa a mesma janela nos dois anos.
- [x] A sazonalidade histórica inclui apenas anos completos. Quando um relatório atualizado amplia a cobertura, os novos períodos ficam disponíveis sem alteração no painel.

### Validação realizada

- `.venv/bin/python -m unittest discover -s tests -v`: 18 testes passaram,
  incluindo seis testes de cobertura e execução do painel com AppTest.
- O painel abriu com a base real sem exceções: cobertura de 01/01/2026 a
  01/08/2026, com 213 dias cobertos.
- Agosto e o terceiro trimestre de 2026 aparecem como parciais; meses sem
  dados não aparecem como barras ou opções de filtro do ano selecionado.
- A comparação mensal usa somente meses completos e deixa lacunas nos
  períodos restantes. O painel não apresenta comparação de acumulados.
- A média mensal considera somente meses completos. Os demais indicadores
  incluem os valores efetivamente cobertos e identificam meses parciais.
- Simulações de 2027 parcial e completo atualizaram os filtros e a inclusão
  na sazonalidade. Ano bissexto e lacunas de datas também foram testados.

## Task 04 — Esclarecer o gráfico diário e analisar dias da semana

Status: concluída na branch `task/04-analise-dias`.

Depende das Tasks 01 e 03. Arquivo principal: dashboard/app.py

Identificar o gráfico atual como uma média histórica por dia do mês e indicar quais anos entram nele. Acrescentar uma visão por dia da semana para responder quais dias costumam faturar mais no ano selecionado.

### Critérios de aceite

- [x] O gráfico histórico indica em título ou legenda que usa vários anos e informa quais foram considerados.
- [x] A nova visão respeita o filtro de ano e apresenta, por dia da semana, a mediana e a quantidade de datas cobertas.
- [x] Zeros dentro da cobertura entram no cálculo. A legenda usa “dias com faturamento zero” enquanto a loja não confirmar o calendário de funcionamento.

### Validação realizada

- `.venv/bin/python -m unittest discover -s tests -v`: 19 testes passaram.
- AppTest confirmou a identificação da média histórica e dos anos usados,
  a mediana com zeros, as contagens e a atualização ao trocar o filtro de ano.
- Na simulação, os valores 0, 10 e 100 geram mediana 10, três datas cobertas
  e um dia com faturamento zero. Dias sem cobertura mantêm mediana ausente.
- Execução com a base real de 2026 sem exceções: a tabela semanal soma
  213 datas cobertas e 71 dias com faturamento zero.

## Task 05 — Ajustar o texto de sazonalidade e estoque

Status: concluída na branch `task/05-sazonalidade-estoque`.

Arquivo principal: dashboard/app.py

Explicar que meses de receita historicamente mais alta são uma referência para programar a revisão do estoque. Para decidir quais itens reforçar e em qual quantidade, a loja precisa consultar vendas por produto e estoque disponível.

### Critérios de aceite

- [x] A mensagem cita os anos usados e relaciona os picos históricos a uma possível data de revisão do estoque.
- [x] O texto explica quais dados adicionais são necessários para decidir a reposição por produto.

### Validação realizada

- Painel executado com AppTest e a base real, sem exceções.
- Mensagem conferida: cita 2023, 2024 e 2025, o pico em dezembro e novembro
  como possível mês de revisão, considerando o prazo dos fornecedores.
- O texto orienta consultar vendas por produto, quantidades vendidas e
  estoque disponível de cada item para decidir a reposição.

## Task 06 — Gerar um ZIP de entrega enxuto

Status: pendente.

Arquivos principais: README.md e requirements.txt

Montar um pacote com o código e as instruções para recriar o ambiente. Incluir dados reais somente se forem adequados ao destinatário da entrega.

### Critérios de aceite

- [ ] O ZIP inclui código, README e dependências, sem .venv, .git ou __pycache__.
- [ ] O README indica onde colocar os PDFs, como processar os dados, como executar a conferência e como iniciar o painel.
- [ ] A instalação e a abertura do painel são verificadas em um ambiente virtual novo com os arquivos destinados à entrega.
