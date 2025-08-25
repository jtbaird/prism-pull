import pytest
from unittest.mock import patch, MagicMock
from freezegun import freeze_time
import datetime
import src.prism_session as ps
import os


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


def test_is_string_float():
    assert ps.is_string_float("3.14")
    assert not ps.is_string_float("abc")
    assert not ps.is_string_float("[1, 2, 3]")
    assert not ps.is_string_float("{'key': 'value'}")


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


@patch.object(ps.PrismSession, "_submit_and_download")
@patch.object(ps.PrismSession, "_submit_and_download_bulk")
@patch.object(ps.PrismSession, "_set_data_settings")
@patch.object(ps.PrismSession, "_set_date_range")
@patch.object(ps.PrismSession, "_set_coordinates")
# @patch.object(ps.PrismSession, "_generate_partitions")
@patch.object(ps.PrismSession, "_upload_csv")
# @patch.object(ps.PrismSession, "_validate_csv")
@patch.object(ps.PrismSession, "_validate_inputs")
@patch("src.prism_session.webdriver.Chrome", return_value=MagicMock())
def test_submit_coordinates(
    mock_chrome,
    mock_validate_inputs,
    # mock_validate_csv,
    mock_upload_csv,
    # mock_generate_partitions,
    mock_set_coordinates,
    mock_set_date_range,
    mock_set_data_settings,
    mock_submit_and_download_bulk,
    mock_submit_and_download,
):

    session = ps.PrismSession()
    session.driver = MagicMock()  # Prevents real browser usage

    session.submit_coordinates(is_bulk_request=False)

    mock_validate_inputs.assert_called_once()
    assert mock_upload_csv.call_count == 0
    mock_set_coordinates.assert_called_once_with(40.9473, -112.217)
    mock_set_date_range.assert_called_once()
    mock_set_data_settings.assert_called_once()
    assert mock_submit_and_download_bulk.call_count == 0
    mock_submit_and_download.assert_called_once()

    # large bulk request case
    session.submit_coordinates(
        is_bulk_request=True, csv_path="tests/resources/large_coordinates.csv"
    )
    assert mock_validate_inputs.call_count == 2
    assert mock_upload_csv.call_count == 2
    mock_set_coordinates.assert_called_once()
    assert mock_set_date_range.call_count == 2
    assert mock_set_data_settings.call_count == 2
    assert mock_submit_and_download_bulk.call_count == 2
    mock_submit_and_download.assert_called_once()

    # regular bulk request case
    session.submit_coordinates(
        is_bulk_request=True, csv_path="tests/resources/small_coordinates.csv"
    )

    assert mock_validate_inputs.call_count == 3
    assert mock_upload_csv.call_count == 3
    mock_set_coordinates.assert_called_once()
    assert mock_set_date_range.call_count == 3
    assert mock_set_data_settings.call_count == 3
    assert mock_submit_and_download_bulk.call_count == 3
    mock_submit_and_download.assert_called_once()


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
@freeze_time("2025-01-01")
@patch("src.prism_session.webdriver.Chrome", return_value=MagicMock())
def test__validate_inputs(mock_webdriver):
    session = ps.PrismSession()
    result = session._validate_inputs(
        start_date=1,
        start_month=1,
        start_year=2020,
        end_date=31,
        end_month=12,
        end_year=2020,
    )
    assert result is None

    # case where check_months fails
    with pytest.raises(ValueError, match="Month must be between 1 and 12."):
        session._validate_inputs(
            start_date=1,
            start_month=0,
            start_year=2020,
            end_date=31,
            end_month=12,
            end_year=2020,
        )
    # case where check_dates fails
    with pytest.raises(
        ValueError, match="Date must be between 0 and 30 for February in a leap year."
    ):
        session._validate_inputs(
            start_date=30,
            start_month=2,
            start_year=2020,
            end_date=31,
            end_month=12,
            end_year=2020,
        )
    # case where check_years fails
    with pytest.raises(ValueError, match="Year must be between 1895 and 2025."):
        session._validate_inputs(
            start_date=1,
            start_month=1,
            start_year=1894,
            end_date=31,
            end_month=12,
            end_year=2020,
        )


