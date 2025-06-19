import yt_dlp

channel_url = "https://www.youtube.com/watch?v=7rgsRE3JNWo" 
output_path = "downloads/%(uploader)s/%(title)s.%(ext)s"

extractor = yt_dlp.YoutubeDL({
    'format': 'bestvideo+bestaudio/best',  # 최고 품질로 자동 병합
    'outtmpl': output_path,
    'merge_output_format': 'mp4'  # 병합 후 mp4로 저장
})
info = extractor.extract_info(channel_url, download=True)

