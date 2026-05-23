from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import random

def train_model(**context):
    print("Загрузка чеков с S3... обучение линейной регрессии...")
    print("Модель обучена.")

def evaluate_model(**context):
    accuracy = random.uniform(0.8, 0.95)
    print(f"Модель оценена. Accuracy = {accuracy:.2f}")
    if accuracy < 0.85:
        raise ValueError("Качество модели ниже порога, деплой отменён.")
    context['ti'].xcom_push(key='new_accuracy', value=accuracy)

def deploy_model(**context):
    print("Модель задеплоена.")

with DAG(
    dag_id="ml_inventory_retraining_pipeline",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    description="Continuous Training pipeline для расчёта складских запасов",
    tags=["ml", "inventory"]
) as dag:
    train = PythonOperator(task_id="train_model", python_callable=train_model)
    evaluate = PythonOperator(task_id="evaluate_model", python_callable=evaluate_model)
    deploy = PythonOperator(task_id="deploy_model", python_callable=deploy_model)
    train >> evaluate >> deploy
