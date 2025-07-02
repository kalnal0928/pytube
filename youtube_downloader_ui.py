import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import yt_dlp
import threading
import os
import sys

class YouTubeDownloaderUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("600x500")
        
        # 다운로드 상태 변수
        self.is_downloading = False
        
        self.create_widgets()
        
    def create_widgets(self):
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # URL 입력
        ttk.Label(main_frame, text="YouTube URL:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=60)
        self.url_entry.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 출력 경로
        ttk.Label(main_frame, text="다운로드 경로:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        path_frame = ttk.Frame(main_frame)
        path_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.path_var = tk.StringVar(value="downloads")
        self.path_entry = ttk.Entry(path_frame, textvariable=self.path_var, width=50)
        self.path_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.browse_button = ttk.Button(path_frame, text="찾아보기", command=self.browse_folder)
        self.browse_button.grid(row=0, column=1, padx=(5, 0))
        
        # 품질 설정
        quality_frame = ttk.LabelFrame(main_frame, text="품질 설정", padding="5")
        quality_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.quality_var = tk.StringVar(value="best")
        quality_options = [
            ("최고 품질 (단일 파일)", "best"),
            ("최고 품질 (병합 필요 - ffmpeg 필요)", "bestvideo+bestaudio"),
            ("720p", "best[height<=720]"),
            ("480p", "best[height<=480]"),
            ("음성만 (mp3)", "bestaudio/best")
        ]
        
        for i, (text, value) in enumerate(quality_options):
            ttk.Radiobutton(quality_frame, text=text, variable=self.quality_var, 
                           value=value).grid(row=i, column=0, sticky=tk.W, pady=2)
        
        # 다운로드 버튼
        self.download_button = ttk.Button(main_frame, text="다운로드 시작", 
                                        command=self.start_download)
        self.download_button.grid(row=5, column=0, pady=(0, 10))
        
        # 정지 버튼
        self.stop_button = ttk.Button(main_frame, text="정지", 
                                    command=self.stop_download, state="disabled")
        self.stop_button.grid(row=5, column=1, pady=(0, 10), padx=(5, 0))
        
        # 진행률 바
        self.progress_var = tk.StringVar(value="대기 중...")
        ttk.Label(main_frame, textvariable=self.progress_var).grid(row=6, column=0, columnspan=2, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 10))
        
        # 로그 출력
        ttk.Label(main_frame, text="로그:").grid(row=8, column=0, sticky=tk.W, pady=(0, 5))
        self.log_text = scrolledtext.ScrolledText(main_frame, height=10, width=70)
        self.log_text.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 그리드 가중치 설정
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(9, weight=1)
        path_frame.columnconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_var.set(folder)
    
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
                self.progress_var.set(f"다운로드 중... {percent:.1f}%")
            else:
                self.progress_var.set("다운로드 중...")
        elif d['status'] == 'finished':
            self.progress_var.set("다운로드 완료!")
            self.log_message(f"완료: {d['filename']}")
    
    def start_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("오류", "YouTube URL을 입력해주세요.")
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
        """다운로드 정지 (현재 구현에서는 완료 후에만 정지됨)"""
        self.is_downloading = False
        self.download_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.progress_bar.stop()
        self.progress_var.set("다운로드 정지됨")
    
    def download_video(self, url):
        try:
            # 출력 경로 설정
            output_path = self.path_var.get()
            if not output_path:
                output_path = "downloads"
            
            # 디렉토리 생성
            os.makedirs(output_path, exist_ok=True)
            
            # yt-dlp 설정
            quality = self.quality_var.get()
            
            ydl_opts = {
                'format': quality,
                'outtmpl': os.path.join(output_path, '%(uploader)s - %(title)s.%(ext)s'),
                'progress_hooks': [self.progress_hook],
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
            
            self.log_message(f"다운로드 시작: {url}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Unknown')
                self.log_message(f"성공적으로 다운로드됨: {title}")
            
        except Exception as e:
            self.log_message(f"오류 발생: {str(e)}")
            messagebox.showerror("다운로드 오류", f"다운로드 중 오류가 발생했습니다:\n{str(e)}")
        
        finally:
            # UI 상태 복원
            self.is_downloading = False
            self.download_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.progress_bar.stop()
            if not hasattr(self, '_download_completed'):
                self.progress_var.set("완료")

def main():
    root = tk.Tk()
    app = YouTubeDownloaderUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()