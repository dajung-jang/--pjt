import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv()
emb = OpenAIEmbeddings(
    model="text-embedding-3-small",   # ← 이 이름이 되는지 시험하는 것
    api_key=os.environ["GMS_KEY"],
    base_url="https://gms.ssafy.io/gmsapi/api.openai.com/v1/",
)
vec = emb.embed_query("서핑하기 좋은 파도")
print("성공! 벡터 길이:", len(vec))