# import streamlit as st
# import feedparser
# import os
# import urllib.parse
# from dotenv import load_dotenv
# from openai import OpenAI

# # 1. 환경 변수 로드
# load_dotenv()

# # --- 설정 및 초기화 ---
# API_KEY = os.getenv("OPENAI_API_KEY")
# API_BASE = os.getenv("OPENAI_API_BASE")  # GMS 등 별도 엔드포인트 사용 시 필요
# MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gpt-3.5-turbo") # 기본값 설정

# # OpenAI 클라이언트 초기화 (GMS 호환 구조)
# # 만약 GMS가 OpenAI SDK와 호환되지 않는 requests 방식이라면 이 부분을 수정해야 합니다.
# if API_BASE:
#     client = OpenAI(api_key=API_KEY, base_url=API_BASE)
# else:
#     client = OpenAI(api_key=API_KEY)

# # 페이지 설정
# st.set_page_config(page_title="AI 뉴스 큐레이터", page_icon="📰")
# st.title("📰 AI 뉴스 검색 챗봇")

# # 세션 상태 초기화 (대화 기록)
# if "messages" not in st.session_state:
#     st.session_state.messages = []

# # --- 핵심 함수 정의 ---

# def get_news_data(keyword):
#     """
#     Google News RSS를 통해 키워드 관련 기사를 수집합니다.
#     Args:
#         keyword (str): 검색할 키워드
#     Returns:
#         list: 기사 정보 딕셔너리 리스트 (최대 5개)
#     """
#     encoded_keyword = urllib.parse.quote(keyword)
#     # 한국어(ko), 한국 지역(KR) 설정
#     rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
    
#     feed = feedparser.parse(rss_url)
#     news_items = []
    
#     if not feed.entries:
#         return []

#     # 상위 5개 기사만 추출
#     for entry in feed.entries[:5]:
#         news_items.append({
#             "title": entry.title,
#             "link": entry.link,
#             "summary": entry.get('summary', '요약 없음')[:200] + "..." # 너무 긴 요약은 자름
#         })
    
#     return news_items

# def classify_intent(user_input):
#     """
#     사용자의 입력이 '뉴스 검색'인지 '일반 대화'인지 판단하고, 검색어까지 추출합니다.
#     Returns:
#         dict: {"type": "SEARCH", "keyword": "..."} or {"type": "CHAT", "keyword": None}
#     """
#     system_prompt = """
#     당신은 사용자의 의도를 분류하는 AI입니다.
#     사용자의 입력이 '뉴스', '기사', '최근 소식' 등을 묻는 검색 요청이라면 'SEARCH:검색키워드' 형식으로 답변하세요.
#     검색 요청이 아니라면 'CHAT'이라고만 답변하세요.
    
#     예시 1: "요즘 삼성전자 주가 기사 좀 찾아줘" -> SEARCH:삼성전자 주가
#     예시 2: "안녕 반가워" -> CHAT
#     예시 3: "미국 대선 결과 뉴스 알려줘" -> SEARCH:미국 대선 결과
#     """

#     try:
#         response = client.chat.completions.create(
#             model=MODEL_NAME,
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": user_input}
#             ],
#           #  temperature=0.0 # 정확한 분류를 위해 0으로 설정
#         )
#         content = response.choices[0].message.content.strip()

#         if content.startswith("SEARCH:"):
#             keyword = content.split("SEARCH:")[1].strip()
#             return {"type": "SEARCH", "keyword": keyword}
#         else:
#             return {"type": "CHAT", "keyword": None}
            
#     except Exception as e:
#         st.error(f"의도 파악 중 에러 발생: {e}")
#         return {"type": "CHAT", "keyword": None} # 에러 시 일반 대화로 처리

# def get_llm_response(prompt, context_type="general", news_data=None):
#     """
#     LLM에게 응답을 요청합니다. 뉴스 데이터가 있을 경우 프롬프트를 조정합니다.
#     """
#     messages = st.session_state.messages.copy() # 이전 문맥 유지를 위해 복사
    
