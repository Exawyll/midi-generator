# ── Stage 1 : build du frontend React ────────────────────────────────────────
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

# Installer les dépendances d'abord (cache Docker)
COPY frontend/package*.json ./
RUN npm ci --silent

# Copier les sources et builder
COPY frontend/ ./
RUN npm run build
# → produit frontend/dist/

# ── Stage 2 : backend Python + static files ───────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Dépendances Python
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Code backend
COPY backend/ ./

# Fichiers statiques du frontend buildé
COPY --from=frontend-builder /app/frontend/dist ./static

ENV PORT=8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