@patch("src.prism_session.WebDriverWait")
@patch("src.prism_session.webdriver.Chrome", return_value=MagicMock())
def test__set_coordinates(mock_webdriver, mock_wait):
    session = ps.PrismSession()
    mock_element = MagicMock()
    mock_element.click = MagicMock()
    mock_element.clear = MagicMock()
    mock_element.send_keys = MagicMock()
    mock_wait.return_value.until.return_value = mock_element

    session._set_coordinates(40.9473, -112.2170)

    assert mock_element.click.call_count == 1
    assert mock_element.clear.call_count == 2
    assert mock_element.send_keys.call_count == 2


@patch("src.prism_session.Select")
@patch("src.prism_session.WebDriverWait")
@patch("src.prism_session.webdriver.Chrome", return_value=MagicMock())
def test__set_date_range(mock_webdriver, mock_wait, mock_select):
    session = ps.PrismSession()

    until_mocks = []

    def until_side_effect(*args, **kwargs):
        mock = MagicMock()
        mock.click = MagicMock()
        until_mocks.append(mock)
        return mock

    mock_wait.return_value.until.side_effect = until_side_effect

    # cases for 30 year date settings
    session._set_date_range(
        is_30_year_monthly=True,
        is_30_year_daily=False,
        is_annual=False,
        is_single_month=False,
        is_monthly=False,
        is_daily=False,
        start_date=1,
        start_month=1,
        start_year=2020,
        end_date=31,
        end_month=12,
        end_year=2020,
    )

    assert until_mocks[0].click.call_count == 1

    session._set_date_range(
        is_30_year_monthly=False,
        is_30_year_daily=True,
        is_annual=False,
        is_single_month=False,
        is_monthly=False,
        is_daily=False,
        start_date=1,
        start_month=1,
        start_year=2020,
        end_date=31,
        end_month=12,
        end_year=2020,
    )

    assert until_mocks[1].click.call_count == 1

    # case for is_annual date setting
    session._set_date_range(
        is_30_year_monthly=False,
        is_30_year_daily=False,
        is_annual=True,
        is_single_month=False,
        is_monthly=False,
        is_daily=False,
        start_date=1,
        start_month=1,
        start_year=2020,
        end_date=31,
        end_month=12,
        end_year=2020,
    )

    # Assert the third mock's click was called
    assert until_mocks[2].click.call_count == 1

    assert mock_select.call_count == 2

    assert mock_select.return_value.select_by_value.call_count == 2

    # case for is_single_month date setting
    session._set_date_range(
        is_30_year_monthly=False,
        is_30_year_daily=False,
        is_annual=False,
        is_single_month=True,
        is_monthly=False,
        is_daily=False,
        start_date=1,
        start_month=1,
        start_year=2020,
        end_date=31,
        end_month=12,
        end_year=2020,
    )

    # Assert the third mock's click was called
    assert until_mocks[2].click.call_count == 1

    assert mock_select.call_count == 5

    assert mock_select.return_value.select_by_value.call_count == 5

    # case for is_monthly date setting
    session._set_date_range(
        is_30_year_monthly=False,
        is_30_year_daily=False,
        is_annual=False,
        is_single_month=False,
        is_monthly=True,
        is_daily=False,
        start_date=1,
        start_month=1,
        start_year=2020,
        end_date=31,
        end_month=12,
        end_year=2020,
    )

    # Assert the third mock's click was called
    assert until_mocks[2].click.call_count == 1

    assert mock_select.call_count == 9

    assert mock_select.return_value.select_by_value.call_count == 9

    # case for is_monthly date setting
    session._set_date_range(
        is_30_year_monthly=False,
        is_30_year_daily=False,
        is_annual=False,
        is_single_month=False,
        is_monthly=False,
        is_daily=True,
        start_date=1,
        start_month=1,
        start_year=2020,
        end_date=31,
        end_month=12,
        end_year=2020,
    )

    # Assert the third mock's click was called
    assert until_mocks[2].click.call_count == 1

    assert mock_select.call_count == 15

    assert mock_select.return_value.select_by_value.call_count == 15


