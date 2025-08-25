import csv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_float_string(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def validate_csv(file_path):
    with open(file_path, newline="") as csvfile:
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
                raise ValueError("Third column must be a string of 12 or fewer characters.")

        logger.info(f"CSV validation passed for {row_count} rows.")
        if row_count > 500:
            logger.info("CSV is greater than 500 row max. Partitioning required.")
            return False
        else:
            logger.info("CSV is within the row limits.")
            return True

validate_csv("test_coordinates.csv")