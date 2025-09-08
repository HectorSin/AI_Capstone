from langchain.text_splitter import RecursiveCharacterTextSplitter

def split_text(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return text_splitter.split_text(text)

# ai 모델 PoC

"""
Langchain 활용하여 구현
"""

# 텍스트 입력
input_text = "3D 프린팅 기술"

# 텍스트 분할
text_chunks = split_text(input_text)

# 핵심 요약
summary = summarize_text(text_chunks)

# 임베딩 및 벡터 저장

# 팟캐스트 생성

# 요약 리포트

# Q&A

if __name__ == "__main__":
    print(text_chunks)