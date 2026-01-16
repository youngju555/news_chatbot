# import streamlit as st
# import feedparser
# import os
# import urllib.parse
# import requests  # 웹 요청용 라이브러리 추가
# from bs4 import BeautifulSoup  # HTML 분석용 라이브러리 추가
# from dotenv import load_dotenv
# from openai import OpenAI

# # 1. 환경 변수 로드
# load_dotenv()

# # --- 설정 및 초기화 ---
# API_KEY = os.getenv("OPENAI_API_KEY")
# API_BASE = os.getenv("OPENAI_API_BASE")
# MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gpt-3.5-turbo")

# # OpenAI 클라이언트 초기화
# if API_BASE:
#     client = OpenAI(api_key=API_KEY, base_url=API_BASE)
# else:
#     client = OpenAI(api_key=API_KEY)

# # 페이지 설정
# st.set_page_config(page_title="AI 뉴스 큐레이터 (Pro)", page_icon="📰", layout="wide")
# st.title("📰 AI 심층 뉴스 분석 챗봇")

# # --- 세션 상태 초기화 ---
# if "messages" not in st.session_state:
#     st.session_state.messages = []

# # [유지됨] 토큰 사용량 누적 기록
# if "total_tokens" not in st.session_state:
#     st.session_state.total_tokens = 0

# # --- 사이드바: 사용량 모니터 (기존 기능 유지) ---
# with st.sidebar:
#     st.header("📊 사용량 모니터")
#     st.info("API에서는 '남은 잔액'을 알려주지 않아서, '이번 대화 사용량'을 추산하여 보여줍니다.")
    
#     # 미터기 표시
#     st.metric(label="누적 사용 토큰 (추정)", value=f"{st.session_state.total_tokens:,} Tokens")
    
#     # 팁
#     st.caption(f"현재 모델: {MODEL_NAME}")
#     st.caption("※ 한글 1글자 ≈ 1~2토큰")
    
#     if st.button("대화 & 사용량 초기화"):
#         st.session_state.messages = []
#         st.session_state.total_tokens = 0
#         st.rerun()

# # --- 핵심 함수 정의 ---

# def calc_tokens(text):
#     """토큰 수를 대략적으로 계산 (글자 수 * 1.2)"""
#     if not text:
#         return 0
#     return int(len(text) * 1.2)

# # [새로 추가됨] 웹페이지 본문 긁어오기 (BeautifulSoup 사용)
# # [수정됨] 더 강력한 크롤링 함수
# def fetch_article_content(url):
#     try:
#         # 1. 강력한 위장 (크롬 브라우저인 척 헤더 설정)
#         headers = {
#             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
#             "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
#             "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
#             "Referer": "https://www.google.com/"
#         }
        
#         # 2. 세션 사용 (접속 유지력 향상)
#         session = requests.Session()
        
#         # 3. 접속 시도 (타임아웃 3초 -> 15초로 늘림)
#         response = session.get(url, headers=headers, timeout=15, allow_redirects=True)
#         response.raise_for_status() # 404, 403 에러 체크
        
#         # 4. 인코딩 자동 감지 (한글 깨짐 방지)
#         response.encoding = response.apparent_encoding

#         # 5. HTML 파싱
#         soup = BeautifulSoup(response.text, "html.parser")
        
#         # 불필요한 태그 제거
#         for tag in soup(["script", "style", "header", "footer", "nav", "aside", "form", "iframe"]):
#             tag.decompose()
            
#         # 본문 텍스트 추출 (p 태그뿐만 아니라 div의 본문도 고려)
#         text_content = " ".join([p.get_text().strip() for p in soup.find_all(['p', 'div'])])
        
#         # 공백 정리
#         import re
#         text_content = re.sub(r'\s+', ' ', text_content).strip()

#         # 내용이 너무 짧으면(300자 미만) 실패로 간주 (메뉴판만 긁어오는 경우 방지)
#         if len(text_content) < 300:
#             print(f"내용 부족 ({len(text_content)}자): {url}") # 터미널 디버깅용
#             return None
            
#         return text_content[:2000] + "..." # 2000자 제한
        
#     except Exception as e:
#         print(f"크롤링 에러 발생: {e}") # 터미널에서 에러 내용 확인 가능
#         return None
    
# def get_news_data(keyword):
#     encoded_keyword = urllib.parse.quote(keyword)
#     rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
    
