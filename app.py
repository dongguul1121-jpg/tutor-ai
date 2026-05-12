import streamlit as st
import google.generativeai as genai
import extra_streamlit_components as stx
import time
from PIL import Image
import json
import firebase_admin
from firebase_admin import credentials, firestore


if not firebase_admin._apps:
    try:
        raw_secret = st.secrets["FIREBASE_JSON"]
        key_dict = json.loads(raw_secret)
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error("🚨 열쇠(JSON) 모양에 문제가 있습니다! 아래 박스 안의 글자를 확인해주세요.")
        st.code(st.secrets.get("FIREBASE_JSON", "열쇠가 비어있습니다!"))
        st.error(f"파이썬의 불만(에러 내용): {e}")
        st.stop()
db = firestore.client()

# 1. Gemini API 키 설정 (본인의 키로 변경하세요)

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

# ==========================================
# 1. 초기 설정 및 세션 상태 정의
# ==========================================
# (기본 import 및 파이어베이스 설정은 그대로 두세요)

# 세션 상태 초기화 (제일 먼저 실행되어야 함)
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "logout_active" not in st.session_state:
    st.session_state.logout_active = False
if "page" not in st.session_state:
    st.session_state.page = "main"
if "library" not in st.session_state:
    st.session_state.library = []

# ==========================================
# 2. 쿠키 읽기 및 자동로그인 로직 (핵심)
# ==========================================
cookie_manager = stx.CookieManager(key="dongguk_cookie_manager_v2") # 키를 살짝 바꿔서 초기화 유도

# 쿠키를 읽어올 수 있도록 아주 짧게 대기
time.sleep(0.2)
saved_user = cookie_manager.get(cookie="current_user")

# ⭐️ 자동로그인 핵심 로직
# 아직 로그인이 안 된 상태인데, 쿠키(방문증)가 있고 + 방금 로그아웃 버튼을 누른 게 아니라면!
if not st.session_state.authenticated and saved_user and not st.session_state.logout_active:
    st.session_state.authenticated = True
    st.session_state.current_user = saved_user
    
    # 로그인 성공했으니 DB에서 라이브러리 데이터를 즉시 새로고침
    st.session_state.library = []
    docs = db.collection("library").where("user", "==", saved_user).stream()
    for doc in docs:
        item = doc.to_dict()
        item["id"] = doc.id
        st.session_state.library.append(item)
    
    st.rerun() # 모든 준비가 끝났으니 화면을 새로고침해서 메인으로 진입!

# ==========================================
# 3. 로그인 창 (로그인 안 된 경우)
# ==========================================
if not st.session_state.authenticated:
    st.title("🔒 동국 튜터 AI 로그인")
    user_id = st.text_input("아이디 (ID)")
    user_pw = st.text_input("비밀번호 (Password)", type="password")
    auto_login = st.checkbox("자동 로그인 (30일 유지)", value=True)
    
    if st.button("로그인", key="login_btn"):
        if user_id in st.secrets["users"] and st.secrets["users"][user_id] == user_pw:
            st.session_state.authenticated = True
            st.session_state.current_user = user_id
            st.session_state.logout_active = False # 로그아웃 상태 해제
            
            if auto_login:
                cookie_manager.set("current_user", user_id, max_age=30*24*60*60)
            
            # DB 데이터 로드
            st.session_state.library = []
            docs = db.collection("library").where("user", "==", user_id).stream()
            for doc in docs:
                item = doc.to_dict(); item["id"] = doc.id
                st.session_state.library.append(item)
            
            st.rerun()
        else:
            st.error("❌ 정보를 확인해주세요.")
    st.stop() # 로그인 전까지는 아래 코드를 실행하지 않음

# ==========================================
# 4. 로그아웃 버튼 (메뉴 부분)
# ==========================================
# ... (중략: 메뉴 popover 코드 안의 로그아웃 버튼) ...
if st.button("🚪 로그아웃", key="btn_logout", use_container_width=True):
    cookie_manager.delete("current_user") # 쿠키 파기
    st.session_state.logout_active = True # 로그아웃 깃발 올림
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.library = []
    st.rerun()

# 3. 우측 상단 메뉴 & 로그아웃 기능 (방문증 파기 기능 추가)
if "page" not in st.session_state:
    st.session_state.page = "main"
if "library" not in st.session_state:
    st.session_state.library = []
    # ⭐️ 창고(DB)에서 내 문제들을 꺼내오는 코드!
    if st.session_state.get("current_user"):
        # 내 아이디("user") 꼬리표가 붙은 문제들만 'library' 폴더에서 싹 다 가져옵니다.
        docs = db.collection("library").where("user", "==", st.session_state.current_user).stream()
        for doc in docs:
            item = doc.to_dict()
            item["id"] = doc.id # DB에서 발급받은 고유 번호표를 붙여줍니다 (나중에 삭제할 때 필요)
            st.session_state.library.append(item)

if "current_explanation" not in st.session_state:
    st.session_state.current_explanation = None
if "current_image" not in st.session_state:
    st.session_state.current_image = None

