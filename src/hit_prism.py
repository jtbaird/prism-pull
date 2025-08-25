import prism_session

prism = prism_session.PrismSession()

# prism.get_30_year_monthly_normals(
#     csv_path='test_coordinates.csv', 
#     solar_rad_clear_sky=True,
#     solar_rad_sloped_sfc=True
# )

# prism.get_30_year_daily_normals(
#     csv_path='test_coordinates.csv',
# )

# prism.get_annual_values(
#     csv_path='test_coordinates.csv',
#     start_year=2020,
#     end_year=2022,
#     precipitation=False, 
#     max_vpd=True
# )

# prism.get_single_month_values(
#     csv_path='test_coordinates.csv',
#     month=6,
#     start_year=2020,
#     end_year=2024,
#     precipitation=True,
#     max_temp=True
# )

# prism.get_monthly_values(
#     csv_path='test_coordinates.csv',
#     start_month=1,
#     start_year=2020,
#     end_month=6,
#     end_year=2025,
#     precipitation=True,
#     max_temp=True
# )

prism.get_daily_values(
    csv_path='large_coordinates.csv',
    start_day=1,
    start_month=1,
    start_year=2020,
    end_day=31,
    end_month=12,
    end_year=2024,
    precipitation=True,
    max_temp=True
)

prism.close()