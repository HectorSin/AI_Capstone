import requests
# ai 모델 MVP 구현

"""
특정 카테고리를 입력 받아 그 카테고리에 대한 팟캐스트를 생성하는 모델을 구현
데이터 수집 -> 보고서 형태로 정리 및 요약 -> 팟캐스트 대본 생성 -> STT 모델 활용 팟캐스트 생성 -> 음성파일 전처리리 -> 팟캐스트 리턴
"""

# 카테고리
category = "VLLM, CV, LLM"
# 데이터 수집
## 해당하는 카테고리의 URL 수집
url = f"https://www.google.com/search?q={category}"
response = requests.get(url)
data = response.text
print(data)

## 해당하는 URL 데이터 수집

## LLM 입력 가능한 형태로 데이터 전처리

# 보고서 형태로 정리 및 요약

# 팟캐스트 대본 생성 [보고서를 토대로로 팟캐스트 대본 생성]

# STT 모델 활용 팟캐스트 생성 [팟캐스트 대본을 토대로 팟캐스트 생성]

# 음성파일 전처리 [팟캐스트 생성 후 음성파일 전처리]

# 팟캐스트 리턴 [음성파일 전처리 후 팟캐스트 리턴]

if __name__ == "__main__":
    pass