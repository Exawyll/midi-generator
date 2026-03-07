# Image légère : le frontend est buildé en amont par Cloud Build (step node:22)
# Le dist/ est déjà présent dans le workspace quand ce Dockerfile s'exécute.
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./

# dist/ généré par le step npm-build de cloudbuild.yaml
COPY frontend/dist ./static

ENV PORT=8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
