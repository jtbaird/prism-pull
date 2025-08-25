from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import datetime
import os
import logging
import csv

BULK_URL = "https://prism.oregonstate.edu/explorer/bulk.php"
SINGLE_URL = "https://prism.oregonstate.edu/explorer/"
CWD = os.getcwd()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_months(month):
    if month < 1 or month > 12:
        raise ValueError("Month must be between 1 and 12.")


def check_dates(date, month, year):
    is_leap_year = year % 4 == 0
    if is_leap_year and month == 2:
        if date < 1 or date > 29:
            raise ValueError("Date must be between 0 and 30 for February in a leap year.")
    elif not is_leap_year and month == 2:
        if date < 1 or date > 28:
            raise ValueError("Date must be between 0 and 29 for February in non leap year.")
    elif month in [4, 6, 9, 11]:
        if date < 1 or date > 30:
            raise ValueError("Date must be between 0 and 31 for this month.")
    else:
        if date < 1 or date > 31:
            raise ValueError("Date must be between 0 and 32 for this month.")


def check_years(year):
    present = int(datetime.datetime.now().year)
    if year < 1895 or year > present:
        raise ValueError(f"Year must be between 1895 and {present}.")


def is_within_past_6_months(year, month, date):
    now = datetime.datetime.now()
    # Calculate the year and month 6 months ago
    six_months_ago_year = now.year
    six_months_ago_month = now.month - 6
    if six_months_ago_month <= 0:
        six_months_ago_month += 12
        six_months_ago_year -= 1
    six_months_ago = datetime.datetime(six_months_ago_year, six_months_ago_month, 1)
    target = datetime.datetime(year, month, date)
    return target >= six_months_ago


