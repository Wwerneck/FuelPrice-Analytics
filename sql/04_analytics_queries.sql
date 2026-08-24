-- 1 e 2: médias por combustível e por estado
SELECT produto, AVG(preco_venda) preco_medio FROM fuel_prices GROUP BY produto ORDER BY preco_medio DESC;
SELECT uf, AVG(preco_venda) preco_medio FROM fuel_prices GROUP BY uf ORDER BY preco_medio DESC;

-- 3, 4 e 5: extremos geográficos e ranking municipal
WITH gasolina AS (
  SELECT uf, AVG(preco_venda) media FROM fuel_prices WHERE produto = 'GASOLINA COMUM' GROUP BY uf
)
SELECT uf, media, RANK() OVER (ORDER BY media DESC) rank_mais_cara,
       DENSE_RANK() OVER (ORDER BY media) rank_mais_barata FROM gasolina;
SELECT municipio, uf, AVG(preco_venda) media, ROW_NUMBER() OVER (ORDER BY AVG(preco_venda) DESC) posicao
FROM fuel_prices GROUP BY municipio, uf ORDER BY media DESC;

-- 6, 7, 10 e 14: evolução, variação, valorização e comparação anterior
WITH mensal AS (
 SELECT ano_mes, produto, AVG(preco_venda) media FROM fuel_prices GROUP BY ano_mes, produto
), comparacao AS (
 SELECT *, LAG(media) OVER (PARTITION BY produto ORDER BY ano_mes) anterior,
        LEAD(media) OVER (PARTITION BY produto ORDER BY ano_mes) proxima,
        AVG(media) OVER (PARTITION BY produto ORDER BY ano_mes ROWS BETWEEN 3 PRECEDING AND CURRENT ROW) media_movel,
        SUM(media) OVER (PARTITION BY produto ORDER BY ano_mes) soma_acumulada
 FROM mensal
)
SELECT *, CASE WHEN anterior > 0 THEN (media / anterior - 1) * 100 END variacao_pct
FROM comparacao ORDER BY produto, ano_mes;

-- 8: estados onde etanol compensa (limiar parametrizado :etanol_threshold)
WITH precos AS (
 SELECT ano_mes, uf,
  AVG(preco_venda) FILTER (WHERE produto = 'ETANOL HIDRATADO') etanol,
  AVG(preco_venda) FILTER (WHERE produto = 'GASOLINA COMUM') gasolina
 FROM fuel_prices GROUP BY ano_mes, uf
)
SELECT *, etanol / NULLIF(gasolina, 0) relacao,
 CASE WHEN etanol / NULLIF(gasolina, 0) <= :etanol_threshold THEN 'SIM' ELSE 'NAO' END etanol_compensa
FROM precos WHERE etanol IS NOT NULL AND gasolina IS NOT NULL;

-- 9, 11, 12 e 13: volatilidade, anomalias, amplitude e cobertura
SELECT regiao, STDDEV_POP(preco_venda) volatilidade FROM fuel_prices GROUP BY regiao ORDER BY volatilidade DESC;
SELECT * FROM fuel_prices WHERE outlier IS TRUE ORDER BY ABS(z_score) DESC;
SELECT uf, MAX(preco_venda)-MIN(preco_venda) amplitude FROM fuel_prices GROUP BY uf ORDER BY amplitude DESC;
SELECT uf, municipio, COUNT(DISTINCT cnpj_revenda) postos FROM fuel_prices
GROUP BY uf, municipio HAVING COUNT(DISTINCT cnpj_revenda) > 1 ORDER BY postos DESC;
