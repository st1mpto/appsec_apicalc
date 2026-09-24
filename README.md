# API Calculator

API-калькулятор на FastAPI.

На данный момент реализованы:

- базовые математические операции;
- обработка ошибок;
- валидация входных данных;
- unit-тесты;
- Docker-контейнеризация;
- развёртывание приложения на Debian.

CI/CD и инструменты анализа безопасности пока не реализованы.

## Быстрый запуск локально

Создать виртуальное окружение:

```bash
python -m venv .venv
```

Активировать окружение.

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Установить зависимости:

```bash
python -m pip install -r requirements.txt
```

Запустить приложение:

```bash
uvicorn app.main:app --reload
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

Health-check:

```text
http://127.0.0.1:8000/health
```

## Unit-тесты

Установить зависимости для тестирования:

```bash
python -m pip install -r requirements-dev.txt
```

Запустить тесты:

```bash
python -m pytest -v
```


## Развёртывание на Debian

Проект развёрнут на Debian в Docker-контейнере.

После клонирования или обновления репозитория:

```bash
git pull
```

Собрать новую версию:

```bash
docker build -t appsec-apicalc:1.0.0 .
```

Запустить контейнер:

```bash
docker run -d \
  --name appsec-apicalc \
  --restart unless-stopped \
  -p 8000:8000 \
  appsec-apicalc:1.0.0
```

API будет доступен по адресу:

```text
http://<IP_DEBIAN>:8000/docs
```

## Структура проекта

```text
appsec_apicalc/
├── app/
│   ├── main.py
│   ├── models.py
│   └── services/
│       └── calculator.py
├── tests/
├── Dockerfile
├── .dockerignore
├── requirements.txt
├── requirements-dev.txt
└── pytest.ini
```

## Текущий этап

Сейчас проект содержит:

- рабочий API-калькулятор;
- unit-тесты;
- Docker-образ;
- запуск на Debian.
