from unittest.mock import patch, MagicMock
from dags.ml_inventory_monitor import check_conditions

@patch('dags.ml_inventory_monitor.S3Hook')
def test_no_checks(mock_s3):
    mock_hook = MagicMock()
    mock_hook.check_for_key.return_value = False
    mock_s3.return_value = mock_hook

    context = {'ti': MagicMock(), 'dag_run': MagicMock(conf={})}
    check_conditions(**context)
    context['ti'].xcom_push.assert_called_with(key='need_retrain', value=False)