#     system_prompt = ""
#     user_content = prompt

#     if context_type == "news_summary" and news_data:
#         system_prompt = "당신은 뉴스 큐레이터입니다. 제공된 뉴스 기사들을 바탕으로 사용자에게 요약된 정보를 제공하세요. 각 기사의 출처(링크)를 반드시 포함하세요."
        
#         # 뉴스 데이터를 텍스트로 변환하여 프롬프트에 주입
#         news_text = "\n".join([f"- 제목: {item['title']}\n  링크: {item['link']}\n  내용: {item['summary']}" for item in news_data])
#         user_content = f"사용자 질문: {prompt}\n\n[검색된 뉴스 데이터]\n{news_text}\n\n위 데이터를 바탕으로 요약해서 답변해줘."
#     else:
#         system_prompt = "당신은 도움이 되는 AI 챗봇입니다."

#     # 시스템 메시지 추가 (리스트 맨 앞에)
#     messages.insert(0, {"role": "system", "content": system_prompt})
    
#     # 마지막 사용자 메시지 교체 (뉴스 데이터가 포함된 프롬프트로 변경되었을 수 있음)
#     if context_type == "news_summary":
#         # 기존 메시지 기록에는 원본 질문만 남기고, 이번 추론에만 뉴스 데이터를 주입
#         # (구현 단순화를 위해 이번 턴의 메시지를 직접 구성)
#         messages[-1] = {"role": "user", "content": user_content}

#     try:
#         stream = client.chat.completions.create(
#             model=MODEL_NAME,
#             messages=messages,
#             stream=True
#         )
#         return stream
#     except Exception as e:
#         return f"API 호출 오류 발생: {e}"

# # --- UI 및 메인 로직 ---

# # 1. 이전 대화 기록 표시
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])

# # 2. 사용자 입력 처리
# if prompt := st.chat_input("무엇을 도와드릴까요? (예: 삼성전자 뉴스 찾아줘)"):
#     # 사용자 메시지 표시 및 저장
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     with st.chat_message("user"):
#         st.markdown(prompt)

#     # 3. 로직 처리 (Assistant 응답)
#     with st.chat_message("assistant"):
#         message_placeholder = st.empty()
#         full_response = ""
        
#         # A. 의도 판단
#         intent_result = classify_intent(prompt)
        
#         # B. 분기 처리
#         if intent_result["type"] == "SEARCH":
#             keyword = intent_result["keyword"]
#             with st.status(f"🔍 '{keyword}' 관련 뉴스를 검색 중입니다...", expanded=True) as status:
#                 # 뉴스 검색 수행
#                 news_items = get_news_data(keyword)
                
#                 if news_items:
#                     status.update(label="뉴스 검색 완료! 요약 중입니다...", state="running")
#                     # LLM에게 요약 요청
#                     stream_response = get_llm_response(prompt, context_type="news_summary", news_data=news_items)
#                     status.update(label="완료!", state="complete", expanded=False)
#                 else:
#                     status.update(label="검색 결과가 없습니다.", state="error")
#                     full_response = f"'{keyword}'에 대한 최신 뉴스를 찾지 못했습니다."
#                     stream_response = None

#         else: # CASE: 일반 대화
#             stream_response = get_llm_response(prompt, context_type="general")

#         # 스트리밍 응답 출력
#         if stream_response and intent_result["type"] != "SEARCH_FAIL":
#              # 문자열 에러 메시지가 아닌 경우 (스트림 객체인 경우)
#             if not isinstance(stream_response, str):
#                 for chunk in stream_response:
#                     if chunk.choices[0].delta.content is not None:
#                         full_response += chunk.choices[0].delta.content
#                         message_placeholder.markdown(full_response + "▌")
#                 message_placeholder.markdown(full_response)
#             else:
#                 # 에러 메시지 출력
#                 full_response = stream_response
#                 message_placeholder.error(full_response)
#         elif not stream_response and intent_result["type"] == "SEARCH":
#              # 뉴스 검색 실패 메시지 출력 (위에서 설정함)
#              message_placeholder.markdown(full_response)

