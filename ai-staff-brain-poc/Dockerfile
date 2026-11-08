FROM python:3.12-alpine
WORKDIR /app
COPY server.py index.html ./
ENV PORT=8080
USER 65534:65534
EXPOSE 8080
CMD ["python", "server.py"]
