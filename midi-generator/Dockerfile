# ── Stage 1 : build du frontend React ────────────────────────────────────────
FROM node:20-slim AS frontend-builder

WORKDIR /build

# Copier tout le frontend en une seule passe (node_modules exclu via .dockerignore)
COPY frontend/ .

# npm install (pas npm ci) pour éviter les conflits de lockfile cross-platform
# --include=dev force l'installation des devDependencies (vite, @vitejs/plugin-react)
RUN npm install --include=dev

RUN npm run build
# → produit /build/dist/

# ── Stage 2 : backend Python + static files ───────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Dépendances Python
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Code backend
COPY backend/ ./

# Fichiers statiques du frontend buildé
COPY --from=frontend-builder /build/dist ./static

ENV PORT=8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