@patch("src.prism_session.WebDriverWait")
@patch("src.prism_session.webdriver.Chrome", return_value=MagicMock())
def test__set_data_settings(mock_chrome, mock_wait):
    session = ps.PrismSession()
    mock_element = MagicMock()
    mock_element.click = MagicMock()
    mock_wait.return_value.until.return_value = mock_element

    session._set_data_settings(
        precipitation=True,
        min_temp=False,
        mean_temp=True,
        max_temp=False,
        min_vpd=False,
        max_vpd=False,
        mean_dewpoint_temp=False,
        cloud_transmittance=False,
        solar_rad_horiz_sfc=False,
        solar_rad_sloped_sfc=False,
        solar_rad_clear_sky=False,
    )

    assert mock_element.click.call_count == 0

    session._set_data_settings(
        precipitation=False,
        min_temp=True,
        mean_temp=False,
        max_temp=True,
        min_vpd=True,
        max_vpd=True,
        mean_dewpoint_temp=True,
        cloud_transmittance=True,
        solar_rad_horiz_sfc=True,
        solar_rad_sloped_sfc=True,
        solar_rad_clear_sky=True,
    )

    assert mock_element.click.call_count == 11


@patch("src.prism_session.WebDriverWait")
@patch("src.prism_session.webdriver.Chrome", return_value=MagicMock())
def test__submit_and_download(mock_chrome, mock_wait):
    session = ps.PrismSession()
    mock_element = MagicMock()
    mock_element.click = MagicMock()
    mock_wait.return_value.until.return_value = mock_element

    session._submit_and_download()

    assert mock_element.click.call_count == 2


@patch("src.prism_session.webdriver.Chrome", return_value=MagicMock())
def test__validate_csv(mock_chrome):
    session = ps.PrismSession()

    # case where csv is <= 500 records
    result = session._validate_csv("tests/resources/small_coordinates.csv")

    assert not result

    # case where csv is over 500 records
    result = session._validate_csv("tests/resources/large_coordinates.csv")

    assert result

    with pytest.raises(ValueError, match="CSV row 3 must have exactly 3 columns."):
        session._validate_csv("tests/resources/short_row.csv")
    with pytest.raises(
        ValueError, match="First column in row 2 must be a float coordinate."
    ):
        session._validate_csv("tests/resources/bad_first_column.csv")
    with pytest.raises(
        ValueError, match="Second column in row 3 must be a float coordinate."
    ):
        session._validate_csv("tests/resources/bad_second_column.csv")
    with pytest.raises(
        ValueError,
        match="Third column in row 4 must be a string of 12 or fewer characters.",
    ):
        session._validate_csv("tests/resources/long_name.csv")


@patch("src.prism_session.WebDriverWait")
@patch("src.prism_session.webdriver.Chrome", return_value=MagicMock())
def test__upload_csv(mock_chrome, mock_wait):
    session = ps.PrismSession()
    mock_element = MagicMock()
    mock_element.send_keys = MagicMock()
    mock_wait.return_value.until.return_value = mock_element

    session._upload_csv("tests/resources/small_coordinates.csv")

    assert mock_element.send_keys.call_count == 1


@patch("src.prism_session.webdriver.Chrome", return_value=MagicMock())
def test__generate_partitions(mock_chrome):
    session = ps.PrismSession()
    partitions = session._generate_partitions("tests/resources/large_coordinates.csv")
    assert len(partitions) == 2

    os.remove("tests/resources/large_coordinates.csv_1.csv")
    os.remove("tests/resources/large_coordinates.csv_2.csv")


@patch("src.prism_session.WebDriverWait")
@patch("src.prism_session.webdriver.Chrome", return_value=MagicMock())
def test__submit_and_download_bulk(mock_chrome, mock_wait):
    session = ps.PrismSession(driver_wait=0)
    mock_element = MagicMock()
    mock_element.click = MagicMock()
    mock_wait.return_value.until.return_value = mock_element

    session._submit_and_download_bulk()

    assert mock_element.click.call_count == 1
