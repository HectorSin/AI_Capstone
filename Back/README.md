# BackEnd

## DB 세팅
![PostgreSQL](https://www.postgresql.org/download/) 설치

## 실행
```
conda activate capstone
cd Back/app
uvicorn main:app --reload
```

## 데이터베이스 스키마

![데이터베이스 스키마](../img/database.png)

### 주요 엔티티
- **User**: 사용자 정보 관리
- **AnalysisTopic**: 분석 주제 관리
- **TopicResult**: 주제 분석 결과
- **Schedule**: 스케줄링 관리
- **Voice**: 음성 설정
- **GeneratedPodcast**: 생성된 팟캐스트
- **Subscription**: 구독 관계
- **SourceURL**: 소스 URL 관리