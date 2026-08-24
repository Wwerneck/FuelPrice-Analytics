# FuelPrice Analytics

[![CI](https://github.com/Wwerneck/FuelPrice-Analytics/actions/workflows/ci.yml/badge.svg)](https://github.com/Wwerneck/FuelPrice-Analytics/actions/workflows/ci.yml)
[![Dashboard](https://img.shields.io/badge/Streamlit-Live%20Dashboard-FF4B4B?logo=streamlit&logoColor=white)](https://fuelprice-analytics-nh2bn8uwvdyubz9chnbutm.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)

> **[Acesse o dashboard interativo publicado](https://fuelprice-analytics-nh2bn8uwvdyubz9chnbutm.streamlit.app/)**

Pipeline de engenharia e análise de dados que baixa preços públicos por posto revendedor da ANP, valida o contrato bruto, limpa e transforma os registros, cria features com Pandas/NumPy e publica Parquet, métricas, PostgreSQL e um dashboard Streamlit.

## Problema e objetivos

Os arquivos da ANP são úteis, mas exigem tratamento de encoding, schema, datas, números decimais, qualidade e histórico antes de sustentar análises. O projeto oferece uma execução reproduzível, idempotente e observável, adequada para portfólio de dados.

## Fonte oficial

- Catálogo: [Série Histórica de Preços de Combustíveis e de GLP — ANP](https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/serie-historica-de-precos-de-combustiveis)
- Formato: CSV distribuído diretamente ou em ZIP; leitura tolerante a UTF-8/Latin-1 e separador `;`.
- Granularidade: preço observado por produto, posto e data de coleta.
- Periodicidade: pesquisa semanal, com arquivos recentes mensais e consolidações semestrais.
- Campos oficiais centrais: Região/Estado (siglas), Município, Revenda, CNPJ, endereço, Produto, Data da Coleta, Valor de Venda, Unidade de Medida e Bandeira.

O extrator lê o catálogo e escolhe a consolidação automotiva semestral mais recente. `ANP_SOURCE_URL` permite fixar uma versão oficial. Em 24/08/2026, o fluxo real validou `ca-2026-01.zip`: 422.418 registros lidos e 422.412 publicados.

## Arquitetura

```text
ANP → Extract → Raw/ZIP → Raw validation → Cleaning (Pandas)
    → Transformation + Features (Pandas/NumPy) → Processed validation
    → Interim/Processed Parquet → PostgreSQL → SQL → Streamlit
                              ↑
                     Apache Airflow (orquestração)
```

`main.py` é o caminho de referência. A DAG usa as mesmas funções de `src/`, passa somente caminhos e metadados pequenos via XCom e mantém DataFrames em Parquet.

## Estrutura

```text
config/              configuração central e ambiente
src/extraction/      descoberta, retry, download e idempotência do raw
src/ingestion/       CSV/XLSX/ZIP e detecção prática de encoding
src/transformation/  limpeza, regras e feature engineering
src/validation/      contratos raw/processed e relatório de qualidade
src/analytics/       estatísticas NumPy e métricas JSON
src/database/        conexão e carga idempotente por chave SHA-256
src/pipeline/        orquestração Python e metadados de execução
sql/                 DDL, índices, view e 14 análises SQL
dashboard/           aplicação Streamlit/Plotly
airflow/dags/        DAG semanal com tasks separadas
tests/               testes unitários e de encadeamento sem rede
```

## ETL, NumPy e features

A camada raw não sofre transformação. A limpeza normaliza colunas, textos, produtos, datas, decimais e duplicatas, produzindo um relatório de alterações. Regras geográficas e agregações ficam na transformação. NumPy calcula média, mediana, variância, percentis, variação segura, z-score, outliers e faixas baseadas em P25/P75. Features incluem calendário, preço anterior, variações, médias móveis, relação etanol/gasolina e competitividade com limiar configurável.

Outliers são marcados, nunca excluídos automaticamente.

## Data Quality e observabilidade

Erros críticos — dataset vazio, schema ausente, data/preço não interpretável, produto/UF ausentes, preço não positivo, UF inválida ou null crítico processado — interrompem o pipeline. Duplicatas e outliers geram `APROVADO COM ALERTA`; ausência de problemas gera `APROVADO`; violações críticas geram `REPROVADO`/exceção.

Cada etapa registra START/SUCCESS/FAILURE em console e `logs/pipeline.log`, com traceback. `data/processed/last_run.json` guarda run ID, timestamps, arquivo, contagens, status e relatório de limpeza. Downloads existentes e válidos são reutilizados; a carga PostgreSQL usa chave de negócio hash e upsert.

## Execução local

Requer Python 3.11+.

```bash
python -m venv .venv
# PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-pipeline.txt
copy .env.example .env
python main.py
pytest
streamlit run dashboard/app.py
```

Por padrão, o pipeline termina em Parquet sem exigir infraestrutura. Defina `LOAD_DATABASE=true` para carregar PostgreSQL. O dashboard lê `data/processed/fuel_prices.parquet` e nunca consulta a ANP durante a navegação.

## PostgreSQL e SQL

A primeira versão usa uma tabela analítica desnormalizada: para um único fato e dimensões de baixa complexidade, ela reduz joins e operação sem perder capacidade analítica. Um star schema é roadmap para múltiplas fontes/assuntos. Índices compostos atendem período/produto e UF/município; índices isolados de baixa seletividade foram evitados.

`sql/04_analytics_queries.sql` demonstra filtros, agregações, `HAVING`, CTE, `CASE`, joins lógicos, `LAG`, `LEAD`, `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `AVG OVER` e `SUM OVER`, cobrindo as 14 perguntas do briefing.

## Docker e Airflow

```bash
docker compose up airflow-init
docker compose up -d
```

- Airflow: http://localhost:8080 (`airflow` / `airflow`)
- PostgreSQL: `localhost:5432`

A DAG `fuelprice_pipeline` roda às segundas-feiras, coerente com a pesquisa semanal da ANP. Download recebe três tentativas; validações críticas não recebem retry. Para instalação local do Airflow, use a versão e o arquivo `constraints` oficiais compatíveis com sua versão do Python, em vez de misturá-lo ao ambiente leve do pipeline.

## Dashboard

Filtros de período, região, UF, município e combustível; KPIs de preço, cobertura e outliers; evolução temporal, ranking estadual, distribuição e insights automáticos. Os cálculos respondem ao recorte selecionado, sem valores analíticos hardcoded.

## Testes

Os testes usam um dataset mínimo em memória e cobrem schema, limpeza, tipos, estatística, variação, etanol/gasolina, outliers, descoberta do arquivo e encadeamento até Parquet. A integração real com a ANP é exercitada por `python main.py`.

O teste PostgreSQL é habilitado quando `TEST_DATABASE_URL` está definido. O workflow em `.github/workflows/ci.yml` executa compilação e testes automaticamente em pushes e pull requests.

## Roadmap

- Incrementalidade persistente baseada em arquivo/checksum e watermark de data.
- Dimensões conformadas quando novas fontes justificarem um star schema.
- Testes de integração PostgreSQL/Airflow no CI.
- Great Expectations/OpenLineage e alertas operacionais.
- Particionamento de Parquet por ano/mês para séries históricas maiores.

## Resultados reproduzidos

Na validação de 24/08/2026, a fonte oficial forneceu 422.418 linhas; seis duplicatas foram removidas com rastreabilidade, e 422.412 linhas foram persistidas em Parquet. Métricas e insights completos permanecem calculados dinamicamente a cada execução.
