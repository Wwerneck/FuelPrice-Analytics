import pandas as pd
import pytest


@pytest.fixture
def raw_df():
    return pd.DataFrame({
        "Regiao - Sigla": ["SE", "SE", "SE", "SE", "SE"],
        "Estado - Sigla": ["SP"] * 5,
        "Municipio": ["CAMPINAS"] * 5,
        "Revenda": ["POSTO A", "POSTO A", "POSTO A", "POSTO A", "POSTO A"],
        "CNPJ da Revenda": ["1"] * 5,
        "Produto": ["GASOLINA C", "ETANOL", "GASOLINA C", "ETANOL", "GASOLINA C"],
        "Data da Coleta": ["01/01/2026", "01/01/2026", "08/01/2026", "08/01/2026", "15/01/2026"],
        "Valor de Venda": ["6,00", "4,00", "6,20", "4,10", "6,40"],
        "Unidade de Medida": ["R$ / litro"] * 5,
        "Bandeira": ["BRANCA"] * 5,
    })
