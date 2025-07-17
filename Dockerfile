# ---- Base Builder Stage ----
FROM python:3.11-slim as builder
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --user --no-cache-dir -r requirements.txt

# ---- Final Stage ----
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY src ./src
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "-m", "src.app"]