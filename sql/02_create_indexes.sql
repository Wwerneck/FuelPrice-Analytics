CREATE INDEX IF NOT EXISTS idx_fuel_prices_date_product ON fuel_prices (data_coleta, produto);
CREATE INDEX IF NOT EXISTS idx_fuel_prices_location ON fuel_prices (uf, municipio);
CREATE INDEX IF NOT EXISTS idx_fuel_prices_cnpj ON fuel_prices (cnpj_revenda);
-- Índices refletem filtros do dashboard; colunas de baixa seletividade isoladas foram evitadas.
