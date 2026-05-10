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

# 4. 동국 튜터의 영독해 페르소나 및 프롬프트 설정 (지식 통째로 주입)
system_prompt = f"""
너는 수능 영어 독해의 절대 강자, '동국 튜터 AI'야.
사용자가 올린 수능 영어 문제 사진을 분석해서 해설해야 해.
반드시 아래 제공된 [동국 튜터 독해 비법]의 알고리즘과 용어를 엄격하게 적용해서 해설해.

[동국 튜터 독해 비법 시작]
{knowledge_text}
[동국 튜터 독해 비법 끝]

# Output Format
- 💡 [문제 유형 및 타겟 시그널]
- 🔍 [동국 튜터식 뼈대 스캐닝] (비법에 있는 가중치 조절, 등식화 등 적용)
- 🎯 [정답 도출 및 오답 소거]
- 📝 [실전 Action Plan 요약]
"""

# 5. 웹사이트 화면 구성
st.set_page_config(page_title="동국 튜터 AI", page_icon="🎓")
hide_menu_style = """
<style>
/* 1. 상단 기본 메뉴와 헤더를 아예 공간째로 날려버림 */
header {visibility: hidden !important; display: none !important;}
#MainMenu {visibility: hidden !important; display: none !important;}
[data-testid="stHeader"] {visibility: hidden !important; display: none !important;}
[data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}

/* 2. 하단 Made with Streamlit 워터마크 숨기기 */
footer {visibility: hidden !important;}

/* 3. 종이배(Deploy) 버튼의 모든 가능한 이름표 강제 삭제 */
.stAppDeployButton {display: none !important;}
[data-testid="stAppDeployButton"] {display: none !important;}
button[kind="header"] {display: none !important;}

/* 4. 프로필 아이콘 및 기타 배지 숨기기 */
.viewerBadge_container {display: none !important;}
.viewerBadge_link {display: none !important;}
</style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)
st.title("🎓 수능 영어 풀이 AI")
st.markdown("막히는 문제 사진을 올려주시면, 동국 튜터의 논리 독해 비법으로 뼈대를 발라드립니다!")

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
