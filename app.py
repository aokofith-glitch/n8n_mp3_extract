import streamlit as st
import yt_dlp
import whisper
import os
import tempfile
from deep_translator import GoogleTranslator
import time
import re

# 페이지 설정
st.set_page_config(
    page_title="YouTube 가사 추출 및 번역",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"  # 사이드바 기본 상태 설정
)

# 접근성 개선을 위한 HTML 주입
st.markdown("""
<style>
/* 접근성 개선: 버튼에 aria-label 추가 */
button[data-testid="stBaseButton-headerNoPadding"] {
    aria-label: "메뉴 열기";
}
</style>
""", unsafe_allow_html=True)

# 자동 브라우저 열기는 run_app.py에서 처리

# 제목 및 헤더
st.title("🎵 YouTube 가사 추출 및 번역기")
st.markdown("### YouTube URL을 입력하면 MP3 파일과 가사를 추출하고 번역해드립니다.")

# 서버 상태 표시
with st.sidebar:
    st.markdown("---")
    st.markdown("### 🔧 서버 상태")
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8501))
        if result == 0:
            st.success("✅ 서버 실행 중")
            st.info(f"🌐 URL: http://localhost:8501")
        else:
            st.warning("⚠️ 서버 연결 확인 중...")
        sock.close()
    except:
        st.info("ℹ️ 서버 정보 확인 중...")

# 대시보드 스타일 정보 카드
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("### 🎬 YouTube URL")
    st.info("동영상 링크를 입력하세요")

with col2:
    st.markdown("### 🎵 MP3 추출")
    st.info("고품질 오디오로 변환")

with col3:
    st.markdown("### 🎤 가사 추출")
    st.info("AI 음성 인식 기술")

with col4:
    st.markdown("### 🌐 번역")
    st.info("10개 이상 언어 지원")

st.markdown("---")

# 사용 방법 섹션
st.header("📖 사용 방법")
how_to_col1, how_to_col2 = st.columns(2)

with how_to_col1:
    st.markdown("""
    ### 1️⃣ 단계별 가이드
    1. **YouTube URL 입력**: 아래 입력창에 YouTube 동영상 링크를 붙여넣으세요
    2. **번역 언어 선택**: 왼쪽 사이드바에서 원하는 번역 언어를 선택하세요
    3. **추출하기 클릭**: 버튼을 클릭하면 자동으로 처리됩니다
    4. **결과 확인**: MP3 다운로드 및 가사 확인이 가능합니다
    """)

with how_to_col2:
    st.markdown("""
    ### ⚡ 주요 기능
    - ✅ **고품질 MP3 추출**: YouTube 오디오를 고품질 MP3로 변환
    - ✅ **AI 가사 인식**: OpenAI Whisper로 정확한 가사 추출
    - ✅ **실시간 번역**: 10개 이상의 언어 지원
    - ✅ **줄별 비교**: 원본과 번역을 나란히 비교
    - ✅ **즉시 다운로드**: 추출된 MP3 파일 즉시 다운로드
    """)

st.markdown("---")

# 세션 상태 초기화
if 'audio_file_path' not in st.session_state:
    st.session_state.audio_file_path = None
if 'lyrics' not in st.session_state:
    st.session_state.lyrics = None
if 'translated_lyrics' not in st.session_state:
    st.session_state.translated_lyrics = None
if 'original_language' not in st.session_state:
    st.session_state.original_language = None

# 사이드바
st.sidebar.header("⚙️ 설정")

# 서버 상태 표시
st.sidebar.markdown("### 🔧 서버 상태")
try:
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 8501))
    if result == 0:
        st.sidebar.success("✅ 서버 실행 중")
        st.sidebar.info(f"🌐 http://localhost:8501")
    else:
        st.sidebar.warning("⚠️ 서버 확인 중...")
    sock.close()
except:
    st.sidebar.info("ℹ️ 서버 정보 확인 중...")

# FFmpeg 상태 확인 (함수 정의 후에 실행되도록 주석 처리하고 나중에 업데이트)
ffmpeg_status_placeholder = st.sidebar.empty()

st.sidebar.markdown("---")

# 번역 언어 선택
target_language = st.sidebar.selectbox(
    "번역 언어 선택",
    options=["한국어", "영어", "일본어", "중국어", "스페인어", "프랑스어", "독일어", "이탈리아어", "포르투갈어", "러시아어"],
    index=0
)