# 1. 상단 메뉴 구성 (페이지 상단 고정)
menu_col1, menu_col2 = st.columns([15, 1])
with menu_col2:
    # ⭐️ key값에 현재 페이지를 넣어 화면 이동 시 메뉴가 자동으로 닫히게 합니다.
    with st.popover("⋮", key=f"nav_popover_{st.session_state.page}"):
        if st.button("🏠 메인 화면", key="btn_go_main", use_container_width=True):
            st.session_state.page = "main"
            st.rerun()
            
        if st.button("📚 라이브러리", key="btn_go_lib", use_container_width=True):
            st.session_state.page = "library"
            st.rerun()
            
        # ⭐️ 에러가 났던 로그아웃 버튼 구역입니다.
        # --- 로그아웃 버튼 구역 ---
        if st.button("🚪 로그아웃", key="btn_logout", use_container_width=True):
            cookie_manager.delete("current_user") # 쿠키 파기
            st.session_state.logout_active = True # 로그아웃 깃발 올림
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.session_state.library = []
            st.rerun()

# --- 화면 분기 처리 ---



# 📚 라이브러리 화면

if st.session_state.page == "library":
    st.title("📚 나의 문제 라이브러리")
    if len(st.session_state.library) == 0:
        st.info("아직 저장된 문제가 없습니다. 메인 화면에서 문제를 풀어보세요!")
    else:
        sorted_lib = sorted(st.session_state.library[::-1], key=lambda x: x["bookmarked"], reverse=True)
        for i, item in enumerate(sorted_lib):
            star = "⭐️" if item["bookmarked"] else "☆"
            with st.expander(f"{star} {item['title']}"):
                if "image" in item and item["image"] is not None:
                    st.image(item["image"], caption="업로드했던 문제", use_column_width=True)
                    st.divider() 
                st.write(item["content"])
                col1, col2 = st.columns([6, 1])    
                with col1:
                    # 즐겨찾기 버튼은 왼쪽 칸에 위치 (글자 길이에 맞춰 정렬됨)
                    btn_label = "⭐ 즐겨찾기 해제" if item.get("bookmarked", False) else "☆ 즐겨찾기 설정"
                    if st.button(btn_label, key=f"bookmark_{i}"):
                        new_status = not item.get("bookmarked", False)
                        db.collection("library").document(item["id"]).update({"bookmarked": new_status})
                        for entry in st.session_state.library:
                            if entry["id"] == item["id"]:
                                entry["bookmarked"] = new_status
                        st.rerun()
                        
                with col2:
                    # 삭제 버튼은 이제 상자의 가장 우측 끝 칸에 안착합니다!
                    if st.button("🗑️ 삭제", key=f"del_{i}", use_container_width=True):
                        db.collection("library").document(item["id"]).delete()
                        st.session_state.library = [e for e in st.session_state.library if e["id"] != item["id"]]
                        st.rerun()

elif st.session_state.page == "main":
    st.title("🎓 동국 튜터 수능 영어 AI")
    st.info(f"환영합니다, {st.session_state.current_user}님! 오늘도 논리 독해로 뼈대를 발라봅시다.")

    if "last_uploaded_file_name" not in st.session_state:
        st.session_state.last_uploaded_file_name = None
    uploaded_file = st.file_uploader("수능 영어 문제 사진을 업로드하세요", type=["jpg", "jpeg", "png"])
    
    # ⭐️ 1. 새 파일이 올라오면 '사진'과 '파일이름'을 단기 기억에 저장!
    if uploaded_file is not None:
        if st.session_state.last_uploaded_file_name != uploaded_file.name:
            st.session_state.current_explanation = None # 이전 해설 싹 지우기
            st.session_state.last_uploaded_file_name = uploaded_file.name
            st.session_state.current_image = Image.open(uploaded_file) # 새 사진 저장!

    # ⭐️ 2. 기억 장소에 사진이 있다면 무조건 화면에 띄웁니다! (갔다 와도 유지됨)
    if st.session_state.current_image is not None:
        st.image(st.session_state.current_image, caption="업로드된 문제", use_column_width=True)

        # ⭐️ 3. 사진은 있는데 '해설'이 아직 없을 때만 버튼을 보여줍니다!
        if st.session_state.current_explanation is None:
            if st.button("동국 튜터식 해설 보기"):
                with st.spinner("지문을 분석하고 있습니다..."):
                    try:
                        response = model.generate_content([system_prompt, st.session_state.current_image])
                        st.session_state.current_explanation = response.text
                        full_text = response.text
                        title_line = full_text.split('\n')[0].replace("0. [유형 및 주제]: ", "").strip()
  
                        if not any(item['content'] == full_text for item in st.session_state.library):                    
                            # ⭐️ 1. DB 창고에 저장할 데이터 상자를 만듭니다.
                            new_doc_ref = db.collection("library").document() # 새 문서(방) 열기
                            db_item = {
                                "id": new_doc_ref.id,
                                "user": st.session_state.current_user, # 누구의 문제인지 아이디 꼬리표 달기
                                "title": title_line if title_line else "새로운 문제 해설",
                                "content": full_text,
                                "bookmarked": False
                            }
                            # DB 창고에 진짜로 던져 넣기!
                            new_doc_ref.set(db_item)
                            
                            # ⭐️ 2. 방금 푼 문제를 지금 당장 화면에 띄우기 위해 (사진 포함해서) 단기 기억에도 넣습니다.
                            ui_item = db_item.copy()
                            ui_item["image"] = st.session_state.current_image
                            st.session_state.library.append(ui_item)
                            
                            st.success("✅ 라이브러리에 영구 저장이 완료되었습니다!")

                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {e}")


    if st.session_state.current_explanation:
        st.subheader("💡 동국 튜터의 명쾌한 해설")
        st.write(st.session_state.current_explanation)



