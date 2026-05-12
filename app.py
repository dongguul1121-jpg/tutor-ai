import streamlit as st
import google.generativeai as genai
import extra_streamlit_components as stx
import time
from PIL import Image

import json
import firebase_admin
from firebase_admin import credentials, firestore

# 👇👇 이 부분을 엑스레이 코드로 덮어씁니다 👇👇
if not firebase_admin._apps:
    try:
        raw_secret = st.secrets["FIREBASE_JSON"]
        key_dict = json.loads(raw_secret)
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        # 에러가 나면 빨간 줄 대신, 금고 안의 내용물을 화면에 그대로 토해냅니다!
        st.error("🚨 열쇠(JSON) 모양에 문제가 있습니다! 아래 박스 안의 글자를 확인해주세요.")
        st.code(st.secrets.get("FIREBASE_JSON", "열쇠가 비어있습니다!"))
        st.error(f"파이썬의 불만(에러 내용): {e}")
        st.stop()

db = firestore.client()

# 1. Gemini API 키 설정 (본인의 키로 변경하세요)
# 서버의 안전한 금고(secrets)에서 키를 꺼내오도록 수정
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)

# 2. 사용할 AI 모델 설정
model = genai.GenerativeModel('gemini-2.5-flash')

# 3. ⭐️ 지식 베이스(텍스트 파일) 읽어오기 ⭐️
knowledge_text = ""
try:
    with open("coze knowledge.txt", "r", encoding="utf-8") as f:
        knowledge_text = f.read()
except FileNotFoundError:
    st.error("오류: 'coze knowledge.txt' 파일을 같은 폴더에 넣어주세요!")

             
# 4. 동국 튜터의 영독해 페르소나 및 프롬프트 설정 (실전 사고 흐름 강화 버전)
system_prompt = f"""
너는 수능 영어 독해의 절대 강자, '동국 튜터 AI'야. 
사용자가 올린 문제 사진을 분석할 때, 학생이 옆에서 과외를 받는 것처럼 '사고의 전개 과정'을 생중계하듯 해설해 줘.

[동국 튜터 독해 비법 시작]
{knowledge_text}
[동국 튜터 독해 비법 끝]

# Output Format (반드시 아래 순서를 지킬 것)
[유형 및 주제]: (예: [빈칸 추론] 기후 변화의 역설) - 반드시 이 형식으로 첫 줄에 작성해줘.

### 1. 📖 전체 해석
- 지문 전체 내용을 매끄러운 우리말로 먼저 보여줘서 맥락을 잡게 해.

### 2. 🧠 문제 풀이 방법 (동국 튜터식 실전 사고 흐름)
- 지문의 첫 문장부터 마지막 문장까지, 실전에서 학생이 해야 하는 '생각'을 순서대로 기술해.
- **[문장 1]**: 이 문장에서 잡아야 할 핵심 소재와 속성(+)은 무엇인지, 이때 쓰인 '구문 도구'(예: 도치, 강조구문, 관계사 등)를 언급하며 뼈대를 발라내.
- **[문장 2]**: 앞 문장과 어떤 관계(등식, 대조, 환언)로 연결되는지, 논리적 연결 고리를 짚어줘.
- 이 과정을 마지막 문장까지 반복하며, 중간에 등장하는 '타겟 시그널'이 사고방식을 어떻게 바꾸는지 설명해.
- **[최종 정답 도출]**: 위 사고 과정을 통해 정답 선지가 나올 수밖에 없는 이유와 매력적 오답의 제거 원리를 한 줄로 정리해.

### 3. 🔑 주요 포인트 & 구문 독해 도구
- 지문에서 반드시 챙겨야 할 1순위 핵심 어휘 3~5개.
- 지문 내에서 가장 구조가 복잡했던 문장을 하나 선정해, 구문 도구를 활용한 '구조 분석 가이드'를 제공해.
"""


# 5. 웹사이트 화면 구성
st.set_page_config(page_title="동국 튜터 AI", page_icon="🎓")

