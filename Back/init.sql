-- 데이터베이스 초기화 스크립트
-- 이 파일은 PostgreSQL 컨테이너가 처음 시작될 때 실행됩니다.

-- 데이터베이스가 이미 존재하는지 확인하고 생성
SELECT 'CREATE DATABASE capstone_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'capstone_db')\gexec

-- capstone_db 데이터베이스에 연결
\c capstone_db;

-- 사용자 생성 (이미 존재할 수 있으므로 IF NOT EXISTS 사용)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'capstone_user') THEN
        CREATE ROLE capstone_user WITH LOGIN PASSWORD 'capstone_password';
    END IF;
END
$$;

-- 권한 부여
GRANT ALL PRIVILEGES ON DATABASE capstone_db TO capstone_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO capstone_user;