#     # 4. Assistant 응답 저장
#     st.session_state.messages.append({"role": "assistant", "content": full_response})

import streamlit as st
import feedparser
import os
import urllib.parse
from dotenv import load_dotenv
from openai import OpenAI

# 1. 환경 변수 로드
load_dotenv()

# --- 설정 및 초기화 ---
API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE = os.getenv("OPENAI_API_BASE")
MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gpt-3.5-turbo")

# OpenAI 클라이언트 초기화
if API_BASE:
    client = OpenAI(api_key=API_KEY, base_url=API_BASE)
else:
    client = OpenAI(api_key=API_KEY)

# 페이지 설정 (레이아웃을 wide로 하면 사이드바가 더 잘 보입니다)
st.set_page_config(page_title="AI 뉴스 큐레이터", page_icon="📰", layout="wide")
st.title("📰 AI 뉴스 검색 챗봇")

# --- 세션 상태 초기화 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# [추가됨] 토큰 사용량 누적 기록
if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = 0

# --- 사이드바: 사용량 모니터 (새로 추가된 기능) ---
with st.sidebar:
    st.header("📊 사용량 모니터")
    st.info("API에서는 '남은 잔액'을 알려주지 않아서, '이번 대화 사용량'을 추산하여 보여줍니다.")
    
    # 미터기 표시
    st.metric(label="누적 사용 토큰 (추정)", value=f"{st.session_state.total_tokens:,} Tokens")
    
    # 팁
    st.caption(f"현재 모델: {MODEL_NAME}")
    st.caption("※ 한글 1글자 ≈ 1~2토큰")
    
    if st.button("대화 & 사용량 초기화"):
        st.session_state.messages = []
        st.session_state.total_tokens = 0
        st.rerun()

# --- 핵심 함수 정의 ---

def calc_tokens(text):
    """
    토큰 수를 대략적으로 계산합니다. (정확한 토큰 라이브러리 없이 글자 수 기반 추정)
    한글/영어 혼용 시 평균적으로 글자 수의 1.0~1.5배 정도로 잡는 것이 안전합니다.
    """
    if not text:
        return 0
    return int(len(text) * 1.2) # 약간 넉넉하게 잡음

def get_news_data(keyword):
    encoded_keyword = urllib.parse.quote(keyword)
    rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
    
    feed = feedparser.parse(rss_url)
    news_items = []
    
    if not feed.entries:
        return []

    for entry in feed.entries[:5]:
        news_items.append({
            "title": entry.title,
            "link": entry.link,
            "summary": entry.get('summary', '요약 없음')[:200] + "..."
        })
    
    return news_items

def classify_intent(user_input):
    system_prompt = """
    당신은 사용자의 의도를 분류하는 AI입니다.
    사용자의 입력이 '뉴스', '기사', '최근 소식' 등을 묻는 검색 요청이라면 'SEARCH:검색키워드' 형식으로 답변하세요.
    검색 요청이 아니라면 'CHAT'이라고만 답변하세요.
    """
    
    # 의도 파악에 쓰인 토큰도 계산 (입력 + 시스템 프롬프트)
    input_tokens = calc_tokens(system_prompt + user_input)

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
            # temperature 삭제됨 (GMS 호환)
        )
        content = response.choices[0].message.content.strip()
        
        # 출력 토큰 계산
        output_tokens = calc_tokens(content)
        st.session_state.total_tokens += (input_tokens + output_tokens) # 누적

        if content.startswith("SEARCH:"):
            keyword = content.split("SEARCH:")[1].strip()
            return {"type": "SEARCH", "keyword": keyword}
        else:
            return {"type": "CHAT", "keyword": None}
            
    except Exception as e:
        st.error(f"의도 파악 중 에러 발생: {e}")
        return {"type": "CHAT", "keyword": None}