#     feed = feedparser.parse(rss_url)
#     news_items = []
    
#     if not feed.entries:
#         return []

#     # 상위 3개 기사만 처리
#     for i, entry in enumerate(feed.entries[:3]):
#         content = entry.get('summary', '요약 없음')
#         source_type = "Google RSS 요약" # 기본값
        
#         # [업그레이드] 상위 2개는 직접 접속해서 본문 읽기 시도
#         if i < 2:
#             # 사이드바에 로딩 상태 표시하지 않고 조용히 처리하거나, 
#             # 필요하면 st.toast 등으로 알릴 수 있음. 여기선 속도를 위해 생략.
#             crawled_text = fetch_article_content(entry.link)
#             if crawled_text:
#                 content = crawled_text
#                 source_type = "🌐 웹사이트 본문 (크롤링됨)"
        
#         news_items.append({
#             "title": entry.title,
#             "link": entry.link,
#             "content": content,
#             "source_type": source_type
#         })
    
#     return news_items

# def classify_intent(user_input):
#     system_prompt = """
#     당신은 사용자의 의도를 분류하는 AI입니다.
#     사용자의 입력이 '뉴스', '기사', '최근 소식' 등을 묻는 검색 요청이라면 'SEARCH:검색키워드' 형식으로 답변하세요.
#     검색 요청이 아니라면 'CHAT'이라고만 답변하세요.
#     """
    
#     input_tokens = calc_tokens(system_prompt + user_input)

#     try:
#         response = client.chat.completions.create(
#             model=MODEL_NAME,
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": user_input}
#             ]
#         )
#         content = response.choices[0].message.content.strip()
        
#         output_tokens = calc_tokens(content)
#         st.session_state.total_tokens += (input_tokens + output_tokens) # 분류 토큰 누적

#         if content.startswith("SEARCH:"):
#             keyword = content.split("SEARCH:")[1].strip()
#             return {"type": "SEARCH", "keyword": keyword}
#         else:
#             return {"type": "CHAT", "keyword": None}
            
#     except Exception as e:
#         return {"type": "CHAT", "keyword": None}

# def get_llm_response(prompt, context_type="general", news_data=None):
#     messages = st.session_state.messages.copy()
    
#     system_prompt = ""
#     user_content = prompt

#     if context_type == "news_summary" and news_data:
#         # 뉴스 데이터를 LLM이 읽기 편하게 포맷팅
#         news_context = ""
#         for idx, item in enumerate(news_data, 1):
#             news_context += f"""
#             [{idx}] 제목: {item['title']}
#             - 출처유형: {item['source_type']}
#             - 링크: {item['link']}
#             - 내용: {item['content']}
#             \n"""
            
#         system_prompt = f"""
#         당신은 심층 뉴스 분석가입니다. [검색된 뉴스 데이터]를 기반으로 답변하세요.
#         '웹사이트 본문'이 포함된 경우, 그 내용을 인용하여 구체적으로 설명하세요.
#         반드시 각 기사의 출처 링크를 포함하세요.
#         """
#         user_content = f"사용자 질문: {prompt}\n\n[검색된 뉴스 데이터]\n{news_context}"
#     else:
#         system_prompt = "당신은 도움이 되는 AI 챗봇입니다."

#     # 프롬프트 구성 (시스템 메시지 추가)
#     messages_for_api = [{"role": "system", "content": system_prompt}] + messages
    
#     if context_type == "news_summary":
#         # 마지막 메시지를 뉴스 데이터가 포함된 버전으로 교체 (API 전송용)
#         messages_for_api.append({"role": "user", "content": user_content})

#     # 입력 토큰 계산
#     all_text = "".join([str(m["content"]) for m in messages_for_api])
#     input_tokens = calc_tokens(all_text)

#     try:
#         stream = client.chat.completions.create(
#             model=MODEL_NAME,
#             messages=messages_for_api,
#             stream=True
#         )
#         return stream, input_tokens
#     except Exception as e:
#         return f"API 호출 오류 발생: {e}", 0

# # --- UI 및 메인 로직 ---

# # 1. 대화 기록 표시
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])

# # 2. 사용자 입력
# if prompt := st.chat_input("무엇을 도와드릴까요?"):
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     with st.chat_message("user"):
#         st.markdown(prompt)

#     with st.chat_message("assistant"):
#         message_placeholder = st.empty()
#         full_response = ""
        
