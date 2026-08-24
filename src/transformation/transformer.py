import pandas as pd

REGIONS = {"AC":"N","AP":"N","AM":"N","PA":"N","RO":"N","RR":"N","TO":"N","AL":"NE","BA":"NE","CE":"NE","MA":"NE","PB":"NE","PE":"NE","PI":"NE","RN":"NE","SE":"NE","DF":"CO","GO":"CO","MT":"CO","MS":"CO","ES":"SE","MG":"SE","RJ":"SE","SP":"SE","PR":"S","RS":"S","SC":"S"}


def transform(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["regiao"] = result["uf"].map(REGIONS).fillna(result.get("regiao"))
    result["preco_venda"] = result["preco_venda"].astype("float64")
    keys = [c for c in ("data_coleta", "regiao", "uf", "municipio", "produto") if c in result]
    result["preco_medio_grupo"] = result.groupby(keys, dropna=False)["preco_venda"].transform("mean")
    return result
