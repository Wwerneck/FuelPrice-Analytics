CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id UUID PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL,
    records_read BIGINT DEFAULT 0,
    records_written BIGINT DEFAULT 0,
    source_file TEXT,
    error_message TEXT
);

-- A tabela analítica desnormalizada é deliberada: o volume e o caso de uso de
-- portfólio não justificam, nesta versão, a complexidade operacional de um star schema.
CREATE TABLE IF NOT EXISTS fuel_prices (
    record_id CHAR(64) PRIMARY KEY,
    data_coleta DATE NOT NULL,
    regiao VARCHAR(2), uf CHAR(2) NOT NULL, municipio TEXT NOT NULL,
    revenda TEXT, cnpj_revenda VARCHAR(18), produto TEXT NOT NULL,
    preco_venda NUMERIC(10,3) NOT NULL CHECK (preco_venda > 0),
    unidade_medida TEXT, bandeira TEXT, ano INTEGER, mes INTEGER,
    ano_mes CHAR(7), trimestre SMALLINT, semana SMALLINT,
    preco_anterior NUMERIC(10,3), variacao_percentual NUMERIC,
    z_score NUMERIC, outlier BOOLEAN, faixa_preco VARCHAR(10),
    relacao_etanol_gasolina NUMERIC, etanol_compensa VARCHAR(3)
);