#         # A. 의도 판단
#         intent_result = classify_intent(prompt)
        
#         stream_response = None
#         input_tokens_estimate = 0
        
#         # B. 분기 처리
#         if intent_result["type"] == "SEARCH":
#             keyword = intent_result["keyword"]
#             with st.status(f"🕵️ '{keyword}' 심층 분석 중...", expanded=True) as status:
#                 st.write("1. 구글 뉴스 RSS 수집 중...")
#                 news_items = get_news_data(keyword)
                
#                 # 크롤링 성공 여부 체크
#                 crawled_count = sum(1 for item in news_items if "크롤링" in item['source_type'])
#                 if crawled_count > 0:
#                     status.update(label=f"웹사이트 {crawled_count}곳 원문 확보 완료! 분석 중...", state="running")
#                 else:
#                     status.update(label="원문 접속 불가. 요약본으로 분석합니다.", state="running")
                
#                 if news_items:
#                     stream_response, input_tokens_estimate = get_llm_response(prompt, "news_summary", news_items)
#                     status.update(label="완료!", state="complete", expanded=False)
#                 else:
#                     status.update(label="검색 결과 없음", state="error")
#                     full_response = "관련 기사를 찾지 못했습니다."

#         else: # 일반 대화
#             stream_response, input_tokens_estimate = get_llm_response(prompt, "general")

#         # C. 응답 출력 및 토큰 정산
#         if stream_response:
#             if not isinstance(stream_response, str):
#                 for chunk in stream_response:
#                     if chunk.choices[0].delta.content:
#                         full_response += chunk.choices[0].delta.content
#                         message_placeholder.markdown(full_response + "▌")
#                 message_placeholder.markdown(full_response)
                
#                 # [토큰 정산 - 사용자 요청 기능 유지]
#                 output_tokens_estimate = calc_tokens(full_response)
#                 st.session_state.total_tokens += (input_tokens_estimate + output_tokens_estimate)
                
#                 # 사이드바 갱신을 위해(선택) - 너무 깜빡이면 주석 처리
#                 # st.rerun()
#             else:
#                 full_response = stream_response
#                 message_placeholder.error(full_response)
#         elif not stream_response and intent_result["type"] == "SEARCH" and not full_response:
#              # 검색 실패 시
#              pass

#     st.session_state.messages.append({"role": "assistant", "content": full_response})
import streamlit as st
import feedparser
import os
import urllib.parse
# [변경됨] 전문 크롤링 라이브러리 추가
from newspaper import Article, Config
from dotenv import load_dotenv
from openai import OpenAI
import urllib3
import requests
from bs4 import BeautifulSoup


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 1. 환경 변수 로드
load_dotenv()

# --- 설정 및 초기화 ---
API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE = os.getenv("OPENAI_API_BASE")
MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gpt-3.5-turbo")

if API_BASE:
    client = OpenAI(api_key=API_KEY, base_url=API_BASE)
else:
    client = OpenAI(api_key=API_KEY)

# 페이지 설정
st.set_page_config(page_title="AI 뉴스 큐레이터 (Pro)", page_icon="📰", layout="wide")
st.title("📰 AI 심층 뉴스 분석 챗봇")

# --- 세션 상태 ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = 0

# --- 사이드바 ---
with st.sidebar:
    st.header("📊 사용량 모니터")
    st.metric(label="누적 사용 토큰", value=f"{st.session_state.total_tokens:,} Tokens")
    if st.button("초기화"):
        st.session_state.messages = []
        st.session_state.total_tokens = 0
        st.rerun()

# --- 핵심 함수 ---
def extract_real_url(entry):
    """
    Google News RSS entry에서 실제 언론사 기사 URL 추출
    """
    try:
        if "summary" in entry:
            soup = BeautifulSoup(entry.summary, "html.parser")
            a = soup.find("a")
            if a and a.get("href"):
                return a["href"]
    except Exception:
        pass

    # fallback (실패 시 기존 링크)
    return entry.link

def calc_tokens(text):
    if not text: return 0
    return int(len(text) * 1.2)

