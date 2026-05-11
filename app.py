import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

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


# 👇👇 [정식 ID/PW 로그인 시스템] 👇👇

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 동국 튜터 AI 로그인")
    st.markdown("수강생 전용 공간입니다. 발급받은 아이디와 비밀번호를 입력하세요.")
    
    # 1. 아이디와 비밀번호 입력 칸 두 개 만들기
    user_id = st.text_input("아이디 (ID)")
    user_pw = st.text_input("비밀번호 (Password)", type="password")
    
    if st.button("로그인"):
        # 2. 금고([users] 명단)에 입력한 아이디가 있는지, 그리고 비밀번호가 맞는지 확인
        if user_id in st.secrets["users"] and st.secrets["users"][user_id] == user_pw:
            st.session_state.authenticated = True
            st.session_state.current_user = user_id  # 누가 로그인했는지 기억해둠
            st.rerun() # 로그인 성공! 화면 새로고침
        else:
            st.error("❌ 아이디 또는 비밀번호가 올바르지 않습니다.")
            
    # 로그인 전까지는 무조건 화면 멈춤
    st.stop()
    
# 👆👆 여기까지 [로그인 시스템] 끝 👆👆


# 👇👇 지운 자리에 이 코드를 통째로 붙여넣으세요 👇👇

# 1. 우측 상단 '점 3개' 로그아웃 버튼 만들기
menu_col1, menu_col2 = st.columns([15, 1])
with menu_col2:
    with st.popover("⋮"):
        if st.button("🚪 로그아웃", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.rerun()

# 2. 메인 화면 제목
st.title("🎓 동국 튜터 수능 영어 AI")
st.info(f"환영합니다, {st.session_state.current_user}님! 오늘도 논리 독해로 뼈대를 발라봅시다.")

# 👆👆 여기까지입니다. 이 아래로는 원래 있던 문제 사진 업로드 코드(st.file_uploader)가 자연스럽게 이어지면 됩니다! 👆👆


# 파일 업로드 버튼
uploaded_file = st.file_uploader("수능 영어 문제 사진을 업로드하세요", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="업로드된 문제", use_column_width=True)
    
    if st.button("동국 튜터식 해설 보기"):
        with st.spinner("비법 지식을 바탕으로 지문의 뼈대를 분석하고 있습니다..."):
            try:
                response = model.generate_content([system_prompt, image])
                st.subheader("💡 동국 튜터의 명쾌한 해설")
                st.write(response.text)
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
