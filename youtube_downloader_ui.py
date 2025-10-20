import customtkinter as ctk
from tkinter import filedialog, messagebox
import yt_dlp
from threading import Thread, Event
import os
import sys
import subprocess
import webbrowser
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

        self.create_widgets()
        self.check_ffmpeg_status()

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
        self.log_message("📝 URL을 입력하고 다운로드 버튼을 클릭하세요.")

    def _create_header(self, parent):
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        header_frame.columnconfigure(1, weight=1)

        ctk.CTkLabel(header_frame, text="YouTube Downloader", font=self.title_font).grid(row=0, column=0, sticky="w")
        
        self.ffmpeg_status = ctk.StringVar(value="확인 중...")
        self.ffmpeg_label = ctk.CTkLabel(header_frame, textvariable=self.ffmpeg_status, font=self.small_font)
        self.ffmpeg_label.grid(row=0, column=1, sticky="e", padx=(0, 10))

        self.help_button = ctk.CTkButton(header_frame, text="FFmpeg 도움말", width=120, command=self.show_ffmpeg_help, font=self.body_font)
        self.help_button.grid(row=0, column=2, sticky="e")

    def _create_url_input(self, parent):
        ctk.CTkLabel(parent, text="YouTube URL:", font=self.body_font).grid(row=1, column=0, sticky="w", padx=10)
        self.url_var = ctk.StringVar()
        self.url_entry = ctk.CTkEntry(parent, textvariable=self.url_var, placeholder_text="https://www.youtube.com/watch?v=...", font=self.body_font)
        self.url_entry.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))

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
        self.progress_var = ctk.StringVar(value="대기 중...")
        ctk.CTkLabel(parent, textvariable=self.progress_var, font=self.body_font).grid(row=0, column=0, sticky="w", padx=10, pady=(5,0))

        self.progress_bar = ctk.CTkProgressBar(parent, mode='indeterminate')
        self.progress_bar.set(0)
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 10))

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
            self.progress_bar.configure(mode='indeterminate')
            self.progress_bar.start()
            self.progress_var.set("다운로드 준비 중...")
        else:
            self.download_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.progress_bar.stop()
            self.progress_bar.configure(mode='determinate')
            self.progress_bar.set(0)
            self.progress_var.set("대기 중...")

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

    def log_message(self, message):
        """로그 텍스트에 메시지 추가"""
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.update_idletasks()

    def progress_hook(self, d):
        """yt-dlp 진행률 콜백"""
        if self.stop_event.is_set():
            raise yt_dlp.utils.DownloadError("사용자에 의해 다운로드가 취소되었습니다.")

        if d['status'] == 'downloading':
            self.progress_bar.configure(mode='determinate')
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            if total_bytes:
                percent = d['downloaded_bytes'] / total_bytes
                self.progress_bar.set(percent)
                
                speed = d.get('speed')
                if speed:
                    speed_mb = speed / 1024 / 1024
                    self.progress_var.set(f"다운로드 중... {percent*100:.1f}% ({speed_mb:.1f} MB/s)")
                else:
                    self.progress_var.set(f"다운로드 중... {percent*100:.1f}%")
            else:
                self.progress_bar.configure(mode='indeterminate')
                self.progress_var.set(f"다운로드 중... ({d.get('_percent_str', 'N/A')})")
        elif d['status'] == 'finished':
            self.progress_bar.set(1)
            self.progress_var.set("다운로드 완료!")
            filename = os.path.basename(d['filename'])
            self.log_message(f"✅ 완료: {filename}")

    def start_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("오류", "YouTube URL을 입력해주세요.")
            return

        quality = self.quality_var.get()
        ffmpeg_needed = quality in ["bestvideo+bestaudio", "bestaudio/best"]

        if ffmpeg_needed and "❌" in self.ffmpeg_status.get():
            result = messagebox.askyesno("FFmpeg 필요",
                "선택한 품질 옵션은 FFmpeg가 필요합니다.\n"
                "FFmpeg 없이 '최고 품질 (단일 파일)' 옵션으로 변경하시겠습니까?")
            if result:
                self.quality_var.set("best")
                self.log_message("🔄 품질 옵션이 '최고 품질 (단일 파일)'로 변경되었습니다.")
            else:
                return

        if self.download_thread and self.download_thread.is_alive():
            return

        self._set_ui_state(is_downloading=True)
        self.stop_event.clear()

        self.download_thread = Thread(target=self.download_video, args=(url,), daemon=True)
        self.download_thread.start()

    def stop_download(self):
        """다운로드 정지"""
        if self.download_thread and self.download_thread.is_alive():
            self.stop_event.set()
            self.progress_var.set("다운로드 정지 중...")
            self.log_message("⚠️ 다운로드 정지를 요청했습니다...")

    def download_video(self, url):
        try:
            output_path = self.path_var.get()
            if not output_path:
                output_path = os.path.join(os.path.expanduser("~"), "Downloads", "YouTube")
            
            os.makedirs(output_path, exist_ok=True)
            
            quality = self.quality_var.get()
            
            ydl_opts = {
                'format': quality,
                'outtmpl': os.path.join(output_path, '%(uploader)s - %(title)s.%(ext)s'),
                'progress_hooks': [self.progress_hook],
                'no_warnings': True,
                'noprogress': True, # Disable default progress bar
            }

            if quality == "bestaudio/best":
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            elif quality == "bestvideo+bestaudio":
                ydl_opts['merge_output_format'] = 'mp4'

            self.log_message(f"📥 다운로드 시작: {url}")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Unknown')
                uploader = info.get('uploader', 'Unknown')
                self.log_message(f"🎉 성공: {title} (by {uploader})")
                self.log_message(f"📁 저장 위치: {output_path}")

        except yt_dlp.utils.DownloadError as e:
            if "사용자에 의해" in str(e):
                self.log_message("🛑 다운로드가 정지되었습니다.")
            else:
                self.log_message(f"❌ 다운로드 오류: {e}")
                messagebox.showerror("다운로드 오류", f"다운로드 중 오류가 발생했습니다:\n{e}")
        except Exception as e:
            error_msg = str(e)
            self.log_message(f"❌ 오류 발생: {error_msg}")
            
            if "ffmpeg" in error_msg.lower():
                messagebox.showerror("FFmpeg 오류",
                    "FFmpeg가 필요한 기능입니다.\n\n"
                    "해결 방법:\n"
                    "1. FFmpeg를 설치하거나\n"
                    "2. '최고 품질 (단일 파일)' 옵션을 사용하세요.\n\n"
                    "'FFmpeg 설치 도움말' 버튼을 클릭하여 설치 방법을 확인하세요.")
            else:
                messagebox.showerror("다운로드 오류", f"다운로드 중 오류가 발생했습니다:\n{error_msg}")
        
        finally:
            self.after(100, self._set_ui_state, False)

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
