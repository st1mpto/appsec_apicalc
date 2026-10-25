FROM appsec-apicalc:base

ARG APP_VERSION=1.0.0-local
ARG GIT_COMMIT=local

ENV APP_VERSION=${APP_VERSION} \
    GIT_COMMIT=${GIT_COMMIT}

WORKDIR /app

COPY --chown=appuser:appgroup app ./app

USER appuser

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--no-server-header"]