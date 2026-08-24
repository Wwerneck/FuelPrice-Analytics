# Camada publicada

`fuel_prices.parquet` é um snapshot derivado exclusivamente do arquivo oficial ANP
`ca-2026-01.zip`, processado em 24/08/2026. Ele contém 422.412 observações válidas
entre 01/01/2026 e 30/06/2026 e permite que a demonstração hospedada funcione sem
baixar ou transformar dados durante a abertura do dashboard.

O snapshot é reproduzível com `python main.py`; a camada operacional completa em
`data/processed/` permanece ignorada pelo Git.
