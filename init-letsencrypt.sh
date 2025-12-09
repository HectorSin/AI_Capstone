#!/bin/bash

# SSL 인증서 초기 발급 스크립트
# 사용법: ./init-letsencrypt.sh

set -e

domains=(api.snackcast.shop)
email="your-email@example.com" # 이메일 주소를 입력하세요
staging=0 # 테스트할 때는 1로 설정 (Let's Encrypt 제한 회피)

data_path="./nginx/certbot"
rsa_key_size=4096

# Nginx 임시 설정 생성
mkdir -p "$data_path/conf/live/$domains"

echo "### Nginx를 임시로 시작합니다..."
docker-compose up -d nginx

echo "### 임시 인증서 요청..."
docker-compose run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    --email $email \
    -d $domains \
    --rsa-key-size $rsa_key_size \
    --agree-tos \
    --force-renewal" certbot

echo "### Nginx 재시작..."
docker-compose restart nginx

echo "### SSL 인증서 발급 완료!"
