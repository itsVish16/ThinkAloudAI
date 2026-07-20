import pandas as pd
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def verify_dataset(csv_path: str):
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        logging.error(f"Failed to read CSV: {e}")
        return

    logging.info(f"Loaded dataset with {len(df)} rows.")

    required_columns = [
        "id", "title", "slug", "difficulty", "tags", "description", 
        "constraints", "hints", "time_limit_ms", "memory_limit_mb", 
        "starter_code_cpp", "starter_code_python", "test_cases_json"
    ]

    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        logging.error(f"Missing required columns: {missing_cols}")
        return
    else:
        logging.info("All required columns are present.")

    # Check for missing values in critical columns
    critical_cols = ["title", "description", "difficulty"]
    for col in critical_cols:
        missing_count = df[col].isnull().sum()
        if missing_count > 0:
            logging.warning(f"Column '{col}' has {missing_count} missing values.")

    # Verify JSON in test_cases_json
    invalid_json_count = 0
    for idx, row in df.iterrows():
        try:
            if pd.notna(row['test_cases_json']):
                json.loads(row['test_cases_json'])
        except Exception:
            invalid_json_count += 1
            if invalid_json_count <= 5:
                logging.warning(f"Row {idx} (Title: {row['title']}) has invalid JSON in test_cases_json.")

    if invalid_json_count > 0:
        logging.error(f"Total rows with invalid JSON test cases: {invalid_json_count}")
    else:
        logging.info("All test_cases_json fields are valid JSON.")
        
    # Check difficulty values
    difficulties = df['difficulty'].dropna().unique()
    logging.info(f"Unique difficulty levels: {difficulties}")

if __name__ == "__main__":
    verify_dataset("/Users/vishal/Desktop/ThinkAloudAI/dsa_problems.csv")
