import prism_session

prism = prism_session.PrismSession()

# prism.get_30_year_monthly_normals(
#     44.0582, 
#     -121.3153, 
#     solar_rad_clear_sky=True,
#     solar_rad_sloped_sfc=True
# )

# prism.get_30_year_daily_normals(
#     44.0582, 
#     -121.3153
# )

# prism.get_annual_values(
#     44.0582, 
#     -121.3153, 
#     start_year=2020, 
#     end_year=2022,
#     precipitation=False, 
#     max_vpd=True
# )

# prism.get_single_month_values(
#     44.0582,
#     -121.3153,
#     start_month=6,
#     start_year=2020,
#     end_year=2024,
#     precipitation=True,
#     max_temp=True
# )

prism.get_monthly_values(
    44.0582,
    -121.3153,
    start_month=1,
    start_year=2020,
    end_month=6,
    end_year=2025,
    precipitation=True,
    max_temp=True
)

# prism.get_daily_values(
#     44.0582,
#     -121.3153,
#     start_day=1,
#     start_month=1,
#     start_year=2020,
#     end_day=31,
#     end_month=12,
#     end_year=2024,
#     precipitation=True,
#     max_temp=True
# )

prism.close()