# 언어 코드 매핑
language_codes = {
    "한국어": "ko",
    "영어": "en",
    "일본어": "ja",
    "중국어": "zh",
    "스페인어": "es",
    "프랑스어": "fr",
    "독일어": "de",
    "이탈리아어": "it",
    "포르투갈어": "pt",
    "러시아어": "ru"
}

target_lang_code = language_codes[target_language]

# YouTube URL 입력 섹션
st.header("🎬 YouTube URL 입력")
st.markdown("아래에 YouTube 동영상 URL을 입력하세요:")

url = st.text_input(
    "YouTube URL:",
    placeholder="https://www.youtube.com/watch?v=... 또는 https://youtu.be/...",
    label_visibility="collapsed"
)

# 예시 URL 표시
with st.expander("💡 예시 URL 형식"):
    st.code("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    st.code("https://youtu.be/dQw4w9WgXcQ")
    st.markdown("위와 같은 형식의 YouTube URL을 사용하세요.")

col1, col2 = st.columns([1, 4])

with col1:
    extract_button = st.button("🎵 추출하기", type="primary", use_container_width=True, help="YouTube URL에서 오디오와 가사를 추출합니다")

with col2:
    if st.session_state.audio_file_path and os.path.exists(st.session_state.audio_file_path):
        with open(st.session_state.audio_file_path, "rb") as audio_file:
            st.download_button(
                label="📥 MP3 다운로드",
                data=audio_file,
                file_name="extracted_audio.mp3",
                mime="audio/mpeg",
                use_container_width=True,
                help="추출된 MP3 파일을 다운로드합니다"
            )

# 진행 상황 표시 (초기에는 숨김)
progress_bar = st.empty()
status_text = st.empty()

def find_ffmpeg():
    """FFmpeg 경로 찾기"""
    import shutil
    
    # 1. PATH에서 찾기
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        return os.path.dirname(ffmpeg_path)
    
    # 2. 프로젝트 폴더 내에서 찾기
    script_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        r'C:\ffmpeg\bin',  # 사용자가 추가한 경로
        r'C:\Program Files\ffmpeg\bin',  # 일반적인 설치 경로
        os.path.join(script_dir, 'ffmpeg', 'bin'),
        os.path.join(script_dir, 'ffmpeg-8.0.1', 'bin'),
        os.path.join(script_dir, 'ffmpeg-8.0.1', 'ffmpeg-8.0.1', 'bin'),  # 사용자가 제공한 경로
        os.path.join(script_dir, 'ffmpeg-8.0.1-full_build', 'bin'),
        # 직접 경로도 확인
        r'C:\Users\LG\Desktop\바이브코딩 경진대회\ffmpeg-8.0.1\ffmpeg-8.0.1\bin',
    ]
    
    for path in possible_paths:
        ffmpeg_exe = os.path.join(path, 'ffmpeg.exe')
        if os.path.exists(ffmpeg_exe):
            return path
    
    # bin 폴더가 없는 경우, 직접 ffmpeg.exe를 찾기
    direct_paths = [
        os.path.join(script_dir, 'ffmpeg-8.0.1', 'ffmpeg-8.0.1'),
        r'C:\Users\LG\Desktop\바이브코딩 경진대회\ffmpeg-8.0.1\ffmpeg-8.0.1',
    ]
    
    for base_path in direct_paths:
        # 하위 폴더에서 ffmpeg.exe 찾기
        for root, dirs, files in os.walk(base_path):
            if 'ffmpeg.exe' in files:
                return root
    
    return None