hide_menu_style = """
<style>
/* 1. 상단 기본 메뉴와 헤더 숨기기 */
header {visibility: hidden !important; display: none !important;}
#MainMenu {visibility: hidden !important; display: none !important;}
[data-testid="stHeader"] {visibility: hidden !important; display: none !important;}
[data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}

/* 2. 하단 워터마크 숨기기 */
footer {visibility: hidden !important;}

/* 3. 종이배 및 아이콘 숨기기 */
.stAppDeployButton {display: none !important;}
[data-testid="stAppDeployButton"] {display: none !important;}
button[kind="header"] {display: none !important;}
.viewerBadge_container {display: none !important;}
.viewerBadge_link {display: none !important;}

/* 🎯 4. 제목 글자 크기 모바일 최적화 (새로 추가된 부분) */
h1 {
    word-break: keep-all !important; /* 단어 단위로 줄바꿈 방지 */
}

/* 화면 너비가 768px 이하(모바일)일 때 글자 크기를 확 줄임 */
@media screen and (max-width: 768px) {
    h1 {
        font-size: 1.6rem !important; 
    }
}
</style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)


# 👇👇 [자동 로그인 시스템 적용] 👇👇

# 수정 코드 (key 추가)
cookie_manager = stx.CookieManager(key="dongguk_cookie_manager")


# 스트림릿이 쿠키를 읽어올 아주 짧은 시간(0.1초)을 줍니다.
time.sleep(0.1)
saved_user = cookie_manager.get(cookie="current_user")

# 2. 방문증이 있으면 자동 통과, 없으면 로그인 창 띄우기
if saved_user:
    st.session_state.authenticated = True
    st.session_state.current_user = saved_user
elif "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# (이전 쿠키 불러오는 코드는 그대로 유지)

if not st.session_state.authenticated:
    st.title("🔒 동국 튜터 AI 로그인")
    st.markdown("수강생 전용 공간입니다. 발급받은 아이디와 비밀번호를 입력하세요.")
    
    user_id = st.text_input("아이디 (ID)")
    user_pw = st.text_input("비밀번호 (Password)", type="password")
    
    # ⭐️ 핵심 1: 자동 로그인 체크박스 만들기 (기본값은 체크된 상태)
    auto_login = st.checkbox("자동 로그인 (30일 유지)", value=True)
    
    if st.button("로그인"):
        if user_id in st.secrets["users"] and st.secrets["users"][user_id] == user_pw:
            st.session_state.authenticated = True
            st.session_state.current_user = user_id
            
            # ⭐️ 핵심 2: 자동 로그인에 체크했을 때만 방문증(쿠키)을 발급!
            if auto_login:
                cookie_manager.set("current_user", user_id, max_age=30*24*60*60)
            
            time.sleep(0.5) 
            st.rerun()
        else:
            st.error("❌ 아이디 또는 비밀번호가 올바르지 않습니다.")
    st.stop()

# (이하 우측 상단 로그아웃 메뉴 등 기존 코드 동일)


# 3. 우측 상단 메뉴 & 로그아웃 기능 (방문증 파기 기능 추가)


# 1. 상단 메뉴 (페이지에 상관없이 항상 노출)
menu_col1, menu_col2 = st.columns([15, 1])
with menu_col2:
    with st.popover("⋮"):
        if st.button("🏠 메인 화면", use_container_width=True):
            st.session_state.page = "main"
            st.rerun()
        if st.button("📚 라이브러리", use_container_width=True):
            st.session_state.page = "library"
            st.rerun()
        if st.button("🚪 로그아웃", use_container_width=True):
            try:
                cookie_manager.delete("current_user")
            except KeyError:
                pass 
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.rerun()

# 2. 세션 상태 초기화
if "page" not in st.session_state:
    st.session_state.page = "main"
if "library" not in st.session_state:
    st.session_state.library = []
if "current_explanation" not in st.session_state:
    st.session_state.current_explanation = None

# --- 화면 분기 처리 ---

# 📚 라이브러리 화면
if st.session_state.page == "library":
    st.title("📚 나의 문제 라이브러리")
    
    if len(st.session_state.library) == 0:
        st.info("아직 저장된 문제가 없습니다. 메인 화면에서 문제를 풀어보세요!")
    else:
        sorted_lib = sorted(st.session_state.library, key=lambda x: x["bookmarked"], reverse=True)
        for i, item in enumerate(sorted_lib):
            star = "⭐️" if item["bookmarked"] else "☆"
            with st.expander(f"{star} {item['title']}"):
                if "image" in item and item["image"] is not None:
                    st.image(item["image"], caption="업로드했던 문제", use_column_width=True)
                    st.divider() # 사진과 해설 사이에 얇은 선을 하나 그어줍니다.
                st.write(item["content"])
                col1, col2 = st.columns(2)
                
                with col1:
                    btn_label = "⭐ 즐겨찾기 해제" if item["bookmarked"] else "☆ 즐겨찾기 설정"
                    if st.button(btn_label, key=f"bookmark_{i}"):
                        item_index = st.session_state.library.index(item)
                        st.session_state.library[item_index]["bookmarked"] = not item["bookmarked"]
                        st.rerun()
                with col2:
                    if st.button("🗑️ 삭제", key=f"del_{i}"):
                        item_index = st.session_state.library.index(item)
                        del st.session_state.library[item_index]
                        st.rerun()

# 🏠 메인 화면 (핵심: elif로 묶어서 라이브러리 화면일 때는 실행되지 않게 함)
elif st.session_state.page == "main":
    st.title("🎓 동국 튜터 수능 영어 AI")
    st.info(f"환영합니다, {st.session_state.current_user}님! 오늘도 논리 독해로 뼈대를 발라봅시다.")

    uploaded_file = st.file_uploader("수능 영어 문제 사진을 업로드하세요", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="업로드된 문제", use_column_width=True)
        
        if st.button("동국 튜터식 해설 보기"):
            with st.spinner("지문을 분석하고 있습니다..."):
                try:
                    response = model.generate_content([system_prompt, image])
                    st.session_state.current_explanation = response.text
                    
                    full_text = response.text
                    title_line = full_text.split('\n')[0].replace("0. [유형 및 주제]: ", "").strip()
                    
                    if not any(item['content'] == full_text for item in st.session_state.library):
                        st.session_state.library.append({
                            "title": title_line if title_line else "새로운 문제 해설",
                            "content": full_text,
                            "bookmarked": False,
                            "image": image
                        })
                        st.success("✅ 라이브러리에 저장이 완료되었습니다!")
                        
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")

    # 기억 장소에 해설이 있다면 메인 화면에서 항상 노출
    if st.session_state.current_explanation:
        st.subheader("💡 동국 튜터의 명쾌한 해설")
        st.write(st.session_state.current_explanation)

              

