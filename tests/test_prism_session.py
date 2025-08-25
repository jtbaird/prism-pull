import pytest
from unittest.mock import patch, MagicMock
from freezegun import freeze_time
import datetime
import src.prism_session as ps


# HELPER FUNCTION TESTS
def test_check_months():
    result = ps.check_months(6)
    assert result is None
    with pytest.raises(ValueError, match="Month must be between 1 and 12."):
        ps.check_months(0)
    with pytest.raises(ValueError, match="Month must be between 1 and 12."):
        ps.check_months(13)


def test_check_dates():
    result = ps.check_dates(3, 2, 2020)
    assert result is None
    result = ps.check_dates(16, 11, 1995)
    assert result is None
    result = ps.check_dates(31, 10, 2021)
    assert result is None
    with pytest.raises(
        ValueError, match="Date must be between 0 and 30 for February in a leap year."
    ):
        ps.check_dates(30, 2, 2020)
    with pytest.raises(
        ValueError, match="Date must be between 0 and 29 for February in non leap year."
    ):
        ps.check_dates(29, 2, 2021)
    with pytest.raises(
        ValueError, match="Date must be between 0 and 32 for this month."
    ):
        ps.check_dates(32, 10, 2021)
    with pytest.raises(
        ValueError, match="Date must be between 0 and 31 for this month."
    ):
        ps.check_dates(31, 11, 2021)


def test_check_years():
    present = int(datetime.datetime.now().year)
    result = ps.check_years(1995)
    assert result is None
    with pytest.raises(ValueError, match=f"Year must be between 1895 and {present}."):
        ps.check_years(1894)
    with pytest.raises(ValueError, match=f"Year must be between 1895 and {present}."):
        ps.check_years(3000)


@freeze_time("2025-01-01")
def test_is_within_past_6_months():
    assert ps.is_within_past_6_months(2024, 12, 1) is True
    assert ps.is_within_past_6_months(2020, 1, 2) is False


def test_is_float_string():
    assert ps.is_float_string("3.14")
    assert not ps.is_float_string("abc")
    assert not ps.is_float_string("[1, 2, 3]")
    assert not ps.is_float_string("{'key': 'value'}")


# PUBLIC METHOD TESTS
@patch("src.prism_session.webdriver.Chrome", return_value=MagicMock())
def test_prism_session_init(mock_webdriver):
    session = ps.PrismSession()
    assert isinstance(session.driver, MagicMock)


@patch("src.prism_session.webdriver.Chrome", return_value=MagicMock())
def test_close(mock_webdriver):
    session = ps.PrismSession()
    session.close()
    session.driver.quit.assert_called_once()


def test_submit_coordinates():
    pass


def test_get_30_year_monthly_normals():
    pass


def test_get_30_year_daily_normals():
    pass


def test_get_annual_values():
    pass


def test_get_single_month_values():
    pass


def test_get_monthly_values():
    pass


def test_get_daily_values():
    pass


# PRIVATE METHOD TESTS
def test__set_coordinates():
    pass


def test__set_date_range():
    pass


def test__set_data_settings():
    pass


def test__submit_and_download():
    pass


def test__validate_csv():
    pass


def test__upload_csv():
    pass


def test__generate_partitions():
    pass


def test__submit_and_download_bulk():
    pass
