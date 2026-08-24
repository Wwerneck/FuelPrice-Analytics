from datetime import date
from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "dashboard" / "app.py"


def run_dashboard() -> AppTest:
    app = AppTest.from_file(str(APP_PATH), default_timeout=90).run()
    assert not app.exception
    return app


def test_geographic_filters_are_cascading():
    app = run_dashboard()

    city = app.multiselect(key="filter_cities")
    assert city.disabled
    assert city.options == []

    app.multiselect(key="filter_regions").set_value(["SE"]).run()
    assert set(app.multiselect(key="filter_states").options) == {
        "Espírito Santo (ES)", "Minas Gerais (MG)", "Rio de Janeiro (RJ)", "São Paulo (SP)",
    }

    app.multiselect(key="filter_states").set_value(["SP"]).run()
    assert not app.multiselect(key="filter_cities").disabled
    assert "Sao Paulo" in app.multiselect(key="filter_cities").options

    app.multiselect(key="filter_regions").set_value(["S"]).run()
    assert app.multiselect(key="filter_states").value == []
    assert set(app.multiselect(key="filter_states").options) == {
        "Paraná (PR)", "Rio Grande do Sul (RS)", "Santa Catarina (SC)",
    }


def test_custom_period_and_clear_action():
    app = run_dashboard()

    app.selectbox(key="filter_period_mode").select("Personalizado").run()
    app.date_input(key="filter_period_custom").set_value(
        (date(2026, 2, 1), date(2026, 2, 28))
    ).run()
    assert app.date_input(key="filter_period_custom").value == (
        date(2026, 2, 1), date(2026, 2, 28)
    )

    app.multiselect(key="filter_products").set_value(["GASOLINA COMUM"]).run()
    app.button(key="reset_filters").click().run()

    assert app.selectbox(key="filter_period_mode").value == "Todo o período"
    assert app.multiselect(key="filter_products").value == []
    assert len(app.date_input) == 0
    assert not app.exception
