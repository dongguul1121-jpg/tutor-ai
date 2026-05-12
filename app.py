import streamlit as st
import google.generativeai as genai
import extra_streamlit_components as stx
import time
import io
import base64
import json
from PIL import Image

import firebase_admin
from firebase_admin import credentials, firestore

# ==========================================
# 1. 파이어베이스(Firestore) 연결 설정
# ==========================================
if not firebase_admin._apps:
    try:
        # 기존에 스트림릿 Secrets에 넣은 'FIREBASE_JSON'을 그대로 사용합니다.
        raw_secret = st.secrets["FIREBASE_JSON"]
        key_dict = json.loads(raw_secret)
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error("🚨 파이어베이스 연결에 실패했습니다. Secrets 설정을 확인해주세요.")
        st.stop()

db = firestore.client()

# ==========================================
# 2. Gemini AI 및 시스템 프롬프트 설정
# ==========================================
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-2.0-flash')

knowledge_text = ""
try:
    with open("coze knowledge.txt", "r", encoding="utf-8") as f:
        knowledge_text = f.read()
except FileNotFoundError:
    st.error("'coze knowledge.txt' 파일이 필요합니다.")

system_prompt = f"""
너는 수능 영어 독해의 절대 강자, '동국 튜터 AI'야.
[동국 튜터 독해 비법 시작]
{knowledge_text}
[동국 튜터 독해 비법 끝]

# Output Format
0. [유형 및 주제]: (반드시 이 형식으로 첫 줄 작성)
### 1. 📖 전체 해석
### 2. 🧠 문제 풀이 방법 (동국 튜터식 사고 흐름)
### 3. 🔑 주요 포인트 & 구문 독해 도구
"""

# ==========================================
# 3. 디자인 및 자동 로그인 (쿠키 사용)
# ==========================================
st.set_page_config(page_title="동국 튜터 AI", page_icon="🎓")

st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    </style>
""", unsafe_allow_html=True)

cookie_manager = stx.CookieManager(key="dongguk_cookie_manager")
time.sleep(0.1)
saved_user = cookie_manager.get(cookie="current_user")

if saved_user:
    st.session_state.authenticated = True
    st.session_state.current_user = saved_user
elif "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 로그인")
    user_id = st.text_input("ID")
    user_pw = st.text_input("PW", type="password")
    if st.button("로그인"):
        if user_id in st.secrets["users"] and st.secrets["users"][user_id] == user_pw:
            st.session_state.authenticated = True
            st.session_state.current_user = user_id
            cookie_manager.set("current_user", user_id, max_age=30*24*60*60)
            st.rerun()
        else:
            st.error("로그인 정보를 확인하세요.")
    st.stop()

# ==========================================
# 4. 메뉴 구성 및 세션 데이터 초기화
# ==========================================
m1, m2 = st.columns([15, 1])
with m2:
    with st.popover("⋮"):
        if st.button("🏠 메인"): st.session_state.page = "main"; st.rerun()
        if st.button("📚 서재"): st.session_state.page = "library"; st.rerun()
        if st.button("🚪 로그아웃"): 
            cookie_manager.delete("current_user")
            st.session_state.authenticated = False
            st.session_state.library = []
            st.rerun()

if "page" not in st.session_state: st.session_state.page = "main"
if "current_explanation" not in st.session_state: st.session_state.current_explanation = None
if "current_image" not in st.session_state: st.session_state.current_image = None

# DB 데이터 불러오기 (한 번만 실행)
if "library" not in st.session_state or not st.session_state.library:
    st.session_state.library = []
    if st.session_state.get("current_user"):
        docs = db.collection("library").where("user", "==", st.session_state.current_user).stream()
        for doc in docs:
            item = doc.to_dict(); item["id"] = doc.id
            st.session_state.library.append(item)

# ==========================================
# 5. 화면별 기능 구현
# ==========================================

# 📚 [라이브러리 화면]
if st.session_state.page == "library":
    st.title("📚 나의 문제 서재")
    if not st.session_state.library:
        st.info("저장된 문제가 없습니다. 메인에서 문제를 풀어보세요!")
    else:
        # 즐겨찾기 우선 + 최신순 정렬
        sorted_list = sorted(st.session_state.library[::-1], key=lambda x: x.get("bookmarked", False), reverse=True)
        for i, item in enumerate(sorted_list):
            star = "⭐" if item.get("bookmarked") else "☆"
            with st.expander(f"{star} {item.get('title', '제목 없음')}"):
                # ⭐️ 저장된 사진(Base64)이 있으면 출력
                if item.get("image_base64"):
                    st.image(item["image_base64"], use_container_width=True)
                st.write(item.get("content"))
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(f"{star} 즐겨찾기", key=f"bk_{i}"):
                        new_s = not item.get("bookmarked")
                        db.collection("library").document(item["id"]).update({"bookmarked": new_s})
                        st.session_state.library = [] # 리셋 후 리로드 유도
                        st.rerun()
                with c2:
                    if st.button("🗑️ 삭제", key=f"del_{i}"):
                        db.collection("library").document(item["id"]).delete()
                        st.session_state.library = [x for x in st.session_state.library if x["id"] != item["id"]]
                        st.rerun()

# 🏠 [메인 화면]
elif st.session_state.page == "main":
    st.title("🎓 동국 튜터 AI")
    up_file = st.file_uploader("수능 영어 문제 사진을 올려주세요.", type=["jpg", "png", "jpeg"])
    
    if up_file:
        if "last_file" not in st.session_state or st.session_state.last_file != up_file.name:
            st.session_state.current_explanation = None
            st.session_state.current_image = Image.open(up_file)
            st.session_state.last_file = up_file.name
        
        st.image(st.session_state.current_image, caption="업로드된 문제", use_container_width=True)
        
        if st.session_state.current_explanation is None:
            if st.button("동국 튜터의 해설 보기"):
                with st.spinner("AI가 지문을 분석하고 사진을 압축 저장하는 중입니다..."):
                    try:
                        # 1. AI 분석
                        res = model.generate_content([system_prompt, st.session_state.current_image])
                        st.session_state.current_explanation = res.text
                        title = res.text.split('\n')[0].replace("0. [유형 및 주제]: ", "").strip()
                        
                        # ⭐️ 2. 사진 압축 & Base64 변환 (Firestore 저장용)
                        img_small = st.session_state.current_image.copy()
                        img_small.thumbnail((800, 800))
                        buf = io.BytesIO()
                        img_small.save(buf, format="JPEG", quality=60) # 용량 최적화
                        img_str = base64.b64encode(buf.getvalue()).decode()
                        img_data_url = f"data:image/jpeg;base64,{img_str}"
                        
                        # 3. DB 저장
                        new_ref = db.collection("library").document()
                        new_data = {
                            "user": st.session_state.current_user,
                            "title": title if title else "새로운 문제 해설",
                            "content": res.text,
                            "bookmarked": False,
                            "image_base64": img_data_url
                        }
                        new_ref.set(new_data)
                        new_data["id"] = new_ref.id
                        st.session_state.library.append(new_data)
                        st.success("✅ 라이브러리에 안전하게 저장되었습니다!")
                        
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {e}")

    if st.session_state.current_explanation:
        st.divider()
        st.subheader("💡 동국 튜터의 명쾌한 해설")
        st.write(st.session_state.current_explanation)
