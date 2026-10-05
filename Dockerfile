FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
ARG INSTALL_ML=true
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
WORKDIR /app
COPY backend/requirements-base.txt backend/requirements-ml.txt /app/backend/
RUN pip install --no-cache-dir -r backend/requirements-base.txt && \
    if [ "$INSTALL_ML" = "true" ]; then \
      pip install --no-cache-dir torch==2.13.0 --index-url https://download.pytorch.org/whl/cpu && \
      pip install --no-cache-dir -r backend/requirements-ml.txt; fi
COPY backend/ /app/backend/
COPY models/ /app/models/
COPY LICENSE NOTICE /app/
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist
WORKDIR /app/backend
EXPOSE 8000
CMD ["python", "-m", "app.serve"]