# [완전 변경됨] newspaper3k 라이브러리를 사용한 깔끔한 크롤링
# [수정됨] 1. requests로 뚫고 -> 2. newspaper로 분석하는 '하이브리드' 방식
def fetch_article_content(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.google.com/"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        config = Config()
        config.browser_user_agent = headers["User-Agent"]
        config.request_timeout = 10

        article = Article(url, language="ko", config=config)
        article.download(input_html=response.text)
        article.parse()

        text = article.text.strip()
        if len(text) < 300:
            return None

        return text[:2000] + "..."

    except Exception as e:
        print(f"[크롤링 실패] {url} / {e}")
        return None
    
def get_news_data(keyword):
    encoded_keyword = urllib.parse.quote(keyword)
    # [팁] 정확도를 위해 'when:1d' (1일 이내) 옵션을 제거하고 일반 검색 사용
    rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
    
    feed = feedparser.parse(rss_url)
    news_items = []
    
    if not feed.entries:
        return []

    for i, entry in enumerate(feed.entries[:3]):
        content = entry.get('summary', '요약 없음')
        source_type = "Google RSS 요약"
        
        # 상위 2개는 전문 라이브러리로 긁어오기 시도
        if i < 2:
            real_url = extract_real_url(entry)
            crawled_text = fetch_article_content(real_url)
            if crawled_text:
                content = crawled_text
                source_type = "🌐 웹사이트 본문 (Newspaper3k)"
        
        news_items.append({
    "title": entry.title,
    "link": real_url,   # ← 중요
    "content": content,
    "source_type": source_type
})

    
    return news_items

def classify_intent(user_input):
    system_prompt = "사용자가 뉴스 검색을 원하면 'SEARCH:키워드', 아니면 'CHAT'이라고 답하세요."
    input_tokens = calc_tokens(system_prompt + user_input)

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_input}]
        )
        content = response.choices[0].message.content.strip()
        st.session_state.total_tokens += (input_tokens + calc_tokens(content))

        if content.startswith("SEARCH:"):
            return {"type": "SEARCH", "keyword": content.split("SEARCH:")[1].strip()}
        return {"type": "CHAT", "keyword": None}
    except:
        return {"type": "CHAT", "keyword": None}

def get_llm_response(prompt, context_type="general", news_data=None):
    messages = st.session_state.messages.copy()
    
    if context_type == "news_summary" and news_data:
        news_context = ""
        for idx, item in enumerate(news_data, 1):
            news_context += f"[{idx}] {item['title']} ({item['source_type']})\n링크: {item['link']}\n내용: {item['content']}\n\n"
            
        system_prompt = "당신은 심층 뉴스 분석가입니다. [뉴스 데이터]를 보고 답변하세요. '웹사이트 본문'이 있다면 그 내용을 적극 인용하세요."
        user_content = f"질문: {prompt}\n\n[뉴스 데이터]\n{news_context}"
        
        messages_for_api = [{"role": "system", "content": system_prompt}] + messages
        messages_for_api.append({"role": "user", "content": user_content})
    else:
        messages_for_api = [{"role": "system", "content": "도움이 되는 챗봇입니다."}] + messages
        messages_for_api.append({"role": "user", "content": prompt})

    all_text = "".join([str(m["content"]) for m in messages_for_api])
    input_tokens = calc_tokens(all_text)

    try:
        stream = client.chat.completions.create(model=MODEL_NAME, messages=messages_for_api, stream=True)
        return stream, input_tokens
    except Exception as e:
        return f"에러: {e}", 0

# --- 메인 로직 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("무엇을 도와드릴까요?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        intent_result = classify_intent(prompt)
        stream_response = None
        input_tokens = 0
        
        if intent_result["type"] == "SEARCH":
            keyword = intent_result["keyword"]
            with st.status(f"🕵️ '{keyword}' 분석 중...", expanded=True) as status:
                news_items = get_news_data(keyword)
                
                # 성공 개수 확인
                success = sum(1 for item in news_items if "Newspaper3k" in item['source_type'])
                if success > 0:
                    status.update(label=f"✅ {success}건 원문 분석 성공!", state="complete", expanded=False)
                else:
                    status.update(label="⚠️ 일부 보안 접속 실패 (요약본 사용)", state="complete", expanded=False)
                
                stream_response, input_tokens = get_llm_response(prompt, "news_summary", news_items)
        else:
            stream_response, input_tokens = get_llm_response(prompt, "general")

        if stream_response and not isinstance(stream_response, str):
            for chunk in stream_response:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            st.session_state.total_tokens += (input_tokens + calc_tokens(full_response))
            message_placeholder.markdown(full_response)
        else:
            message_placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})