# FFmpeg 상태 표시 업데이트
with ffmpeg_status_placeholder.container():
    st.sidebar.markdown("### 🎬 FFmpeg 상태")
    ffmpeg_location = find_ffmpeg()
    if ffmpeg_location:
        ffmpeg_exe = os.path.join(ffmpeg_location, 'ffmpeg.exe')
        if os.path.exists(ffmpeg_exe):
            st.sidebar.success("✅ FFmpeg 설치됨")
            st.sidebar.caption(f"경로: {ffmpeg_location}")
        else:
            # PATH에서 찾은 경우
            import shutil
            ffmpeg_path = shutil.which('ffmpeg')
            if ffmpeg_path:
                st.sidebar.success("✅ FFmpeg 설치됨")
                st.sidebar.caption(f"경로: {ffmpeg_path}")
            else:
                st.sidebar.warning("⚠️ FFmpeg 미설치")
    else:
        st.sidebar.warning("⚠️ FFmpeg 미설치")
        with st.sidebar.expander("FFmpeg 설치 방법"):
            st.markdown("""
            **방법 1: winget 사용 (권장)**
            ```powershell
            winget install Gyan.FFmpeg
            ```
            
            **방법 2: 수동 설치**
            1. https://www.gyan.dev/ffmpeg/builds/ 방문
            2. "ffmpeg-release-full.7z" 다운로드
            3. 압축 해제 후 `bin` 폴더를 PATH에 추가
            
            **참고:** FFmpeg가 없어도 기본 기능은 사용 가능하지만, 
            일부 오디오 형식 변환이 제한될 수 있습니다.
            """)

def download_audio(url, output_path):
    """YouTube에서 오디오를 다운로드하고 MP3로 변환"""
    import shutil
    
    # FFmpeg 경로 찾기
    ffmpeg_location = find_ffmpeg()
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
    }
    
    # FFmpeg가 있으면 MP3로 변환, 없으면 원본 형식 사용
    if ffmpeg_location:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
        ydl_opts['ffmpeg_location'] = ffmpeg_location
    else:
        # FFmpeg가 없으면 이미 오디오 형식인 파일을 그대로 사용
        st.warning("⚠️ FFmpeg가 설치되어 있지 않습니다. 원본 오디오 형식을 사용합니다.")
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    # 다운로드된 파일 찾기
    base_path = output_path.replace('.mp3', '')
    for ext in ['.mp3', '.m4a', '.webm', '.opus', '.ogg']:
        if os.path.exists(base_path + ext):
            file_path = base_path + ext
            
            # MP3가 아니고 FFmpeg가 있으면 변환 시도
            if ext != '.mp3' and ffmpeg_location:
                try:
                    from pydub import AudioSegment
                    audio = AudioSegment.from_file(file_path)
                    mp3_path = base_path + '.mp3'
                    audio.export(mp3_path, format="mp3")
                    os.remove(file_path)
                    return mp3_path
                except Exception as e:
                    st.warning(f"오디오 변환 실패: {e}. 원본 형식 사용: {ext}")
                    return file_path
            
            # MP3이거나 변환 불가능한 경우 원본 반환
            return file_path
    
    # 파일을 찾지 못한 경우
    raise FileNotFoundError("다운로드된 오디오 파일을 찾을 수 없습니다.")

def extract_lyrics(audio_path):
    """Whisper를 사용하여 오디오에서 가사 추출"""
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    return result

def translate_text(text, target_lang):
    """텍스트를 목표 언어로 번역"""
    try:
        # 원본 언어 자동 감지
        detected_lang = GoogleTranslator().detect(text)
        if detected_lang == target_lang:
            return text, detected_lang
        
        translator = GoogleTranslator(source='auto', target=target_lang)
        translated = translator.translate(text)
        return translated, detected_lang
    except Exception as e:
        st.error(f"번역 중 오류 발생: {str(e)}")
        return text, "unknown"

def translate_line_by_line(lines, target_lang):
    """줄별로 번역하여 원본과 번역을 매칭"""
    translator = GoogleTranslator(source='auto', target=target_lang)
    translated_lines = []
    
    for line in lines:
        if line.strip():
            try:
                translated = translator.translate(line.strip())
                translated_lines.append(translated)
            except Exception as e:
                translated_lines.append(f"(번역 오류: {str(e)})")
        else:
            translated_lines.append("")
    
    return translated_lines

