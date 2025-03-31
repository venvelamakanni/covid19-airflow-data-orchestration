from datetime import datetime
import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator

def download_covid_data():
    url = "https://storage.googleapis.com/covid19-open-data/v3/latest/epidemiology.csv"
    df = pd.read_csv(url)
    
    # Clean data: Replace missing 'new_confirmed' with 0
    df["new_confirmed"] = df["new_confirmed"].fillna(0)
    
    df.to_csv("/opt/airflow/data/covid_data.csv", index=False)
    print("Data downloaded!")

def validate_data():
    import great_expectations as ge
    df = ge.read_csv("/opt/airflow/data/covid_data.csv")
    
    # Verify no missing values after cleaning
    results = df.expect_column_values_to_not_be_null("new_confirmed")
    
    if not results.success:
        raise ValueError("Critical: 'new_confirmed' still has missing values!")

def convert_to_parquet():
    df = pd.read_csv("/opt/airflow/data/covid_data.csv")
    df.to_parquet("/opt/airflow/data/covid_data.parquet", index=False)
    print("Converted to Parquet!")

with DAG(
    dag_id="covid_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
) as dag:

    download_task = PythonOperator(
        task_id="download_data",
        python_callable=download_covid_data
    )

    validate_task = PythonOperator(
        task_id="validate_data",
        python_callable=validate_data
    )

    convert_task = PythonOperator(
        task_id="convert_to_parquet",
        python_callable=convert_to_parquet
    )

    download_task >> validate_task >> convert_task