def get_llm_response(prompt, context_type="general", news_data=None):
    messages = st.session_state.messages.copy()
    
    system_prompt = ""
    user_content = prompt

    if context_type == "news_summary" and news_data:
        system_prompt = "당신은 뉴스 큐레이터입니다. 제공된 뉴스 기사들을 바탕으로 사용자에게 요약된 정보를 제공하세요. 각 기사의 출처(링크)를 반드시 포함하세요."
        news_text = "\n".join([f"- 제목: {item['title']}\n  링크: {item['link']}\n  내용: {item['summary']}" for item in news_data])
        user_content = f"사용자 질문: {prompt}\n\n[검색된 뉴스 데이터]\n{news_text}\n\n위 데이터를 바탕으로 요약해서 답변해줘."
    else:
        system_prompt = "당신은 도움이 되는 AI 챗봇입니다."

    messages.insert(0, {"role": "system", "content": system_prompt})
    
    if context_type == "news_summary":
        messages[-1] = {"role": "user", "content": user_content}

    # 입력 프롬프트의 토큰 계산 (대화 기록 전체 + 시스템 프롬프트)
    all_text = "".join([m["content"] for m in messages])
    input_tokens = calc_tokens(all_text)

    try:
        stream = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            stream=True
        )
        return stream, input_tokens # 스트림 객체와 입력 토큰 수 반환
    except Exception as e:
        return f"API 호출 오류 발생: {e}", 0

# --- UI 및 메인 로직 ---

# 1. 이전 대화 기록 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 2. 사용자 입력 처리
if prompt := st.chat_input("무엇을 도와드릴까요? (예: 삼성전자 뉴스 찾아줘)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # A. 의도 판단
        intent_result = classify_intent(prompt)
        
        # B. 분기 처리
        stream_response = None
        input_tokens_estimate = 0
        
        if intent_result["type"] == "SEARCH":
            keyword = intent_result["keyword"]
            with st.status(f"🔍 '{keyword}' 관련 뉴스를 검색 중입니다...", expanded=True) as status:
                news_items = get_news_data(keyword)
                
                if news_items:
                    status.update(label="뉴스 검색 완료! 요약 중입니다...", state="running")
                    # LLM에게 요약 요청 (스트림과 입력 토큰 수 받기)
                    stream_response, input_tokens_estimate = get_llm_response(prompt, context_type="news_summary", news_data=news_items)
                    status.update(label="완료!", state="complete", expanded=False)
                else:
                    status.update(label="검색 결과가 없습니다.", state="error")
                    full_response = f"'{keyword}'에 대한 최신 뉴스를 찾지 못했습니다."
                    stream_response = None

        else: # CASE: 일반 대화
            stream_response, input_tokens_estimate = get_llm_response(prompt, context_type="general")

        # 스트리밍 응답 출력
        if stream_response and intent_result["type"] != "SEARCH_FAIL":
            if not isinstance(stream_response, str):
                for chunk in stream_response:
                    if chunk.choices[0].delta.content is not None:
                        full_response += chunk.choices[0].delta.content
                        message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
                
                # [추가됨] 응답 완료 후 토큰 정산
                output_tokens_estimate = calc_tokens(full_response)
                total_turn_tokens = input_tokens_estimate + output_tokens_estimate
                st.session_state.total_tokens += total_turn_tokens # 사이드바 업데이트를 위해 누적
                
                # 사이드바 즉시 갱신을 위해 rerun (선택사항, 너무 깜빡이면 제거 가능)
                # st.rerun() 
            else:
                full_response = stream_response
                message_placeholder.error(full_response)
        elif not stream_response and intent_result["type"] == "SEARCH":
             message_placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})