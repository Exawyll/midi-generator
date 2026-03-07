# ── Stage 1 : build du frontend React ────────────────────────────────────────
FROM node:22-slim AS frontend-builder

WORKDIR /build

COPY frontend/ .

RUN npm install --include=dev
RUN npm run build
# → produit /build/dist/

# ── Stage 2 : backend Python + static files ───────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./

COPY --from=frontend-builder /build/dist ./static

ENV PORT=8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
