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

BULK_URL = "https://prism.oregonstate.edu/explorer/bulk.php"
SINGLE_URL = "https://prism.oregonstate.edu/explorer/"
CWD = os.getcwd()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_months(month):
    if month < 1 or month > 12:
        raise ValueError("Month must be between 1 and 12.")


def check_days(day, month):
    if month == 2:
        if day < 1 or day > 29:
            raise ValueError("Day must be between 1 and 29 for February.")
    elif month in [4, 6, 9, 11]:
        if day < 1 or day > 30:
            raise ValueError("Day must be between 1 and 30 for this month.")
    else:
        if day < 1 or day > 31:
            raise ValueError("Day must be between 1 and 31.")


def check_years(year):
    present = int(datetime.datetime.now().year)
    if year < 1895 or year > present:
        raise ValueError(f"Year must be between 1895 and {present}.")


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
        latitude,
        longitude,
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
        start_day=1,
        start_month=1,
        start_year=2020,
        end_day=1,
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
            start_day, start_month, start_year, end_day, end_month, end_year
        )

        # open browser and switch to coordinate location mode
        self.driver.get(self.singular_url)

        # set coordinates
        self._set_coordinates(latitude, longitude)

        # set date configuration:
        self._set_date_range(
            is_30_year_monthly,
            is_30_year_daily,
            is_annual,
            is_single_month,
            is_monthly,
            is_daily,
            start_day,
            start_month,
            start_year,
            end_day,
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
        self._submit_and_download()

    def get_30_year_monthly_normals(
        self,
        latitude,
        longitude,
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

        self.submit_coordinates(
            latitude,
            longitude,
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
        latitude,
        longitude,
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

        self.submit_coordinates(
            latitude,
            longitude,
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
        latitude,
        longitude,
        start_year,
        end_year,
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
        if start_year > end_year:
            raise ValueError("Start year must be less than or equal to end year.")

        self.submit_coordinates(
            latitude,
            longitude,
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
        latitude,
        longitude,
        start_month,
        start_year,
        end_year,
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
            start_month (int): Month data to be retrieved for each year from start_year to end_year (inclusive).
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
        if start_year > end_year:
            raise ValueError("Start year must be less than or equal to end year.")

        self.submit_coordinates(
            latitude,
            longitude,
            precipitation=precipitation,
            min_temp=min_temp,
            mean_temp=mean_temp,
            max_temp=max_temp,
            min_vpd=min_vpd,
            max_vpd=max_vpd,
            mean_dewpoint_temp=mean_dewpoint_temp,
            is_monthly=False,
            is_single_month=True,
            start_month=start_month,
            start_year=start_year,
            end_year=end_year,
        )

    def get_monthly_values(
        self,
        latitude,
        longitude,
        start_month,
        start_year,
        end_month,
        end_year,
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
        if start_year > end_year:
            raise ValueError("Start year must be less than or equal to end year.")
        if start_year == end_year and start_month > end_month:
            raise ValueError(
                "Start month must be less than or equal to end month when years are equal."
            )

        self.submit_coordinates(  ## don't need to set is_monthly bc defaults to True
            latitude,
            longitude,
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
        latitude,
        longitude,
        start_day,
        start_month,
        start_year,
        end_day,
        end_month,
        end_year,
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
            start_day (int): Start day for the data range. Defaults to 1.
            start_month (int): Start month for the data range. Defaults to 1.
            start_year (int): Start year for the data range. Defaults to 2000.
            end_day (int): End day for the data range. Defaults to 31.
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
        if start_year > end_year:
            raise ValueError("Start year must be less than or equal to end year.")
        if start_year == end_year and start_month > end_month:
            raise ValueError(
                "Start month must be less than or equal to end month when years are equal."
            )
        if start_year == end_year and start_month == end_month and start_day > end_day:
            raise ValueError(
                "Start day must be less than or equal to end day when months and years are equal."
            )

        self.submit_coordinates(
            latitude,
            longitude,
            precipitation=precipitation,
            min_temp=min_temp,
            mean_temp=mean_temp,
            max_temp=max_temp,
            min_vpd=min_vpd,
            max_vpd=max_vpd,
            mean_dewpoint_temp=mean_dewpoint_temp,
            is_monthly=False,
            is_daily=True,
            start_day=start_day,
            start_month=start_month,
            start_year=start_year,
            end_day=end_day,
            end_month=end_month,
            end_year=end_year,
        )

    def _validate_inputs(
        self, start_day, start_month, start_year, end_day, end_month, end_year
    ):
        check_days(start_day, start_month)
        check_days(end_day, end_month)
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
        start_day,
        start_month,
        start_year,
        end_day,
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
            start_date_id = "tper_daily_start_day"
            start_month_id = "tper_daily_start_month"
            start_year_id = "tper_daily_start_year"
            end_date_id = "tper_daily_end_day"
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
                            f"Selecting start day: {start_day} and end day: {end_day}"
                        )
                        start_date_dropdown = WebDriverWait(
                            self.driver, self.driver_wait
                        ).until(EC.presence_of_element_located((By.ID, start_date_id)))
                        select_start_date = Select(start_date_dropdown)
                        select_start_date.select_by_value(str(start_day))

                        end_date_dropdown = WebDriverWait(
                            self.driver, self.driver_wait
                        ).until(EC.presence_of_element_located((By.ID, end_date_id)))
                        select_end_date = Select(end_date_dropdown)
                        select_end_date.select_by_value(str(end_day))

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
