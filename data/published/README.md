# Camada publicada

`fuel_prices.parquet` é um snapshot derivado exclusivamente do arquivo oficial ANP
`ca-2026-01.zip`, processado em 24/08/2026. Ele contém 422.412 observações válidas
entre 01/01/2026 e 30/06/2026 e permite que a demonstração hospedada funcione sem
baixar ou transformar dados durante a abertura do dashboard.

O snapshot é reproduzível com `python main.py`; a camada operacional completa em
`data/processed/` permanece ignorada pelo Git.

Para reconstruir a versão compacta usada na nuvem, execute:

```bash
python scripts/build_dashboard_snapshot.py
```

Somente colunas consumidas pelo dashboard são publicadas e dimensões repetitivas
usam tipos categóricos. Métricas e agregações utilizam todas as observações; apenas
o box plot aplica uma amostra determinística para evitar excesso de memória/transferência.
