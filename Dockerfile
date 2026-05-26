FROM node:24-alpine AS admin-web-build

WORKDIR /app/admin-web

COPY admin-web/package*.json ./
RUN npm install

COPY admin-web ./
RUN npm run build

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=admin-web-build /app/admin-web/dist ./admin-web/dist

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
