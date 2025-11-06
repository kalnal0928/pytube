import customtkinter as ctk
from tkinter import filedialog, messagebox
import yt_dlp
from threading import Thread, Event
import os
import sys
import subprocess
import webbrowser
import time
#모듈 업데이트 pip install --upgrade yt_dlp 
# 테마 및 글꼴 설정
ctk.set_appearance_mode("System")  # "System", "Dark", "Light"
ctk.set_default_color_theme("blue") # "blue", "green", "dark-blue"

# --- 글꼴 설정 --- (여기서 쉽게 변경하세요)
# 시스템에 설치된 폰트를 사용하거나, 프로그램 폴더에 폰트 파일(.ttf)을 넣고  ㅁㅁ경로를 지정할 수 있습니다.
# 예: BASE_FONT = "c:/windows/fonts/malgun.ttf"
BASE_FONT = "Malgun Gothic" # 기본 폰트
TITLE_FONT_SIZE = 20
BODY_FONT_SIZE = 12

class YouTubeDownloaderUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("YouTube Downloader v2.1")
        self.geometry("700x650")

        # --- 글꼴 객체 생성 ---
        self.title_font = ctk.CTkFont(family=BASE_FONT, size=TITLE_FONT_SIZE, weight="bold")
        self.body_font = ctk.CTkFont(family=BASE_FONT, size=BODY_FONT_SIZE)
        self.small_font = ctk.CTkFont(family=BASE_FONT, size=BODY_FONT_SIZE - 2)

        # 다운로드 상태 및 중단 이벤트
        self.download_thread = None
        self.stop_event = Event()
        
        # 동적 URL 큐 관리
        self.download_queue = []  # 다운로드 대기 중인 URL 목록
        self.is_downloading = False  # 다운로드 진행 중 여부
        self.queue_lock = Thread().lock if hasattr(Thread(), 'lock') else None
        from threading import Lock
        self.queue_lock = Lock()

        self.create_widgets()
        self.check_ffmpeg_status()

        # yt-dlp.exe 자동 업데이트 시작
        Thread(target=self.run_yt_dlp_update, daemon=True).start()

    def check_ffmpeg_status(self):
        """FFmpeg 설치 상태 확인"""
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.ffmpeg_status.set("✅ FFmpeg 설치됨")
            self.ffmpeg_label.configure(text_color="green")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.ffmpeg_status.set("❌ FFmpeg 미설치")
            self.ffmpeg_label.configure(text_color="red")
            self.log_message("⚠️ FFmpeg가 설치되지 않았습니다. 일부 기능이 제한됩니다.")
            self.log_message("📋 FFmpeg 설치 방법은 '도움말' 버튼을 클릭하세요.")

    def _get_yt_dlp_path(self):
        """Determines the path to yt-dlp.exe based on the execution context."""
        if getattr(sys, 'frozen', False):
            # Running in a PyInstaller bundle (frozen)
            if hasattr(sys, '_MEIPASS'):
                # This is a one-file build, files are in the temp _MEIPASS dir
                base_path = sys._MEIPASS
            else:
                # This is a one-folder build, files are relative to the executable
                base_path = os.path.dirname(sys.executable)

            # Based on the build, yt-dlp.exe seems to be in an '_internal' folder
            # Let's check there first.
            internal_path = os.path.join(base_path, '_internal', 'yt-dlp.exe')
            if os.path.exists(internal_path):
                return internal_path

            # As a fallback, check the base path directly. This is the expected
            # location for one-file builds and some one-folder configurations.
            fallback_path = os.path.join(base_path, 'yt-dlp.exe')
            return fallback_path
        else:
            # Running in a normal Python environment
            # Assumes yt-dlp.exe is in the project root.
            return 'yt-dlp.exe'

    def run_yt_dlp_update(self):
        """Checks for and applies updates to yt-dlp.exe."""
        self.log_message("🔄 yt-dlp.exe 업데이트를 확인합니다...")
        yt_dlp_path = self._get_yt_dlp_path()

        if not yt_dlp_path or not os.path.exists(yt_dlp_path):
            self.log_message("ℹ️ yt-dlp.exe를 찾을 수 없어 업데이트를 건너뜁니다.")
            return

        try:
            process = subprocess.run(
                [yt_dlp_path, '-U'],
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8',
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            output = process.stdout
            if "is up to date" in output:
                self.log_message("✅ yt-dlp.exe가 이미 최신 버전입니다.")
            elif "Updated yt-dlp to" in output:
                self.log_message("✨ yt-dlp.exe가 성공적으로 업데이트되었습니다!")
                self.after(100, lambda: messagebox.showinfo("업데이트 완료", "yt-dlp.exe가 최신 버전으로 업데이트되었습니다."))
            else:
                # Log the output for inspection if it's unexpected
                self.log_message(f"[yt-dlp-update] {output.strip()}")

        except subprocess.CalledProcessError as e:
            self.log_message(f"❌ yt-dlp.exe 업데이트 중 오류 발생: {e.stderr}")
            self.after(100, lambda: messagebox.showerror("업데이트 오류", f"yt-dlp.exe 업데이트에 실패했습니다.\n{e.stderr}"))
        except Exception as e:
            self.log_message(f"❌ 예상치 못한 오류 발생: {e}")

    def check_and_update_yt_dlp(self):
        """yt-dlp 업데이트 페이지를 엽니다."""
        self.log_message("🌐 yt-dlp 업데이트 페이지를 엽니다...")
        try:
            webbrowser.open("https://github.com/yt-dlp/yt-dlp/releases/latest")
            self.log_message("✅ 브라우저에서 최신 버전을 다운로드하고 exe 파일을 교체해주세요.")
            messagebox.showinfo("업데이트 안내", "웹 브라우저에서 yt-dlp 최신 릴리스 페이지가 열립니다.\n\n1. 'yt-dlp.exe' 파일을 다운로드하세요.\n2. 현재 프로그램이 있는 폴더의 'yt-dlp.exe'를 다운로드한 새 파일로 교체하세요.")
        except Exception as e:
            self.log_message(f"❌ 오류 발생: {e}")
            messagebox.showerror("오류", f"웹 브라우저를 여는 중 오류가 발생했습니다.\n{e}")

    def create_widgets(self):
        # 그리드 설정
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        # 메인 프레임
        main_frame = ctk.CTkFrame(self, corner_radius=10)
        main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="new")
        main_frame.grid_columnconfigure(0, weight=1)

        self._create_header(main_frame)
        self._create_url_input(main_frame)
        self._create_path_selection(main_frame)
        self._create_quality_options(main_frame)

        # 컨트롤 프레임
        control_frame = ctk.CTkFrame(self, corner_radius=10)
        control_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        control_frame.grid_columnconfigure(0, weight=1)
        self._create_controls(control_frame)

        # 진행률 프레임
        progress_frame = ctk.CTkFrame(self, corner_radius=10)
        progress_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        progress_frame.grid_columnconfigure(0, weight=1)
        self._create_progress_display(progress_frame)
        
        # 로그 프레임
        log_frame = ctk.CTkFrame(self, corner_radius=10)
        log_frame.grid(row=3, rowspan=2, column=0, padx=10, pady=(0, 10), sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)
        self._create_log_output(log_frame)

        # 초기 메시지
        self.log_message("🚀 YouTube Downloader 준비 완료!")
        self.log_message("📝 최대 10개의 YouTube URL을 입력하고 다운로드 버튼을 클릭하세요.")
        self.log_message("💡 한 줄에 하나씩 URL을 입력하면 순차적으로 다운로드됩니다.")

    def _create_header(self, parent):
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        header_frame.columnconfigure(1, weight=1)

        ctk.CTkLabel(header_frame, text="YouTube Downloader", font=self.title_font).grid(row=0, column=0, sticky="w")
        
        self.ffmpeg_status = ctk.StringVar(value="확인 중...")
        self.ffmpeg_label = ctk.CTkLabel(header_frame, textvariable=self.ffmpeg_status, font=self.small_font)
        self.ffmpeg_label.grid(row=0, column=1, sticky="e", padx=(0, 10))

        button_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        button_container.grid(row=0, column=2, sticky="e")

        self.update_button = ctk.CTkButton(button_container, text="yt-dlp 업데이트", width=120, command=self.check_and_update_yt_dlp, font=self.body_font)
        self.update_button.grid(row=0, column=0, sticky="e", padx=(0, 5))

        self.help_button = ctk.CTkButton(button_container, text="FFmpeg 도움말", width=120, command=self.show_ffmpeg_help, font=self.body_font)
        self.help_button.grid(row=0, column=1, sticky="e")

    def _create_url_input(self, parent):
        url_label_frame = ctk.CTkFrame(parent, fg_color="transparent")
        url_label_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10)
        url_label_frame.columnconfigure(1, weight=1)
        
        ctk.CTkLabel(url_label_frame, text="📋 YouTube URL 입력 (최대 10개):", font=self.body_font).grid(row=0, column=0, sticky="w")
        self.url_count_label = ctk.CTkLabel(url_label_frame, text="0/10", font=self.small_font, text_color="gray")
        self.url_count_label.grid(row=0, column=1, sticky="e")
        
        # URL 입력 안내 프레임
        info_frame = ctk.CTkFrame(parent, fg_color="transparent")
        info_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(5, 0))
        
        ctk.CTkLabel(info_frame, text="💡 한 줄에 하나씩 URL을 입력하세요", 
                    font=self.small_font, text_color="gray").grid(row=0, column=0, sticky="w")
        
        # URL 입력 텍스트박스 (테두리와 배경색 개선)
        self.url_textbox = ctk.CTkTextbox(
            parent, 
            height=120, 
            corner_radius=8, 
            font=self.body_font,
            border_width=2,
            border_color=("gray70", "gray30"),
            fg_color=("gray95", "gray10"),
            text_color=("black", "white")
        )
        self.url_textbox.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(5, 10))
        
        # 플레이스홀더 텍스트 설정
        self.placeholder_text = "여기에 YouTube URL을 입력하세요...\n\n예시:\nhttps://www.youtube.com/watch?v=dQw4w9WgXcQ\nhttps://youtu.be/dQw4w9WgXcQ\nhttps://www.youtube.com/playlist?list=PLxxxxxx"
        self.url_textbox.insert("1.0", self.placeholder_text)
        self.url_textbox.configure(text_color="gray")
        
        # 이벤트 바인딩
        self.url_textbox.bind("<FocusIn>", self._on_url_focus_in)
        self.url_textbox.bind("<FocusOut>", self._on_url_focus_out)
        self.url_textbox.bind("<KeyRelease>", self._update_url_count)
        self.url_textbox.bind("<Enter>", self._on_url_hover_in)
        self.url_textbox.bind("<Leave>", self._on_url_hover_out)
        
        # 붙여넣기 이벤트 - 우선순위 높게 바인딩
        self.url_textbox.bind("<<Paste>>", self._on_paste)
        self.url_textbox.bind("<Control-v>", self._on_paste)
        self.url_textbox.bind("<Control-V>", self._on_paste)
        self.url_textbox.bind("<Shift-Insert>", self._on_paste)  # Shift+Insert도 추가
        
        # 키 입력 감지 (Enter 키로 줄바꿈 시에도 처리)
        self.url_textbox.bind("<Return>", self._on_enter_key)
        self.url_textbox.bind("<Key>", self._on_key_press)
        
        # 텍스트 변경 감지를 위한 추가 모니터링
        self._last_text_content = ""
        self._monitor_text_changes()

    def _create_path_selection(self, parent):
        ctk.CTkLabel(parent, text="다운로드 경로:", font=self.body_font).grid(row=3, column=0, sticky="w", padx=10)
        path_frame = ctk.CTkFrame(parent, fg_color="transparent")
        path_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 15))
        path_frame.columnconfigure(0, weight=1)

        default_path = os.path.join(os.path.expanduser("~"), "Downloads", "YouTube")
        self.path_var = ctk.StringVar(value=default_path)
        self.path_entry = ctk.CTkEntry(path_frame, textvariable=self.path_var, font=self.body_font)
        self.path_entry.grid(row=0, column=0, sticky="ew")

        self.browse_button = ctk.CTkButton(path_frame, text="찾아보기", width=100, command=self.browse_folder, font=self.body_font)
        self.browse_button.grid(row=0, column=1, padx=(10, 0))

    def _create_quality_options(self, parent):
        quality_frame = ctk.CTkFrame(parent)
        quality_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        quality_frame.columnconfigure(0, weight=1)
        
        ctk.CTkLabel(quality_frame, text="품질 설정", font=ctk.CTkFont(family=BASE_FONT, size=BODY_FONT_SIZE, weight="bold")).grid(row=0, column=0, sticky="w", padx=10, pady=(5,5))

        self.quality_var = ctk.StringVar(value="best")
        quality_options = [
            ("최고 품질 (단일 파일) - 권장", "best[ext=mp4]/best", False),
            ("최고 품질 (병합) - FFmpeg 필요", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", True),
            ("720p HD", "best[height<=720]", False),
            ("480p", "best[height<=480]", False),
            ("음성만 (mp3) - FFmpeg 필요", "bestaudio/best", True)
        ]

        for i, (text, value, needs_ffmpeg) in enumerate(quality_options):
            if needs_ffmpeg:
                text += " ⚠️"
            rb = ctk.CTkRadioButton(quality_frame, text=text, variable=self.quality_var, value=value, font=self.body_font)
            rb.grid(row=i + 1, column=0, sticky="w", padx=15, pady=3)

    def _create_controls(self, parent):
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        button_frame.columnconfigure((0,1,2), weight=1)

        self.download_button = ctk.CTkButton(button_frame, text="다운로드 시작", command=self.start_download, font=self.body_font)
        self.download_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.stop_button = ctk.CTkButton(button_frame, text="정지", command=self.stop_download, state="disabled", fg_color="#D32F2F", hover_color="#B71C1C", font=self.body_font)
        self.stop_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.clear_button = ctk.CTkButton(button_frame, text="로그 지우기", command=self.clear_log, fg_color="gray", hover_color="#616161", font=self.body_font)
        self.clear_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

    def _create_progress_display(self, parent):
        # 전체 진행률
        self.overall_progress_var = ctk.StringVar(value="대기 중...")
        ctk.CTkLabel(parent, textvariable=self.overall_progress_var, font=self.body_font).grid(row=0, column=0, sticky="w", padx=10, pady=(5,0))

        self.overall_progress_bar = ctk.CTkProgressBar(parent, mode='determinate')
        self.overall_progress_bar.set(0)
        self.overall_progress_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 5))

        # 개별 다운로드 진행률
        self.current_progress_var = ctk.StringVar(value="")
        self.current_progress_label = ctk.CTkLabel(parent, textvariable=self.current_progress_var, font=self.small_font, text_color="gray")
        self.current_progress_label.grid(row=2, column=0, sticky="w", padx=10, pady=(0,0))

        self.current_progress_bar = ctk.CTkProgressBar(parent, mode='indeterminate')
        self.current_progress_bar.set(0)
        self.current_progress_bar.grid(row=3, column=0, sticky="ew", padx=10, pady=(5, 10))

    def _create_log_output(self, parent):
        ctk.CTkLabel(parent, text="로그:", font=ctk.CTkFont(family=BASE_FONT, size=BODY_FONT_SIZE, weight="bold")).grid(row=0, column=0, sticky="w", padx=10, pady=(5,5))
        self.log_text = ctk.CTkTextbox(parent, corner_radius=8, font=self.body_font)
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.log_text.configure(state="disabled")

    def _set_ui_state(self, is_downloading):
        """UI 컨트롤의 상태를 설정합니다."""
        if is_downloading:
            self.download_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.current_progress_bar.configure(mode='indeterminate')
            self.current_progress_bar.start()
            self.overall_progress_var.set("다운로드 준비 중...")
        else:
            self.is_downloading = False
            self.download_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.current_progress_bar.stop()
            self.current_progress_bar.configure(mode='determinate')
            self.current_progress_bar.set(0)
            self.overall_progress_bar.set(0)
            self.overall_progress_var.set("대기 중...")
            self.current_progress_var.set("")

    def show_ffmpeg_help(self):
        """FFmpeg 설치 도움말 창 표시"""
        help_window = ctk.CTkToplevel(self)
        help_window.title("FFmpeg 설치 도움말")
        help_window.geometry("550x450")
        help_window.transient(self)
        help_window.grab_set()
        help_window.grid_columnconfigure(0, weight=1)
        help_window.grid_rowconfigure(0, weight=1)

        help_text_box = ctk.CTkTextbox(help_window, wrap="word", corner_radius=8, font=self.body_font)
        help_text_box.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        help_content = """FFmpeg 설치 안내

FFmpeg는 비디오와 오디오를 처리하는 강력한 오픈소스 프로그램입니다.
고품질 영상/음성 병합이나 음성 추출(mp3 변환)을 위해 필요합니다.

🔹 Windows 설치 방법:

방법 1: winget (Windows 10/11 내장)
1. Windows PowerShell 또는 명령 프롬프트를 관리자 권한으로 실행
2. 다음 명령어 입력 후 실행:
   winget install FFmpeg

방법 2: Chocolatey (패키지 관리자)
1. Chocolatey가 설치되어 있다면 다음 명령어 실행:
   choco install ffmpeg

방법 3: 수동 설치
1. https://ffmpeg.org/download.html 방문
2. Windows 아이콘 클릭 후, gyan.dev 빌드 다운로드
3. 압축 해제 후 bin 폴더를 시스템 환경 변수 'Path'에 추가

🔹 설치 확인:
명령 프롬프트에서 'ffmpeg -version' 입력 시 버전 정보가 표시되면 성공입니다.

🔹 FFmpeg 없이 사용 가능한 기능:
- 최고 품질 (단일 파일) ✅
- 720p, 480p 다운로드 ✅

🔹 FFmpeg 필요한 기능:
- 최고 품질 (병합) ⚠️
- 음성만 추출 (mp3) ⚠️

설치 후에는 프로그램을 재시작해야 적용됩니다.
"""
        help_text_box.insert("1.0", help_content)
        help_text_box.configure(state="disabled")

        button_frame = ctk.CTkFrame(help_window, fg_color="transparent")
        button_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        button_frame.columnconfigure((0,1,2), weight=1)

        def open_ffmpeg_site():
            webbrowser.open("https://ffmpeg.org/download.html")

        ctk.CTkButton(button_frame, text="FFmpeg 웹사이트", command=open_ffmpeg_site, font=self.body_font).grid(row=0, column=0, padx=5, sticky="ew")
        ctk.CTkButton(button_frame, text="설치 상태 새로고침", command=self.check_ffmpeg_status, font=self.body_font).grid(row=0, column=1, padx=5, sticky="ew")
        ctk.CTkButton(button_frame, text="닫기", command=help_window.destroy, font=self.body_font).grid(row=0, column=2, padx=5, sticky="ew")

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_var.set(folder)

    def clear_log(self):
        """로그 텍스트 지우기"""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_message("🧹 로그가 지워졌습니다.")
        self.log_text.configure(state="disabled")

    def _on_url_focus_in(self, event=None):
        """URL 텍스트박스에 포커스가 들어왔을 때"""
        current_text = self.url_textbox.get("1.0", "end-1c")
        if current_text == self.placeholder_text:
            self.url_textbox.delete("1.0", "end")
            self.url_textbox.configure(text_color=("black", "white"))

    def _on_url_focus_out(self, event=None):
        """URL 텍스트박스에서 포커스가 나갔을 때"""
        current_text = self.url_textbox.get("1.0", "end-1c").strip()
        if not current_text:
            self.url_textbox.insert("1.0", self.placeholder_text)
            self.url_textbox.configure(text_color="gray")

    def _on_url_hover_in(self, event=None):
        """URL 텍스트박스에 마우스가 올라왔을 때"""
        self.url_textbox.configure(border_color=("blue", "lightblue"))

    def _on_url_hover_out(self, event=None):
        """URL 텍스트박스에서 마우스가 나갔을 때"""
        self.url_textbox.configure(border_color=("gray70", "gray30"))

    def _on_paste(self, event=None):
        """붙여넣기 이벤트 처리"""
        # 기본 붙여넣기 동작을 먼저 차단
        try:
            # 클립보드에서 텍스트 가져오기
            clipboard_text = self.clipboard_get().strip()
            
            if not clipboard_text:
                return "break"
            
            # 현재 텍스트가 플레이스홀더인지 확인
            current_text = self.url_textbox.get("1.0", "end-1c")
            if current_text == self.placeholder_text:
                self.url_textbox.delete("1.0", "end")
                self.url_textbox.configure(text_color=("black", "white"))
            
            # 현재 커서 위치 저장
            cursor_pos = self.url_textbox.index("insert")
            
            # YouTube URL인지 확인
            if self._is_valid_youtube_url(clipboard_text):
                # 현재 줄의 내용 확인
                line_num = cursor_pos.split('.')[0]
                current_line = self.url_textbox.get(f"{line_num}.0", f"{line_num}.end")
                
                # 현재 줄에 내용이 있으면 새 줄로 이동
                if current_line.strip():
                    self.url_textbox.insert(cursor_pos, "\n")
                    cursor_pos = self.url_textbox.index("insert")
                
                # URL과 줄바꿈을 한 번에 삽입
                self.url_textbox.insert(cursor_pos, clipboard_text + "\n")
                
                # 포커스 유지
                self.url_textbox.focus_set()
                self.url_textbox.see("insert")
                
                # 다운로드 중이면 큐에 추가
                if self.is_downloading:
                    self._add_to_download_queue(clipboard_text)
                
                # 번호 업데이트
                self.after(10, self._update_url_numbers)
                self.after(20, self._update_url_count)
                
                return "break"  # 기본 붙여넣기 동작 방지
            
            # 여러 줄의 텍스트인 경우 각 줄을 확인
            lines = clipboard_text.split('\n')
            valid_urls = [line.strip() for line in lines if line.strip() and self._is_valid_youtube_url(line.strip())]
            
            if valid_urls:
                # 현재 줄에 내용이 있으면 새 줄로 이동
                line_num = cursor_pos.split('.')[0]
                current_line = self.url_textbox.get(f"{line_num}.0", f"{line_num}.end")
                if current_line.strip():
                    self.url_textbox.insert(cursor_pos, "\n")
                
                # 각 URL을 별도 줄에 삽입 (한 번에 처리)
                urls_text = ""
                for i, url in enumerate(valid_urls):
                    if i > 0:
                        urls_text += "\n"
                    urls_text += url
                    
                    # 다운로드 중이면 큐에 추가
                    if self.is_downloading:
                        self._add_to_download_queue(url)
                
                # 모든 URL과 마지막 줄바꿈을 한 번에 삽입
                self.url_textbox.insert("insert", urls_text + "\n")
                
                # 포커스 유지
                self.url_textbox.focus_set()
                self.url_textbox.see("insert")
                
                # 번호 업데이트
                self.after(10, self._update_url_numbers)
                self.after(20, self._update_url_count)
                
                return "break"  # 기본 붙여넣기 동작 방지
            
            # 유효한 URL이 없으면 일반 텍스트로 처리 (기본 동작 허용)
            return None
                
        except Exception as e:
            # 오류 발생 시 기본 붙여넣기 허용
            return None

    def _on_right_click(self, event=None):
        """우클릭 메뉴 처리"""
        # 기본 우클릭 메뉴 허용
        return None

    def _on_enter_key(self, event=None):
        """Enter 키 처리"""
        # 기본 줄바꿈 허용하고 번호 업데이트
        self.after(10, self._update_url_numbers)
        self.after(20, self._update_url_count)
        return None

    def _on_key_press(self, event=None):
        """일반 키 입력 처리"""
        # 플레이스홀더 텍스트 제거
        if event and hasattr(event, 'char') and event.char.isprintable():
            current_text = self.url_textbox.get("1.0", "end-1c")
            if current_text == self.placeholder_text:
                self.url_textbox.delete("1.0", "end")
                self.url_textbox.configure(text_color=("black", "white"))
        return None

    def _monitor_text_changes(self):
        """텍스트 변경사항을 모니터링하여 붙여넣기 감지"""
        try:
            current_text = self.url_textbox.get("1.0", "end-1c")
            
            # 텍스트가 변경되었는지 확인
            if current_text != self._last_text_content:
                text_diff = len(current_text) - len(self._last_text_content)
                
                # 한 번에 많은 텍스트가 추가되었다면 붙여넣기로 간주
                if text_diff > 15:  # 임계값을 낮춤
                    # 새로 추가된 부분에서 URL 찾기
                    new_content = current_text[len(self._last_text_content):]
                    self._process_pasted_content(new_content)
                
                # 번호 업데이트 (모든 변경에 대해)
                self.after(50, self._update_url_numbers)
                
                self._last_text_content = current_text
            
        except Exception as e:
            pass
        
        # 50ms마다 체크 (더 빠르게)
        self.after(50, self._monitor_text_changes)

    def _process_pasted_content(self, content):
        """붙여넣어진 내용 처리"""
        try:
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line and self._is_valid_youtube_url(line):
                    # 다운로드 중이면 큐에 추가
                    if self.is_downloading:
                        self._add_to_download_queue(line)
            
            # 번호 업데이트
            self.after(10, self._update_url_numbers)
            self.after(20, self._update_url_count)
            
        except Exception as e:
            pass

    def _handle_url_paste_direct(self, url_text):
        """URL 붙여넣기를 직접 처리하는 메서드"""
        try:
            # 현재 커서 위치 가져오기
            cursor_pos = self.url_textbox.index("insert")
            line_num = cursor_pos.split('.')[0]
            
            # 현재 줄의 내용 확인
            current_line = self.url_textbox.get(f"{line_num}.0", f"{line_num}.end")
            
            # 현재 줄에 내용이 있으면 새 줄 추가
            if current_line.strip():
                self.url_textbox.insert("insert", "\n")
            
            # URL 삽입
            self.url_textbox.insert("insert", url_text.strip())
            
            # 줄바꿈 추가하고 커서를 다음 줄로 이동
            self.url_textbox.insert("insert", "\n")
            
            # 다운로드 중이면 큐에 추가
            if self.is_downloading:
                self._add_to_download_queue(url_text.strip())
            
            # 번호 업데이트
            self.after(10, self._update_url_numbers)
            self.after(20, self._update_url_count)
            
            return True
            
        except Exception as e:
            return False

    def _move_cursor_to_next_line(self):
        """커서를 다음 줄 시작 부분으로 이동"""
        try:
            # 현재 커서 위치 가져오기
            current_pos = self.url_textbox.index("insert")
            
            # 현재 줄 번호 추출
            line_num = int(current_pos.split('.')[0])
            
            # 다음 줄의 시작 부분으로 커서 이동 (줄 번호 + 1)
            next_line_pos = f"{line_num + 1}.0"
            
            # 해당 줄이 존재하는지 확인
            try:
                self.url_textbox.index(next_line_pos)
                self.url_textbox.mark_set("insert", next_line_pos)
            except:
                # 다음 줄이 없으면 현재 줄 끝으로 이동
                self.url_textbox.mark_set("insert", f"{line_num}.end")
            
            # 커서가 보이도록 스크롤
            self.url_textbox.see("insert")
            
            # 포커스 설정
            self.url_textbox.focus_set()
            
        except Exception as e:
            pass

    def _update_url_numbers(self):
        """URL 앞에 번호 추가"""
        try:
            current_text = self.url_textbox.get("1.0", "end-1c")
            if current_text == self.placeholder_text or not current_text.strip():
                return
            
            lines = current_text.split('\n')
            numbered_lines = []
            url_count = 0
            
            for line in lines:
                line = line.strip()
                if line and self._is_valid_youtube_url(line):
                    url_count += 1
                    # 기존 번호 제거 (정규식으로)
                    import re
                    clean_line = re.sub(r'^\d+\.\s*', '', line)
                    numbered_lines.append(f"{url_count}. {clean_line}")
                elif line:  # 빈 줄이 아닌 경우
                    numbered_lines.append(line)
            
            # 텍스트 업데이트
            new_text = '\n'.join(numbered_lines)
            if new_text != current_text:
                cursor_pos = self.url_textbox.index("insert")
                self.url_textbox.delete("1.0", "end")
                self.url_textbox.insert("1.0", new_text)
                try:
                    self.url_textbox.mark_set("insert", cursor_pos)
                except:
                    pass
                    
        except Exception as e:
            pass

    def _remove_completed_url(self, completed_url):
        """완료된 URL을 제거하고 나머지 URL들의 번호를 재정렬"""
        try:
            current_text = self.url_textbox.get("1.0", "end-1c")
            if current_text == self.placeholder_text:
                return
            
            lines = current_text.split('\n')
            new_lines = []
            
            for line in lines:
                line = line.strip()
                if line:
                    # 번호 제거하고 URL만 추출
                    import re
                    clean_line = re.sub(r'^\d+\.\s*', '', line)
                    # 완료된 URL이 아닌 경우만 유지
                    if clean_line != completed_url:
                        new_lines.append(clean_line)
            
            # 텍스트박스 업데이트
            if new_lines:
                self.url_textbox.delete("1.0", "end")
                self.url_textbox.insert("1.0", '\n'.join(new_lines))
                self.url_textbox.configure(text_color=("black", "white"))
                # 번호 재정렬
                self._update_url_numbers()
            else:
                # 모든 URL이 완료된 경우 플레이스홀더 표시
                self.url_textbox.delete("1.0", "end")
                self.url_textbox.insert("1.0", self.placeholder_text)
                self.url_textbox.configure(text_color="gray")
            
            self._update_url_count()
            
        except Exception as e:
            self.log_message(f"URL 제거 중 오류: {e}")

    def _add_to_download_queue(self, url):
        """다운로드 큐에 URL 추가"""
        try:
            with self.queue_lock:
                if url not in self.download_queue:
                    self.download_queue.append(url)
                    self.log_message(f"📝 다운로드 큐에 추가됨: {url}")
                    self.log_message(f"📋 현재 대기 중인 URL: {len(self.download_queue)}개")
        except Exception as e:
            self.log_message(f"큐 추가 중 오류: {e}")

    def _get_next_url_from_queue(self):
        """큐에서 다음 URL 가져오기"""
        try:
            with self.queue_lock:
                if self.download_queue:
                    return self.download_queue.pop(0)
                return None
        except Exception as e:
            self.log_message(f"큐에서 URL 가져오기 오류: {e}")
            return None

    def _update_queue_from_textbox(self):
        """텍스트박스의 URL들을 큐에 동기화"""
        try:
            current_urls = self._parse_urls()
            with self.queue_lock:
                # 기존 큐 초기화하고 현재 URL들로 재구성
                self.download_queue = [url for url in current_urls if url not in self.download_queue]
        except Exception as e:
            self.log_message(f"큐 동기화 중 오류: {e}")

    def _update_url_count(self, event=None):
        """URL 개수 업데이트"""
        # 키 입력 후 번호 업데이트 (딜레이를 두어 타이핑 중 과도한 업데이트 방지)
        if event and hasattr(event, 'keysym'):
            self.after(500, self._update_url_numbers)
            # 다운로드 중이면 큐도 업데이트
            if self.is_downloading:
                self.after(1000, self._update_queue_from_textbox)
        
        urls = self._parse_urls()
        count = len(urls)
        color = "red" if count > 10 else "gray" if count == 0 else "green"
        self.url_count_label.configure(text=f"{count}/10", text_color=color)

    def _parse_urls(self):
        """텍스트박스에서 URL들을 파싱하여 유효한 YouTube URL만 반환"""
        content = self.url_textbox.get("1.0", "end").strip()
        if not content or content == self.placeholder_text or content.startswith("여기에 YouTube URL을"):
            return []
        
        lines = content.split('\n')
        urls = []
        
        for line in lines:
            line = line.strip()
            if line:
                # 번호 제거하고 URL만 추출
                import re
                clean_line = re.sub(r'^\d+\.\s*', '', line)
                if self._is_valid_youtube_url(clean_line):
                    urls.append(clean_line)
        
        return urls

    def _is_valid_youtube_url(self, url):
        """YouTube URL 유효성 검사"""
        youtube_patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
            r'https?://(?:www\.)?youtu\.be/[\w-]+',
            r'https?://(?:www\.)?youtube\.com/playlist\?list=[\w-]+',
            r'https?://(?:www\.)?youtube\.com/shorts/[\w-]+',
            r'https?://(?:m\.)?youtube\.com/watch\?v=[\w-]+',
        ]
        
        import re
        for pattern in youtube_patterns:
            if re.match(pattern, url):
                return True
        return False

    def download_multiple_videos(self, urls):
        """여러 비디오를 순차적으로 다운로드"""
        total_count = len(urls)
        successful_downloads = 0
        failed_downloads = 0

        self.log_message(f"📋 총 {total_count}개의 URL을 다운로드합니다.")
        
        for i, url in enumerate(urls, 1):
            if self.stop_event.is_set():
                self.log_message("🛑 사용자에 의해 다운로드가 중단되었습니다.")
                break
                
            # 전체 진행률 업데이트
            overall_progress = (i - 1) / total_count
            self.overall_progress_bar.set(overall_progress)
            self.overall_progress_var.set(f"전체 진행률: {i-1}/{total_count} 완료")
            
            self.log_message(f"\n📥 [{i}/{total_count}] 다운로드 시작: {url}")
            self.current_progress_var.set(f"현재: [{i}/{total_count}] 다운로드 중...")
            
            # 개별 비디오 다운로드
            success = self.download_single_video(url)
            
            if success:
                successful_downloads += 1
                self.log_message(f"✅ [{i}/{total_count}] 다운로드 성공!")
                # 성공한 URL을 텍스트박스에서 제거
                self.after(100, lambda u=url: self._remove_completed_url(u))
            else:
                failed_downloads += 1
                self.log_message(f"❌ [{i}/{total_count}] 다운로드 실패!")
                
            # 전체 진행률 업데이트
            overall_progress = i / total_count
            self.overall_progress_bar.set(overall_progress)
            self.overall_progress_var.set(f"전체 진행률: {i}/{total_count} 완료")
            
            if self.stop_event.is_set():
                break
        
        # 최종 결과 표시
        if not self.stop_event.is_set():
            self.overall_progress_bar.set(1.0)
            self.overall_progress_var.set("모든 다운로드 완료!")
            self.current_progress_var.set("")
            self.current_progress_bar.set(0)
            
            self.log_message(f"\n🎉 다운로드 완료!")
            self.log_message(f"✅ 성공: {successful_downloads}개")
            if failed_downloads > 0:
                self.log_message(f"❌ 실패: {failed_downloads}개")
            
            output_path = self.path_var.get()
            self.log_message(f"📁 저장 위치: {output_path}")
            
            # 완료 메시지박스
            if failed_downloads == 0:
                messagebox.showinfo("다운로드 완료", f"모든 비디오 다운로드가 완료되었습니다!\n성공: {successful_downloads}개")
            else:
                messagebox.showwarning("다운로드 완료", f"다운로드가 완료되었습니다.\n성공: {successful_downloads}개\n실패: {failed_downloads}개")
        
        self.after(100, self._set_ui_state, False)

    def download_with_dynamic_queue(self):
        """동적 큐를 사용한 다운로드 시스템"""
        successful_downloads = 0
        failed_downloads = 0
        total_processed = 0

        self.log_message(f"📋 다운로드 시작 - 동적 큐 시스템 활성화")
        self.log_message(f"💡 다운로드 중에도 새로운 URL을 추가할 수 있습니다!")
        
        while True:
            if self.stop_event.is_set():
                self.log_message("🛑 사용자에 의해 다운로드가 중단되었습니다.")
                break
            
            # 큐에서 다음 URL 가져오기
            current_url = self._get_next_url_from_queue()
            
            if current_url is None:
                # 큐가 비어있으면 잠시 대기 후 다시 확인
                self.update_idletasks()
                time.sleep(0.5)
                
                # 텍스트박스에서 새로운 URL 확인
                self._update_queue_from_textbox()
                current_url = self._get_next_url_from_queue()
                
                if current_url is None:
                    # 더 이상 다운로드할 URL이 없으면 종료
                    break
            
            total_processed += 1
            
            # 현재 큐 상태 표시
            with self.queue_lock:
                remaining_count = len(self.download_queue)
            
            self.log_message(f"\n📥 [{total_processed}] 다운로드 시작: {current_url}")
            self.log_message(f"📋 대기 중인 URL: {remaining_count}개")
            
            self.current_progress_var.set(f"현재: [{total_processed}] 다운로드 중... (대기: {remaining_count}개)")
            self.overall_progress_var.set(f"총 {total_processed}개 처리 중 (성공: {successful_downloads}, 실패: {failed_downloads})")
            
            # 개별 비디오 다운로드
            success = self.download_single_video(current_url)
            
            if success:
                successful_downloads += 1
                self.log_message(f"✅ [{total_processed}] 다운로드 성공!")
                # 성공한 URL을 텍스트박스에서 제거
                self.after(100, lambda u=current_url: self._remove_completed_url(u))
            else:
                failed_downloads += 1
                self.log_message(f"❌ [{total_processed}] 다운로드 실패!")
            
            # 진행률 업데이트
            self.overall_progress_var.set(f"총 {total_processed}개 처리됨 (성공: {successful_downloads}, 실패: {failed_downloads})")
            
            if self.stop_event.is_set():
                break
        
        # 최종 결과 표시
        if not self.stop_event.is_set():
            self.overall_progress_var.set("모든 다운로드 완료!")
            self.current_progress_var.set("")
            self.current_progress_bar.set(0)
            
            self.log_message(f"\n🎉 다운로드 완료!")
            self.log_message(f"✅ 성공: {successful_downloads}개")
            if failed_downloads > 0:
                self.log_message(f"❌ 실패: {failed_downloads}개")
            
            output_path = self.path_var.get()
            self.log_message(f"📁 저장 위치: {output_path}")
            
            # 완료 메시지박스
            if failed_downloads == 0:
                messagebox.showinfo("다운로드 완료", f"모든 비디오 다운로드가 완료되었습니다!\n성공: {successful_downloads}개")
            else:
                messagebox.showwarning("다운로드 완료", f"다운로드가 완료되었습니다.\n성공: {successful_downloads}개\n실패: {failed_downloads}개")
        
        self.after(100, self._set_ui_state, False)

    def log_message(self, message):
        """로그 텍스트에 메시지 추가"""
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.update_idletasks()

    def start_download(self):
        urls = self._parse_urls()
        if not urls:
            messagebox.showerror("오류", "유효한 YouTube URL을 입력해주세요.")
            return

        if len(urls) > 10:
            messagebox.showerror("오류", f"최대 10개의 URL만 입력할 수 있습니다. (현재: {len(urls)}개)")
            return

        quality = self.quality_var.get()
        # FFmpeg check is still relevant for the UI warning, but the logic is now handled by yt-dlp.exe
        ffmpeg_needed = "bestvideo" in quality or "bestaudio" in quality

        if ffmpeg_needed and "❌" in self.ffmpeg_status.get():
            # We can still warn the user, as yt-dlp.exe will fail if ffmpeg is not in PATH
            if not messagebox.askyesno("FFmpeg 필요",
                "선택한 품질 옵션은 FFmpeg가 필요합니다.\n"
                "FFmpeg가 설치되어 있지 않으면 오류가 발생합니다. 계속하시겠습니까?"):
                return

        if self.download_thread and self.download_thread.is_alive():
            return

        # 다운로드 큐 초기화
        with self.queue_lock:
            self.download_queue = urls.copy()
        
        self._set_ui_state(is_downloading=True)
        self.is_downloading = True
        self.stop_event.clear()

        self.download_thread = Thread(target=self.download_with_dynamic_queue, daemon=True)
        self.download_thread.start()

    def stop_download(self):
        """다운로드 정지"""
        if self.download_thread and self.download_thread.is_alive():
            self.stop_event.set()
            self.progress_var.set("다운로드 정지 중...")
            self.log_message("⚠️ 다운로드 정지를 요청했습니다...")

    def download_single_video(self, url):
        """단일 비디오 다운로드 (성공/실패 반환)"""
        try:
            output_path = self.path_var.get()
            if not output_path:
                output_path = os.path.join(os.path.expanduser("~"), "Downloads", "YouTube")
            
            os.makedirs(output_path, exist_ok=True)
            
            quality = self.quality_var.get()

            # Determine path to yt-dlp.exe
            yt_dlp_path = self._get_yt_dlp_path()

            if not yt_dlp_path or not os.path.exists(yt_dlp_path):
                self.log_message(f"❌ yt-dlp.exe를 찾을 수 없습니다! (경로: {yt_dlp_path})")
                messagebox.showerror("오류", "yt-dlp.exe를 찾을 수 없습니다. 프로그램 폴더에 파일이 있는지 확인하세요.")
                self.after(100, self._set_ui_state, False)
                return

            # Build the command
            command = [
                yt_dlp_path,
                '--progress',
                '--progress-template', '%(progress.percentage)s;%(progress.speed)s;%(progress.eta)s',
                '-o', os.path.join(output_path, '%(uploader)s - %(title)s.%(ext)s'),
                '--no-warnings',
                '--encoding', 'utf-8', # Ensure output is utf-8
                '--no-check-certificate', # SSL 인증서 검증 비활성화
            ]

            # Format selection
            if quality == "bestaudio/best":
                command.extend(['-x', '--audio-format', 'mp3', '--audio-quality', '192'])
            else:
                command.extend(['-f', quality])
            
            command.append(url)
            
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace', # Avoid encoding errors
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            # Threads to read stdout and stderr to prevent deadlocks
            stdout_thread = Thread(target=self._read_progress_output, args=(process.stdout,), daemon=True)
            stderr_thread = Thread(target=self._read_stderr_output, args=(process.stderr,), daemon=True)
            stdout_thread.start()
            stderr_thread.start()

            # Wait for the process to finish
            while process.poll() is None:
                if self.stop_event.is_set():
                    process.terminate() # Send SIGTERM
                    self.log_message("⏳ 프로세스를 종료하는 중...")
                    break
                self.update_idletasks() # Keep UI responsive
                time.sleep(0.1)

            stdout_thread.join(timeout=1)
            stderr_thread.join(timeout=1)
            
            return_code = process.returncode

            if self.stop_event.is_set():
                return False

            if return_code == 0:
                # The final '100%' might not be caught by the progress reader, so set it manually
                self.current_progress_bar.set(1)
                return True
            else:
                self.log_message(f"❌ 다운로드 오류 발생 (종료 코드: {return_code})")
                return False

        except Exception as e:
            self.log_message(f"❌ 치명적인 오류 발생: {e}")
            import traceback
            self.log_message(traceback.format_exc())
            return False

    def _read_progress_output(self, stream):
        for line in iter(stream.readline, ''):
            if self.stop_event.is_set():
                break
            
            line = line.strip()
            if not line:
                continue

            if '%' in line:
                try:
                    # My custom template: '%(progress.percentage)s;%(progress.speed)s;%(progress.eta)s'
                    parts = line.split(';')
                    if len(parts) >= 1:
                        percentage_str = parts[0].replace('%','').strip()
                        percent_float = float(percentage_str) / 100
                        
                        speed_str = f"속도: {parts[1]}" if len(parts) > 1 and parts[1] else ''
                        eta_str = f"남은 시간: {parts[2]}" if len(parts) > 2 and parts[2] else ''

                        self.current_progress_bar.configure(mode='determinate')
                        self.current_progress_bar.set(percent_float)
                        self.current_progress_var.set(f"다운로드 중... {percentage_str}% {speed_str} {eta_str}")
                except (ValueError, IndexError):
                    # Not a progress line I can parse, treat as a log message
                    self.log_message(f"[yt-dlp] {line}")
            else:
                # Regular log message from yt-dlp
                self.log_message(f"[yt-dlp] {line}")
        stream.close()

    def _read_stderr_output(self, stream):
        for line in iter(stream.readline, ''):
            if self.stop_event.is_set():
                break
            self.log_message(f"[오류] {line.strip()}")
        stream.close()

def main():
    # Windows에서 DPI 스케일링 문제 해결 (ctypes는 customtkinter에서 관리)
    app = YouTubeDownloaderUI()

    def on_closing():
        if app.download_thread and app.download_thread.is_alive():
            if messagebox.askokcancel("종료", "다운로드가 진행 중입니다. 정말 종료하시겠습니까?"):
                app.stop_event.set()
                app.destroy()
        else:
            app.destroy()

    app.protocol("WM_DELETE_WINDOW", on_closing)
    app.mainloop()

if __name__ == "__main__":
    main()
