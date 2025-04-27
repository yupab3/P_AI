# 베이스 이미지
FROM python:3.13-slim

# 작업 디렉토리
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 스크립트 복사
COPY delete_unused_pods.py .

# 컨테이너 시작 시 스크립트 실행
CMD ["python", "delete_unused_pods.py"]
