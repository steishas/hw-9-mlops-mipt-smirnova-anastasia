from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.models import Variable
from datetime import datetime, timedelta

def check_conditions(**context):
    need_retrain = False
    # S3-триггер
    try:
        s3 = S3Hook(aws_conn_id="aws_default")
        if s3.check_for_key("processed/total_checks_sum.txt", bucket_name="retail-checks"):
            obj = s3.get_key("processed/total_checks_sum.txt", bucket_name="retail-checks")
            total_checks = int(obj.get()['Body'].read().decode().strip())
            if total_checks > 10_000_000:
                print(f"S3 trigger: чеков {total_checks} (>10M)")
                need_retrain = True
    except Exception as e:
        print(f"S3 check failed: {e}")

    # Accuracy-триггер
    current_accuracy = float(Variable.get("current_accuracy", default_var="0.95"))
    if current_accuracy < 0.85:
        print(f"Accuracy trigger: {current_accuracy} < 0.85")
        need_retrain = True

    # 3. Срок модели (через конфиг запуска)
    model_expiry_str = context['dag_run'].conf.get('model_expiry') if context.get('dag_run').conf else None
    if model_expiry_str:
        model_expiry = datetime.fromisoformat(model_expiry_str)   # преобразуем строку в datetime
    else:
        model_expiry = datetime.now() + timedelta(hours=2)

    if datetime.now() + timedelta(hours=1) >= model_expiry:
        print(f"Expiry trigger: expires at {model_expiry}")
        need_retrain = True

    context['ti'].xcom_push(key='need_retrain', value=need_retrain)

def branch_decision(**context):
    need_retrain = context['ti'].xcom_pull(key='need_retrain', task_ids='check_conditions')
    return 'trigger_retraining' if need_retrain else 'skip'

with DAG(
    dag_id="ml_inventory_monitor",
    start_date=datetime(2025, 1, 1),
    schedule="@hourly",
    catchup=False,
    max_active_runs=1,
    default_args={'owner': 'ml_team'},
    description="Монитор условий и запуск переобучения",
    tags=["ml", "monitor"]
) as dag:
    check = PythonOperator(task_id="check_conditions", python_callable=check_conditions)
    decide = BranchPythonOperator(task_id="branch", python_callable=branch_decision)

    trigger = TriggerDagRunOperator(
        task_id="trigger_retraining",
        trigger_dag_id="ml_inventory_retraining_pipeline",
        wait_for_completion=False
    )
    skip = EmptyOperator(task_id="skip")
    check >> decide >> [trigger, skip]
