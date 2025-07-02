import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import yt_dlp
import threading
import os
import sys
import subprocess
import webbrowser

class YouTubeDownloaderUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader v1.0")
        self.root.geometry("650x600")
        
        # 다운로드 상태 변수
        self.is_downloading = False
        
        self.create_widgets()
        self.check_ffmpeg_status()
        
    def check_ffmpeg_status(self):
        """FFmpeg 설치 상태 확인"""
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            self.ffmpeg_status.set("✅ FFmpeg 설치됨")
            self.ffmpeg_label.config(foreground="green")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.ffmpeg_status.set("❌ FFmpeg 미설치")
            self.ffmpeg_label.config(foreground="red")
            self.log_message("⚠️ FFmpeg가 설치되지 않았습니다. 일부 기능이 제한됩니다.")
            self.log_message("📋 FFmpeg 설치 방법은 '도움말' 버튼을 클릭하세요.")
        
    def create_widgets(self):
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 제목 및 FFmpeg 상태
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        title_label = ttk.Label(header_frame, text="YouTube Downloader", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # FFmpeg 상태 표시
        self.ffmpeg_status = tk.StringVar(value="확인 중...")
        self.ffmpeg_label = ttk.Label(header_frame, textvariable=self.ffmpeg_status, 
                                     font=('Arial', 10))
        self.ffmpeg_label.grid(row=0, column=1, sticky=tk.E)
        
        # 도움말 버튼
        help_button = ttk.Button(header_frame, text="FFmpeg 설치 도움말", 
                               command=self.show_ffmpeg_help)
        help_button.grid(row=0, column=2, padx=(10, 0))
        
        header_frame.columnconfigure(0, weight=1)
        
        # URL 입력
        ttk.Label(main_frame, text="YouTube URL:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=60)
        self.url_entry.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 출력 경로
        ttk.Label(main_frame, text="다운로드 경로:").grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        
        path_frame = ttk.Frame(main_frame)
        path_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 기본 경로를 사용자 문서 폴더로 설정
        default_path = os.path.join(os.path.expanduser("~"), "Downloads", "YouTube")
        self.path_var = tk.StringVar(value=default_path)
        self.path_entry = ttk.Entry(path_frame, textvariable=self.path_var, width=50)
        self.path_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.browse_button = ttk.Button(path_frame, text="찾아보기", command=self.browse_folder)
        self.browse_button.grid(row=0, column=1, padx=(5, 0))
        
        # 품질 설정
        quality_frame = ttk.LabelFrame(main_frame, text="품질 설정", padding="5")
        quality_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.quality_var = tk.StringVar(value="best")
        quality_options = [
            ("최고 품질 (단일 파일) - 권장", "best", False),
            ("최고 품질 (병합) - FFmpeg 필요", "bestvideo+bestaudio", True),
            ("720p HD", "best[height<=720]", False),
            ("480p", "best[height<=480]", False),
            ("음성만 (mp3) - FFmpeg 필요", "bestaudio/best", True)
        ]
        
        for i, (text, value, needs_ffmpeg) in enumerate(quality_options):
            if needs_ffmpeg:
                text += " ⚠️"
            rb = ttk.Radiobutton(quality_frame, text=text, variable=self.quality_var, 
                               value=value)
            rb.grid(row=i, column=0, sticky=tk.W, pady=2)
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=(0, 10))
        
        self.download_button = ttk.Button(button_frame, text="다운로드 시작", 
                                        command=self.start_download)
        self.download_button.grid(row=0, column=0, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="정지", 
                                    command=self.stop_download, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=(5, 0))
        
        clear_button = ttk.Button(button_frame, text="로그 지우기", 
                                command=self.clear_log)
        clear_button.grid(row=0, column=2, padx=(5, 0))
        
        # 진행률 바
        self.progress_var = tk.StringVar(value="대기 중...")
        ttk.Label(main_frame, textvariable=self.progress_var).grid(row=7, column=0, columnspan=2, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 10))
        
        # 로그 출력
        ttk.Label(main_frame, text="로그:").grid(row=9, column=0, sticky=tk.W, pady=(0, 5))
        self.log_text = scrolledtext.ScrolledText(main_frame, height=12, width=70)
        self.log_text.grid(row=10, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 그리드 가중치 설정
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(10, weight=1)
        path_frame.columnconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # 초기 메시지
        self.log_message("🚀 YouTube Downloader 준비 완료!")
        self.log_message("📝 URL을 입력하고 다운로드 버튼을 클릭하세요.")
        
    def show_ffmpeg_help(self):
        """FFmpeg 설치 도움말 창 표시"""
        help_window = tk.Toplevel(self.root)
        help_window.title("FFmpeg 설치 도움말")
        help_window.geometry("500x400")
        help_window.resizable(True, True)
        
        # 스크롤 텍스트
        help_text = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, padx=10, pady=10)
        help_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        help_content = """
FFmpeg 설치 안내

FFmpeg는 비디오와 오디오를 처리하는 프로그램입니다.
고품질 다운로드와 음성 추출을 위해 필요합니다.

🔹 Windows 설치 방법:

방법 1: 자동 설치 (권장)
1. Windows PowerShell을 관리자 권한으로 실행
2. 다음 명령어 입력:
   winget install FFmpeg

방법 2: Chocolatey 사용
1. Chocolatey가 설치되어 있다면:
   choco install ffmpeg

방법 3: 수동 설치
1. https://ffmpeg.org/download.html 방문
2. Windows 빌드 다운로드
3. 압축 해제 후 bin 폴더를 PATH에 추가

🔹 설치 확인:
명령 프롬프트에서 'ffmpeg -version' 입력

🔹 FFmpeg 없이 사용 가능한 기능:
- 최고 품질 (단일 파일) ✅
- 720p, 480p 다운로드 ✅

🔹 FFmpeg 필요한 기능:
- 최고 품질 (병합) ⚠️
- 음성만 추출 (mp3) ⚠️

설치 후 프로그램을 재시작하세요.
        """
        
        help_text.insert(tk.END, help_content)
        help_text.config(state=tk.DISABLED)
        
        # 버튼 프레임
        button_frame = ttk.Frame(help_window)
        button_frame.pack(pady=10)
        
        # 웹사이트 열기 버튼
        def open_ffmpeg_site():
            webbrowser.open("https://ffmpeg.org/download.html")
        
        ttk.Button(button_frame, text="FFmpeg 웹사이트 열기", 
                  command=open_ffmpeg_site).pack(side=tk.LEFT, padx=5)
        
        # 상태 새로고침 버튼
        ttk.Button(button_frame, text="설치 상태 새로고침", 
                  command=self.check_ffmpeg_status).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="닫기", 
                  command=help_window.destroy).pack(side=tk.LEFT, padx=5)
        
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_var.set(folder)
    
    def clear_log(self):
        """로그 텍스트 지우기"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("🧹 로그가 지워졌습니다.")
    
    def log_message(self, message):
        """로그 텍스트에 메시지 추가"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def progress_hook(self, d):
        """yt-dlp 진행률 콜백"""
        if d['status'] == 'downloading':
            if 'total_bytes' in d:
                percent = d['downloaded_bytes'] / d['total_bytes'] * 100
                speed = d.get('speed', 0)
                if speed:
                    speed_mb = speed / 1024 / 1024
                    self.progress_var.set(f"다운로드 중... {percent:.1f}% ({speed_mb:.1f} MB/s)")
                else:
                    self.progress_var.set(f"다운로드 중... {percent:.1f}%")
            else:
                self.progress_var.set("다운로드 중...")
        elif d['status'] == 'finished':
            self.progress_var.set("다운로드 완료!")
            filename = os.path.basename(d['filename'])
            self.log_message(f"✅ 완료: {filename}")
    
    def start_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("오류", "YouTube URL을 입력해주세요.")
            return
        
        # FFmpeg 필요한 옵션 체크
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
        
        if self.is_downloading:
            return
        
        # UI 상태 변경
        self.is_downloading = True
        self.download_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.progress_bar.start()
        self.progress_var.set("다운로드 준비 중...")
        
        # 별도 스레드에서 다운로드 실행
        thread = threading.Thread(target=self.download_video, args=(url,))
        thread.daemon = True
        thread.start()
    
    def stop_download(self):
        """다운로드 정지"""
        self.is_downloading = False
        self.download_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.progress_bar.stop()
        self.progress_var.set("다운로드 정지됨")
        self.log_message("🛑 사용자에 의해 다운로드가 정지되었습니다.")
    
    def download_video(self, url):
        try:
            # 출력 경로 설정
            output_path = self.path_var.get()
            if not output_path:
                output_path = os.path.join(os.path.expanduser("~"), "Downloads", "YouTube")
            
            # 디렉토리 생성
            os.makedirs(output_path, exist_ok=True)
            
            # yt-dlp 설정
            quality = self.quality_var.get()
            
            ydl_opts = {
                'format': quality,
                'outtmpl': os.path.join(output_path, '%(uploader)s - %(title)s.%(ext)s'),
                'progress_hooks': [self.progress_hook],
                'no_warnings': True,
            }
            
            # 음성만 다운로드인 경우
            if quality == "bestaudio/best":
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            # 병합이 필요한 경우
            elif quality == "bestvideo+bestaudio":
                ydl_opts['merge_output_format'] = 'mp4'
            
            self.log_message(f"📥 다운로드 시작: {url}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if not self.is_downloading:
                    return
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Unknown')
                uploader = info.get('uploader', 'Unknown')
                self.log_message(f"🎉 성공: {title} (by {uploader})")
                self.log_message(f"📁 저장 위치: {output_path}")
            
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
            # UI 상태 복원
            self.is_downloading = False
            self.download_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.progress_bar.stop()
            self.progress_var.set("대기 중...")

def main():
    # Windows에서 DPI 스케일링 문제 해결
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
        
    root = tk.Tk()
    app = YouTubeDownloaderUI(root)
    
    # 종료 시 처리
    def on_closing():
        if app.is_downloading:
            if messagebox.askokcancel("종료", "다운로드가 진행 중입니다. 정말 종료하시겠습니까?"):
                app.is_downloading = False
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()