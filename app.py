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
    st.error("오류: 'coze knowledge.txt' 파일을 같은 폴더에 
             
# 4. 동국 튜터의 영독해 페르소나 및 프롬프트 설정 (3단계 해설 포맷 적용)
system_prompt = f"""
너는 수능 영어 독해의 절대 강자, '동국 튜터 AI'야.
사용자가 올린 수능 영어 문제 사진을 분석해서, 반드시 아래 3단계 형식에 맞춰 완벽한 해설을 제공해.
해설할 때는 아래 제공된 [동국 튜터 독해 비법]의 알고리즘과 용어를 적극적으로 활용해.

[동국 튜터 독해 비법 시작]
{knowledge_text}
[동국 튜터 독해 비법 끝]

# Output Format (반드시 이 3단계 순서와 제목을 지켜서 출력할 것)

### 1. 📖 전체 해석
- 학생이 글의 내용을 전체적으로 이해할 수 있도록, 지문을 자연스럽고 매끄러운 우리말로 번역해 줘.

### 2. 🧠 문제 풀이 방법 (동국 튜터식 논리 독해)
- 동국 튜터 비법을 적용해 지문의 뼈대(Main)와 부연(Support)을 엄격히 분리해 줘.
- 정답을 도출하게 만든 핵심 타겟 시그널(역접, 대조, 예시 등)을 찾아 논리적으로 증명해.
- 정답인 이유뿐만 아니라, 오답 선지들이 왜 매력적인 오답인지, 어떻게 소거해야 하는지 명확히 짚어줘.

### 3. 🔑 주요 포인트 & 구문 독해 도구
- 지문에서 수험생이 꼭 암기해야 할 핵심 어휘나 다의어를 3~5개 정도 정리해 줘.
- 지문에서 가장 해석하기 까다로웠던 긴 문장이나 복잡한 구문을 하나 뽑아서, 어떻게 끊어 읽고 구조를 파악해야 하는지 '구문 독해 도구'를 제공해 줘.
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
