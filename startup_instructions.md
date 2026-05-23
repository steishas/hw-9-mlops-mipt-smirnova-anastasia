https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html

```bash
mkdir -p ./dags ./logs ./plugins ./config
echo -e "AIRFLOW_UID=$(id -u)" > .env
docker compose run airflow-cli airflow config list
docker compose up airflow-init
docker compose up
```
How to add requirements.txt
https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html#special-case-adding-dependencies-via-requirements-txt-file



----
## Overall shape

This is the **official-style Airflow 3 + CeleryExecutor** layout: **PostgreSQL** holds metadata and Celery results, **Redis** is the Celery broker, and several **Airflow processes** share the same image, env, and volumes via the `x-airflow-common` anchor (see ```47:92:/Users/grigoriyarshinov/projects/mlops_course/airflow_tutorial/docker-compose.yaml```). Anything that runs DAGs/tasks also waits on **healthy** `postgres` and `redis`, and most long-lived services wait for **`airflow-init`** to finish successfully.

## Data and messaging

| Service | Role |
|--------|------|
| **postgres** | Airflow’s **metadata database** (DAGs, runs, pools, variables, users, etc.) and, via config, the **Celery result backend** (`db+postgresql+...`). Data persists in the `postgres-db-volume` volume. |
| **redis** | **Celery message broker**: the scheduler puts work on a queue; **workers** pull jobs from here. Only exposed on the internal Docker network (`expose`, not published to the host). |

## One-shot bootstrap

| Service | Role |
|--------|------|
| **airflow-init** | Runs **once** as root: checks CPU/RAM/disk, creates dirs under `/opt/airflow`, runs **DB migrations** (`_AIRFLOW_DB_MIGRATE`), creates the **FAB admin user** (`_AIRFLOW_WWW_USER_*`), fixes **ownership** of mounted dirs for `AIRFLOW_UID`, and installs `pandas` via `_PIP_ADDITIONAL_REQUIREMENTS` for that run. It is not a long-running Airflow daemon. |

## Long-running Airflow components

| Service | Role |
|--------|------|
| **airflow-apiserver** | **HTTP API + web UI** (Airflow 3 splits this out). Published on **host port 8080**. Health check hits `/api/v2/monitor/health`. Task execution talks to it via `AIRFLOW__CORE__EXECUTION_API_SERVER_URL`. |
| **airflow-scheduler** | **Decides when** DAG runs and task instances should run, and **submits** Celery task commands to Redis. Exposes a small **health** HTTP server on 8974 inside the container. |
| **airflow-dag-processor** | **Parses DAG files** from the mounted `dags/` folder and keeps the metadata DB in sync with what’s on disk (separate from the scheduler in this layout). |
| **airflow-worker** | **Celery worker**: **runs** task processes (PythonOperator, etc.). Depends on apiserver being healthy so execution can reach the API. |
| **airflow-triggerer** | Runs **async trigger** logic (deferred operators, triggers) so the scheduler does not block on long waits. |

## Optional / profile services

| Service | Role |
|--------|------|
| **airflow-cli** | **Profile `debug`**: a container whose default command is `airflow` so you can `docker compose run` ad hoc CLI commands with the same env/volumes as the cluster. |
| **flower** | **Profile `flower`**: **Celery monitoring** UI (port **5555** when enabled with `--profile flower`). |

## Shared filesystem (all `<<: *airflow-common` services)

Mounts bind your project’s **`dags/`**, **`logs/`**, **`config/`** (including `airflow.cfg`), **`plugins/`**, plus **`input/`** and **`output/`** into the containers so DAGs, logs, and local data stay on the host.

---

**Mental model:** Postgres + Redis are the **state and queue**; **init** prepares the DB and files; **dag-processor** keeps DAG definitions current; **scheduler** decides *what* runs and *when*; **workers** do the **CPU work**; **triggerer** handles **async waiting**; **apiserver** is the **UI/API** and part of the execution path in Airflow 3.