if extract_button and url:
    try:
        # 임시 디렉토리 생성
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, "audio")
        
        # 1. 오디오 다운로드
        progress_bar = st.progress(0)
        status_text.info("📥 YouTube에서 오디오를 다운로드하는 중...")
        progress_bar.progress(10)
        
        audio_path = download_audio(url, output_path)
        st.session_state.audio_file_path = audio_path
        
        status_text.success(f"✅ 오디오 다운로드 완료!")
        progress_bar.progress(30)
        
        # 2. 가사 추출
        status_text.info("🎤 음성 인식으로 가사를 추출하는 중... (시간이 걸릴 수 있습니다)")
        progress_bar.progress(40)
        
        transcription_result = extract_lyrics(audio_path)
        lyrics_text = transcription_result['text']
        detected_language = transcription_result['language']
        
        st.session_state.lyrics = lyrics_text
        st.session_state.original_language = detected_language
        
        status_text.success("✅ 가사 추출 완료!")
        progress_bar.progress(70)
        
        # 3. 번역
        status_text.info(f"🌐 {target_language}로 번역하는 중...")
        progress_bar.progress(80)
        
        # 줄별로 번역
        lyrics_lines = [line.strip() for line in lyrics_text.split('\n') if line.strip()]
        if not lyrics_lines:
            # 줄바꿈이 없는 경우 문장 단위로 분리
            lyrics_lines = re.split(r'[.!?]\s+', lyrics_text)
            lyrics_lines = [line.strip() for line in lyrics_lines if line.strip()]
        
        translated_lines = translate_line_by_line(lyrics_lines, target_lang_code)
        st.session_state.translated_lyrics = '\n'.join(translated_lines)
        st.session_state.lyrics = '\n'.join(lyrics_lines)  # 원본도 줄별로 정리
        
        status_text.success("✅ 번역 완료!")
        progress_bar.progress(100)
        
        time.sleep(0.5)
        progress_bar.empty()
        status_text.empty()
        
        st.success("🎉 모든 작업이 완료되었습니다!")
        
    except Exception as e:
        st.error(f"오류 발생: {str(e)}")
        progress_bar.empty()
        status_text.empty()

# 가사 표시
if st.session_state.lyrics:
    st.markdown("---")
    st.header("📝 가사")
    
    # 원본 언어 정보 표시
    if st.session_state.original_language:
        lang_names = {
            'en': '영어', 'ko': '한국어', 'ja': '일본어', 'zh': '중국어',
            'es': '스페인어', 'fr': '프랑스어', 'de': '독일어', 'it': '이탈리아어',
            'pt': '포르투갈어', 'ru': '러시아어'
        }
        detected_lang_name = lang_names.get(st.session_state.original_language, st.session_state.original_language)
        st.info(f"감지된 원본 언어: {detected_lang_name}")
    
    # 원본과 번역을 줄별로 표시
    original_lines = [line.strip() for line in st.session_state.lyrics.split('\n') if line.strip()]
    translated_lines = [line.strip() for line in st.session_state.translated_lyrics.split('\n')] if st.session_state.translated_lyrics else []
    
    # 노래방 스타일로 한 줄씩 교차 표시
    st.subheader("🎤 가사 (노래방 스타일)")
    
    # 최대 라인 수 계산
    max_lines = max(len(original_lines), len(translated_lines))
    
    for i in range(max_lines):
        # 원본 가사
        if i < len(original_lines) and original_lines[i]:
            st.markdown(f"**🌍 {original_lines[i]}**")
        
        # 번역 가사
        if i < len(translated_lines) and translated_lines[i]:
            st.markdown(f"**🌐 {translated_lines[i]}**")
        
        # 빈 줄 추가 (가독성 향상)
        if i < max_lines - 1:
            st.markdown("")

# 푸터 및 추가 정보
if not st.session_state.lyrics:
    st.markdown("---")
    st.header("ℹ️ 추가 정보")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.markdown("""
        ### ⏱️ 처리 시간
        - **짧은 동영상** (3분 이하): 약 1-2분
        - **중간 동영상** (3-5분): 약 2-4분
        - **긴 동영상** (5분 이상): 약 4-10분
        
        *처리 시간은 동영상 길이와 시스템 성능에 따라 달라질 수 있습니다.*
        """)
    
    with info_col2:
        st.markdown("""
        ### 🔧 시스템 요구사항
        - Python 3.8 이상
        - FFmpeg 설치 필요
        - 인터넷 연결 필요
        - 충분한 디스크 공간
        
        *FFmpeg가 설치되지 않은 경우 오디오 변환이 실패할 수 있습니다.*
        """)
    
    st.markdown("---")
    st.markdown("💡 **팁**: 긴 동영상의 경우 가사 추출에 시간이 걸릴 수 있습니다. 처리 중에는 페이지를 닫지 마세요!")
else:
    st.markdown("---")
    st.markdown("💡 **팁**: 다른 동영상을 처리하려면 위에서 새로운 URL을 입력하세요!")