def is_float_string(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


class PrismSession:
    def __init__(self, download_dir=CWD, driver_wait=5):
        """
        Initializes a new session for interacting with the PRISM API.

        Args:
            download_dir (str): The absolute path where downloaded files will be saved. Defaults to current working dir.
        """
        logger.info("Starting new PRISM session...")
        self.singular_url = SINGLE_URL
        self.bulk_url = BULK_URL
        self.download_dir = download_dir
        self.driver_wait = driver_wait

        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "directory_upgrade": True,
                "safebrowsing.enabled": True,
            },
        )

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=chrome_options
        )

        logger.info("PRISM session initialized.")

    def close(self):
        logger.info("Closing PRISM session...")
        self.driver.quit()
        logger.info("PRISM session closed.")

    def submit_coordinates(
        self,
        is_bulk_request,
        latitude=40.9473,
        longitude=-112.2170,
        csv_path="/dummy/path/to/csv",
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
        is_30_year_monthly=False,
        is_30_year_daily=False,
        is_annual=False,
        is_single_month=False,
        is_monthly=True,
        is_daily=False,
        start_date=1,
        start_month=1,
        start_year=2020,
        end_date=1,
        end_month=12,
        end_year=2020,
    ):
        """
        Submits a single latitude and longitude to the PRISM Explorer and downloads the result.

        Args:
            latitude (float): Latitude value to submit.
            longitude (float): Longitude value to submit.

        Returns:
            None
        """

        # Validate date inputs
        self._validate_inputs(
            start_date, start_month, start_year, end_date, end_month, end_year
        )

        # open browser and switch to coordinate location mode
        if is_bulk_request:
            self.driver.get(self.bulk_url)
            logger.info("Validating CSV file...")
            needs_partition = self._validate_csv(csv_path)
            if not needs_partition:
                logger.info("Uploading CSV file...")
                self._upload_csv(csv_path)
            else:
                # if there's more than 500 records, break into subsets of 500, set the rest of the request,
                # loop through and download partition
                logger.info("Partitioning CSV file...")
                partitions = self._generate_partitions(csv_path)
        else:
            self.driver.get(self.singular_url)
            self._set_coordinates(latitude, longitude)

        # set date configuration:
        self._set_date_range(
            is_30_year_monthly,
            is_30_year_daily,
            is_annual,
            is_single_month,
            is_monthly,
            is_daily,
            start_date,
            start_month,
            start_year,
            end_date,
            end_month,
            end_year,
        )

        # Set data settings
        self._set_data_settings(
            precipitation,
            min_temp,
            mean_temp,
            max_temp,
            min_vpd,
            max_vpd,
            mean_dewpoint_temp,
            cloud_transmittance,
            solar_rad_horiz_sfc,
            solar_rad_sloped_sfc,
            solar_rad_clear_sky,
        )

        # submit the form and download the data
        if is_bulk_request:
            if needs_partition:
                logger.info("Submitting and downloading multi part bulk data...")
                for part in partitions:
                    self._upload_csv(part)
                    logger.info(
                        f"Submitting and downloading data for partition: {part}"
                    )
                    self._submit_and_download_bulk()
                    logger.info(f"Removing temporary CSV file: {part}")
                    os.remove(part)
            else:
                logger.info("Submitting and downloading single part bulk data...")
                self._submit_and_download_bulk()
        else:
            self._submit_and_download()

    # SINGLE COORDINATE PAIR REQUESTS

    def get_30_year_monthly_normals(
        self,
        latitude=None,
        longitude=None,
        csv_path=None,
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
    ):
        """
        Retrieves PRISM baseline datasets describing average monthly and annual conditions over the most recent three full decades.

        Args:
            latitude (float): Latitude of the location.
            longitude (float): Longitude of the location.
            precipitation (bool, optional): Whether to include precipitation data. Defaults to True.
            min_temp (bool, optional): Whether to include minimum temperature data. Defaults to False.
            mean_temp (bool, optional): Whether to include mean temperature data. Defaults to False.
            max_temp (bool, optional): Whether to include maximum temperature data. Defaults to False.
            min_vpd (bool, optional): Whether to include minimum vapor pressure deficit data. Defaults to False.
            max_vpd (bool, optional): Whether to include maximum vapor pressure deficit data. Defaults to False.
            mean_dewpoint_temp (bool, optional): Whether to include mean dewpoint temperature data. Defaults to False.
            cloud_transmittance (bool, optional): Whether to include cloud transmittance data. Defaults to False.
            solar_rad_horiz_sfc (bool, optional): Whether to include horizontal surface solar radiation data. Defaults to False.
            solar_rad_sloped_sfc (bool, optional): Whether to include sloped surface solar radiation data. Defaults to False.
            solar_rad_clear_sky (bool, optional): Whether to include clear sky solar radiation data. Defaults to False.

        Returns:
            None
        """
        if csv_path:
            logger.info(f"Processing bulk request with CSV: {csv_path}")
            is_bulk_request = True
            if not os.path.isabs(csv_path):
                logger.info("Converting CSV path to absolute path...")
                csv_path = os.path.abspath(csv_path)
        elif latitude is not None and longitude is not None:
            logger.info(
                f"Processing single coordinate request: {latitude}, {longitude}"
            )
            is_bulk_request = False
        else:
            raise ValueError("Either CSV path or latitude/longitude must be provided.")

        self.submit_coordinates(
            latitude=latitude,
            longitude=longitude,
            csv_path=csv_path,
            is_bulk_request=is_bulk_request,
            precipitation=precipitation,
            min_temp=min_temp,
            mean_temp=mean_temp,
            max_temp=max_temp,
            min_vpd=min_vpd,
            max_vpd=max_vpd,
            mean_dewpoint_temp=mean_dewpoint_temp,
            cloud_transmittance=cloud_transmittance,
            solar_rad_horiz_sfc=solar_rad_horiz_sfc,
            solar_rad_sloped_sfc=solar_rad_sloped_sfc,
            solar_rad_clear_sky=solar_rad_clear_sky,
            is_monthly=False,
            is_30_year_monthly=True,
        )

    def get_30_year_daily_normals(
        self,
        latitude=None,
        longitude=None,
        csv_path=None,
        precipitation=True,
        min_temp=False,
        mean_temp=True,
        max_temp=False,
        min_vpd=False,
        max_vpd=False,
        mean_dewpoint_temp=False,
    ):
        """
        Retrieves PRISM baseline datasets describing average monthly and annual conditions over the most recent three full decades.

        Args:
            latitude (float): Latitude of the location.
            longitude (float): Longitude of the location.
            precipitation (bool, optional): Whether to include precipitation data. Defaults to True.
            min_temp (bool, optional): Whether to include minimum temperature data. Defaults to False.
            mean_temp (bool, optional): Whether to include mean temperature data. Defaults to False.
            max_temp (bool, optional): Whether to include maximum temperature data. Defaults to False.
            min_vpd (bool, optional): Whether to include minimum vapor pressure deficit data. Defaults to False.
            max_vpd (bool, optional): Whether to include maximum vapor pressure deficit data. Defaults to False.
            mean_dewpoint_temp (bool, optional): Whether to include mean dewpoint temperature data. Defaults to False.

        Returns:
            None
        """
        if csv_path:
            logger.info(f"Processing bulk request with CSV: {csv_path}")
            is_bulk_request = True
            if not os.path.isabs(csv_path):
                logger.info("Converting CSV path to absolute path...")
                csv_path = os.path.abspath(csv_path)
        elif latitude is not None and longitude is not None:
            logger.info(
                f"Processing single coordinate request: {latitude}, {longitude}"
            )
            is_bulk_request = False
        else:
            raise ValueError("Either CSV path or latitude/longitude must be provided.")

        self.submit_coordinates(
            latitude=latitude,
            longitude=longitude,
            csv_path=csv_path,
            is_bulk_request=is_bulk_request,
            precipitation=precipitation,
            min_temp=min_temp,
            mean_temp=mean_temp,
            max_temp=max_temp,
            min_vpd=min_vpd,
            max_vpd=max_vpd,
            mean_dewpoint_temp=mean_dewpoint_temp,
            is_monthly=False,
            is_30_year_daily=True,
        )

    def get_annual_values(
        self,
        start_year,
        end_year,
        latitude=None,
        longitude=None,
        csv_path=None,
        precipitation=True,
        min_temp=False,
        mean_temp=True,
        max_temp=False,
        min_vpd=False,
        max_vpd=False,
        mean_dewpoint_temp=False,
    ):
        """
        Retrieves annual PRISM climate values for the specified coordinates and year range.

        Args:
            latitude (float): Latitude of the location.
            longitude (float): Longitude of the location.
            start_year (int): Start year for the data range.
            end_year (int): End year for the data range.
            precipitation (bool, optional): Whether to include precipitation data. Defaults to True.
            min_temp (bool, optional): Whether to include minimum temperature data. Defaults to False.
            mean_temp (bool, optional): Whether to include mean temperature data. Defaults to False.
            max_temp (bool, optional): Whether to include maximum temperature data. Defaults to False.
            min_vpd (bool, optional): Whether to include minimum vapor pressure deficit data. Defaults to False.
            max_vpd (bool, optional): Whether to include maximum vapor pressure deficit data. Defaults to False.
            mean_dewpoint_temp (bool, optional): Whether to include mean dewpoint temperature data. Defaults to False.

        Returns:
            None
        """
        if csv_path:
            logger.info(f"Processing bulk request with CSV: {csv_path}")
            is_bulk_request = True
            if not os.path.isabs(csv_path):
                logger.info("Converting CSV path to absolute path...")
                csv_path = os.path.abspath(csv_path)
        elif latitude is not None and longitude is not None:
            logger.info(
                f"Processing single coordinate request: {latitude}, {longitude}"
            )
            is_bulk_request = False
        else:
            raise ValueError("Either CSV path or latitude/longitude must be provided.")
        if start_year > end_year:
            raise ValueError("Start year must be less than or equal to end year.")

        self.submit_coordinates(
            latitude=latitude,
            longitude=longitude,
            csv_path=csv_path,
            is_bulk_request=is_bulk_request,
            precipitation=precipitation,
            min_temp=min_temp,
            mean_temp=mean_temp,
            max_temp=max_temp,
            min_vpd=min_vpd,
            max_vpd=max_vpd,
            mean_dewpoint_temp=mean_dewpoint_temp,
            is_monthly=False,
            is_annual=True,
            start_year=start_year,
            end_year=end_year,
        )

    def get_single_month_values(
        self,
        month,
        start_year,
        end_year,
        latitude=None,
        longitude=None,
        csv_path=None,
        precipitation=True,
        min_temp=False,
        mean_temp=True,
        max_temp=False,
        min_vpd=False,
        max_vpd=False,
        mean_dewpoint_temp=False,
    ):
        """
        Retrieves PRISM climate values for the given month for every year in the specified range for the specified coordinates.

        Args:
            latitude (float): Latitude of the location.
            longitude (float): Longitude of the location.
            month (int): Month data to be retrieved for each year from start_year to end_year (inclusive).
            start_year (int): Year for the data.
            end_year (int): End year for the data.
            precipitation (bool, optional): Whether to include precipitation data. Defaults to True.
            min_temp (bool, optional): Whether to include minimum temperature data. Defaults to False.
            mean_temp (bool, optional): Whether to include mean temperature data. Defaults to False.
            max_temp (bool, optional): Whether to include maximum temperature data. Defaults to False.
            min_vpd (bool, optional): Whether to include minimum vapor pressure deficit data. Defaults to False.
            max_vpd (bool, optional): Whether to include maximum vapor pressure deficit data. Defaults to False.
            mean_dewpoint_temp (bool, optional): Whether to include mean dewpoint temperature data. Defaults to False.

        Returns:
            None
        """
        if csv_path:
            logger.info(f"Processing bulk request with CSV: {csv_path}")
            is_bulk_request = True
            if not os.path.isabs(csv_path):
                logger.info("Converting CSV path to absolute path...")
                csv_path = os.path.abspath(csv_path)
        elif latitude is not None and longitude is not None:
            logger.info(
                f"Processing single coordinate request: {latitude}, {longitude}"
            )
            is_bulk_request = False
        else:
            raise ValueError("Either CSV path or latitude/longitude must be provided.")
        if start_year > end_year:
            raise ValueError("Start year must be less than or equal to end year.")
        if end_year == datetime.datetime.now().year and is_within_past_6_months(
            end_year, month, 1
        ):
            logger.warning(
                "Data within past 6 months is provisional and may be subject to revision."
            )

        self.submit_coordinates(
            latitude=latitude,
            longitude=longitude,
            csv_path=csv_path,
            is_bulk_request=is_bulk_request,
            precipitation=precipitation,
            min_temp=min_temp,
            mean_temp=mean_temp,
            max_temp=max_temp,
            min_vpd=min_vpd,
            max_vpd=max_vpd,
            mean_dewpoint_temp=mean_dewpoint_temp,
            is_monthly=False,
            is_single_month=True,
            start_month=month,
            start_year=start_year,
            end_year=end_year,
        )

    def get_monthly_values(
        self,
        start_month,
        start_year,
        end_month,
        end_year,
        latitude=None,
        longitude=None,
        csv_path=None,
        precipitation=True,
        min_temp=False,
        mean_temp=True,
        max_temp=False,
        min_vpd=False,
        max_vpd=False,
        mean_dewpoint_temp=False,
    ):
        """
        Retrieves monthly PRISM climate values for the specified coordinates and time range.

        Args:
            latitude (float): Latitude of the location.
            longitude (float): Longitude of the location.
            start_month (int): Start month for the data range.
            start_year (int): Start year for the data range.
            end_month (int): End month for the data range.
            end_year (int): End year for the data range.
            precipitation (bool, optional): Whether to include precipitation data. Defaults to True.
            min_temp (bool, optional): Whether to include minimum temperature data. Defaults to False.
            mean_temp (bool, optional): Whether to include mean temperature data. Defaults to False.
            max_temp (bool, optional): Whether to include maximum temperature data. Defaults to False.
            min_vpd (bool, optional): Whether to include minimum vapor pressure deficit data. Defaults to False.
            max_vpd (bool, optional): Whether to include maximum vapor pressure deficit data. Defaults to False.
            mean_dewpoint_temp (bool, optional): Whether to include mean dewpoint temperature data. Defaults to False.

        Returns:
            None
        """
        if csv_path:
            logger.info(f"Processing bulk request with CSV: {csv_path}")
            is_bulk_request = True
            if not os.path.isabs(csv_path):
                logger.info("Converting CSV path to absolute path...")
                csv_path = os.path.abspath(csv_path)
        elif latitude is not None and longitude is not None:
            logger.info(
                f"Processing single coordinate request: {latitude}, {longitude}"
            )
            is_bulk_request = False
        else:
            raise ValueError("Either CSV path or latitude/longitude must be provided.")
        if start_year > end_year:
            raise ValueError("Start year must be less than or equal to end year.")
        if start_year == end_year and start_month > end_month:
            raise ValueError(
                "Start month must be less than or equal to end month when years are equal."
            )
        if end_year == datetime.datetime.now().year and is_within_past_6_months(
            end_year, end_month, 1
        ):
            logger.warning(
                "Data within past 6 months is provisional and may be subject to revision."
            )

        self.submit_coordinates(  ## don't need to set is_monthly bc defaults to True
            latitude=latitude,
            longitude=longitude,
            csv_path=csv_path,
            is_bulk_request=is_bulk_request,
            precipitation=precipitation,
            min_temp=min_temp,
            mean_temp=mean_temp,
            max_temp=max_temp,
            min_vpd=min_vpd,
            max_vpd=max_vpd,
            mean_dewpoint_temp=mean_dewpoint_temp,
            start_month=start_month,
            start_year=start_year,
            end_month=end_month,
            end_year=end_year,
        )

    def get_daily_values(
        self,
        start_date,
        start_month,
        start_year,
        end_date,
        end_month,
        end_year,
        latitude=None,
        longitude=None,
        csv_path=None,
        precipitation=True,
        min_temp=False,
        mean_temp=True,
        max_temp=False,
        min_vpd=False,
        max_vpd=False,
        mean_dewpoint_temp=False,
    ):
        """
        Submits a request for daily climate data for the specified coordinates and time range.

        Args:
            latitude (float): Latitude of the location.
            longitude (float): Longitude of the location.
            start_date (int): Start date for the data range. Defaults to 1.
            start_month (int): Start month for the data range. Defaults to 1.
            start_year (int): Start year for the data range. Defaults to 2000.
            end_date (int): End date for the data range. Defaults to 31.
            end_month (int): End month for the data range. Defaults to 12.
            end_year (int): End year for the data range. Defaults to 2020.
            precipitation (bool, optional): Whether to include precipitation data. Defaults to True.
            min_temp (bool, optional): Whether to include minimum temperature data. Defaults to False.
            mean_temp (bool, optional): Whether to include mean temperature data. Defaults to False.
            max_temp (bool, optional): Whether to include maximum temperature data. Defaults to False.
            min_vpd (bool, optional): Whether to include minimum vapor pressure deficit data. Defaults to False.
            max_vpd (bool, optional): Whether to include maximum vapor pressure deficit data. Defaults to False.
            mean_dewpoint_temp (bool, optional): Whether to include mean dewpoint temperature data. Defaults to False.

        Returns:
            None
        """
        if csv_path:
            logger.info(f"Processing bulk request with CSV: {csv_path}")
            is_bulk_request = True
            if not os.path.isabs(csv_path):
                logger.info("Converting CSV path to absolute path...")
                csv_path = os.path.abspath(csv_path)
        elif latitude is not None and longitude is not None:
            logger.info(
                f"Processing single coordinate request: {latitude}, {longitude}"
            )
            is_bulk_request = False
        else:
            raise ValueError("Either CSV path or latitude/longitude must be provided.")
        if start_year > end_year:
            raise ValueError("Start year must be less than or equal to end year.")
        if start_year == end_year and start_month > end_month:
            raise ValueError(
                "Start month must be less than or equal to end month when years are equal."
            )
        if start_year == end_year and start_month == end_month and start_date > end_date:
            raise ValueError(
                "Start date must be less than or equal to end date when months and years are equal."
            )
        if end_year == datetime.datetime.now().year and is_within_past_6_months(
            end_year, end_month, 1
        ):
            logger.warning(
                "Data within past 6 months is provisional and may be subject to revision."
            )

        self.submit_coordinates(
            latitude=latitude,
            longitude=longitude,
            csv_path=csv_path,
            is_bulk_request=is_bulk_request,
            precipitation=precipitation,
            min_temp=min_temp,
            mean_temp=mean_temp,
            max_temp=max_temp,
            min_vpd=min_vpd,
            max_vpd=max_vpd,
            mean_dewpoint_temp=mean_dewpoint_temp,
            is_monthly=False,
            is_daily=True,
            start_date=start_date,
            start_month=start_month,
            start_year=start_year,
            end_date=end_date,
            end_month=end_month,
            end_year=end_year,
        )

    # PRIVATE METHODS

    def _validate_inputs(
        self, start_date, start_month, start_year, end_date, end_month, end_year
    ):
        check_dates(start_date, start_month, start_year)
        check_dates(end_date, end_month, end_year)
        check_months(start_month)
        check_months(end_month)
        check_years(start_year)
        check_years(end_year)

    def _set_coordinates(self, latitude, longitude):
        coordinate_button = WebDriverWait(self.driver, self.driver_wait).until(
            EC.element_to_be_clickable((By.ID, "loc_method_coords"))
        )
        coordinate_button.click()

        # get coordinate fields once they're available and populate them
        lat_field = WebDriverWait(self.driver, self.driver_wait).until(
            EC.element_to_be_clickable((By.ID, "loc_lat"))
        )
        lon_field = WebDriverWait(self.driver, self.driver_wait).until(
            EC.element_to_be_clickable((By.ID, "loc_lon"))
        )
        lat_field.clear()
        lat_field.send_keys(str(latitude))
        lon_field.clear()
        lon_field.send_keys(str(longitude))

    def _set_date_range(
        self,
        is_30_year_monthly,
        is_30_year_daily,
        is_annual,
        is_single_month,
        is_monthly,
        is_daily,
        start_date,
        start_month,
        start_year,
        end_date,
        end_month,
        end_year,
    ):

        date_id = "tper_monthly"
        start_month_id = "tper_monthly_start_month"
        start_year_id = "tper_monthly_start_year"
        end_month_id = "tper_monthly_end_month"
        end_year_id = "tper_monthly_end_year"

        if is_30_year_monthly:
            date_id = "tper_monthly_normals"
        elif is_30_year_daily:
            date_id = "tper_daily_normals"
        elif is_annual:
            date_id = "tper_yearly"
            start_year_id = "tper_yearly_start_year"
            end_year_id = "tper_yearly_end_year"
        elif is_single_month:
            date_id = "tper_onemonth"
            start_month_id = "tper_onemonth_month"
            start_year_id = "tper_onemonth_start_year"
            end_year_id = "tper_onemonth_end_year"
        elif is_daily:
            date_id = "tper_daily"
            start_date_id = "tper_daily_start_date"
            start_month_id = "tper_daily_start_month"
            start_year_id = "tper_daily_start_year"
            end_date_id = "tper_daily_end_date"
            end_month_id = "tper_daily_end_month"
            end_year_id = "tper_daily_end_year"

        date_button = WebDriverWait(self.driver, self.driver_wait).until(
            EC.element_to_be_clickable((By.ID, date_id))
        )
        date_button.click()

        # set finer date ranges
        if not (is_30_year_monthly or is_30_year_daily):
            # select years
            start_year_dropdown = WebDriverWait(self.driver, self.driver_wait).until(
                EC.presence_of_element_located((By.ID, start_year_id))
            )
            end_year_dropdown = WebDriverWait(self.driver, self.driver_wait).until(
                EC.presence_of_element_located((By.ID, end_year_id))
            )

            # Create a Select object
            logger.info(f"Selecting years: {start_year} to {end_year}")
            select_start_year = Select(start_year_dropdown)
            select_end_year = Select(end_year_dropdown)
            # Select the desired year by value
            select_start_year.select_by_value(str(start_year))
            select_end_year.select_by_value(str(end_year))

            if not is_annual:
                logger.info(f"Selecting start month: {start_month}")
                start_month_dropdown = WebDriverWait(
                    self.driver, self.driver_wait
                ).until(EC.presence_of_element_located((By.ID, start_month_id)))
                select_start_month = Select(start_month_dropdown)
                select_start_month.select_by_value(str(start_month))

                if not is_single_month:
                    logger.info(f"Selecting end month: {end_month}")
                    end_month_dropdown = WebDriverWait(
                        self.driver, self.driver_wait
                    ).until(EC.presence_of_element_located((By.ID, end_month_id)))
                    select_end_month = Select(end_month_dropdown)
                    select_end_month.select_by_value(str(end_month))

                    if not is_monthly:
                        logger.info(
                            f"Selecting start date: {start_date} and end date: {end_date}"
                        )
                        start_date_dropdown = WebDriverWait(
                            self.driver, self.driver_wait
                        ).until(EC.presence_of_element_located((By.ID, start_date_id)))
                        select_start_date = Select(start_date_dropdown)
                        select_start_date.select_by_value(str(start_date))

                        end_date_dropdown = WebDriverWait(
                            self.driver, self.driver_wait
                        ).until(EC.presence_of_element_located((By.ID, end_date_id)))
                        select_end_date = Select(end_date_dropdown)
                        select_end_date.select_by_value(str(end_date))

    def _set_data_settings(
        self,
        precipitation,
        min_temp,
        mean_temp,
        max_temp,
        min_vpd,
        max_vpd,
        mean_dewpoint_temp,
        cloud_transmittance,
        solar_rad_horiz_sfc,
        solar_rad_sloped_sfc,
        solar_rad_clear_sky,
    ):

        true_defaults = {"precipitation": "cvar_ppt", "mean_temp": "cvar_tmean"}

        false_defaults = {
            "min_temp": "cvar_tmin",
            "max_temp": "cvar_tmax",
            "min_vpd": "cvar_vpdmin",
            "max_vpd": "cvar_vpdmax",
            "mean_dewpoint_temp": "cvar_tdmean",
            "cloud_transmittance": "cvar_soltrans",
            "solar_rad_horiz_sfc": "cvar_soltotal",
            "solar_rad_sloped_sfc": "cvar_solslope",
            "solar_rad_clear_sky": "cvar_solclear",
        }
        for key in true_defaults:
            if not eval(key):
                # Click the corresponding button if the setting is not true
                button = WebDriverWait(self.driver, self.driver_wait).until(
                    EC.element_to_be_clickable((By.ID, true_defaults[key]))
                )
                button.click()

        for key in false_defaults:
            if eval(key):
                # Click the corresponding button if the setting is not false
                button = WebDriverWait(self.driver, self.driver_wait).until(
                    EC.element_to_be_clickable((By.ID, false_defaults[key]))
                )
                button.click()

    def _submit_and_download(self):
        WebDriverWait(self.driver, self.driver_wait).until(
            EC.element_to_be_clickable((By.ID, "submit_button"))
        ).click()
        WebDriverWait(self.driver, self.driver_wait).until(
            EC.element_to_be_clickable((By.ID, "download_button"))
        ).click()
        time.sleep(1)  # Wait for download to complete

    def _validate_csv(self, csv_path):
        with open(csv_path, newline="") as csvfile:
            reader = csv.reader(csvfile)
            row_count = 0
            for row in reader:
                row_count += 1
                if len(row) != 3:
                    raise ValueError("CSV row must have exactly 3 columns.")
                if not is_float_string(row[0]):
                    raise ValueError("First column must be a float coordinate.")
                if not is_float_string(row[1]):
                    raise ValueError("Second column must be a float coordinate.")
                if len(row[2]) > 12:
                    raise ValueError(
                        "Third column must be a string of 12 or fewer characters."
                    )

            logger.info(f"CSV validation passed for {row_count} rows.")
            if row_count > 500:
                logger.info("CSV is greater than 500 row max. Partitioning required.")
                return True
            else:
                logger.info("CSV is within the row limits.")
                return False

    def _upload_csv(self, csv_path):
        """Uploads a CSV file to the bulk request form."""
        # upload_button = WebDriverWait(self.driver, self.driver_wait).until(
        #     EC.element_to_be_clickable((By.ID, "upload_locations"))
        # )
        file_input = WebDriverWait(self.driver, self.driver_wait).until(
            EC.presence_of_element_located((By.ID, "locations_file"))
        )
        file_input.send_keys(csv_path)

    def _generate_partitions(self, csv_path):
        """
        Generates <= 500 record partitions of csv file, and returns a list of their paths
        """
        with open(csv_path, newline="") as infile:
            reader = csv.reader(infile)
            partition_number = 1
            rows = []
            partitions = []
            for row in reader:
                rows.append(row)
                if len(rows) == 500:
                    output_path = f"{csv_path}_{partition_number}.csv"
                    partitions.append(output_path)
                    with open(output_path, "w", newline="") as outfile:
                        writer = csv.writer(outfile)
                        writer.writerows(rows)
                    rows = []  # reset rows for next partition
                    partition_number += 1
            # Write any remaining rows
            if rows:
                output_path = f"{csv_path}_{partition_number}.csv"
                partitions.append(output_path)
                with open(output_path, "w", newline="") as outfile:
                    writer = csv.writer(outfile)
                    writer.writerows(rows)

        return partitions

    def _submit_and_download_bulk(self):
        """
        Submits the bulk request form and downloads the resulting CSV files.
        """
        WebDriverWait(self.driver, self.driver_wait).until(
            EC.element_to_be_clickable((By.ID, "submitdown_button"))
        ).click()
        time.sleep(self.driver_wait)  # Wait for download to complete
