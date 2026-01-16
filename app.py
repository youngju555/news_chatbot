import streamlit as st
import feedparser
import os
import urllib.parse
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
import urllib3

# SSL 경고 무시 (배포 환경 노이즈 제거)
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

def calc_tokens(text):
    if not text: return 0
    return int(len(text) * 1.2)

# [최종] BeautifulSoup + 쿠키 사용 (배포 시 가장 안정적)
def fetch_article_content(url):
    try:
        # 1. 헤더 위장
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.google.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        }
        
        # 2. 쿠키 설정 (구글 보안 우회 시도)
        cookies = {"CONSENT": "YES+cb.20210720-07-p0.en+FX+417"}

        # 3. 요청 보내기 (verify=False로 SSL 에러 방지)
        session = requests.Session()
        response = session.get(url, headers=headers, cookies=cookies, timeout=5, verify=False)
        
        # 4. 파싱
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 불필요한 태그 제거
        for tag in soup(["script", "style", "header", "footer", "nav", "aside", "form", "iframe", "noscript"]):
            tag.decompose()
            
        # 본문 추출
        text_content = ""
        paragraphs = soup.find_all(['p', 'div'])
        for p in paragraphs:
            text = p.get_text().strip()
            if len(text) > 30: 
                text_content += text + " "
        
        if len(text_content) < 200:
            return None
            
        return text_content[:2000] + "..."
        
    except Exception:
        return None

def get_news_data(keyword):
    encoded_keyword = urllib.parse.quote(keyword)
    rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
    
    feed = feedparser.parse(rss_url)
    news_items = []
    
    if not feed.entries:
        return []

    for i, entry in enumerate(feed.entries[:3]):
        content = entry.get('summary', '요약 없음')
        source_type = "Google RSS 요약"
        
        # 상위 2개 크롤링 시도
        if i < 2:
            crawled_text = fetch_article_content(entry.link)
            if crawled_text:
                content = crawled_text
                source_type = "🌐 웹사이트 본문 (분석 성공)"
        
        news_items.append({
            "title": entry.title,
            "link": entry.link,
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
                
                success = sum(1 for item in news_items if "분석 성공" in item['source_type'])
                if success > 0:
                    status.update(label=f"✅ {success}건 원문 분석 성공!", state="complete", expanded=False)
                else:
                    status.update(label="⚠️ 요약본으로 분석합니다 (보안 접속 불가)", state="complete", expanded=False)
                
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