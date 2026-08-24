CREATE OR REPLACE VIEW vw_monthly_prices AS
SELECT ano_mes, regiao, uf, municipio, produto,
       AVG(preco_venda) AS preco_medio,
       MIN(preco_venda) AS preco_minimo,
       MAX(preco_venda) AS preco_maximo,
       STDDEV_POP(preco_venda) AS volatilidade,
       COUNT(DISTINCT cnpj_revenda) AS postos
FROM fuel_prices
GROUP BY ano_mes, regiao, uf, municipio, produto;
