import os
import requests
from fastapi import FastAPI, Request, BackgroundTasks

# Автоматическая настройка видео-движка прямо внутри кода
import imageio_ffmpeg
os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()

app = FastAPI()

# ⚠️ Вставьте сюда ваш токен от BotFather внутри кавычек!
TELEGRAM_TOKEN = "8947491742:AAEJLwVy9ZTt_uDdQK0O2zuvEcLO83D6J4o"

def process_video_in_background(video_url: str, chat_id: str):
    input_path = f"input_{chat_id}.mp4"
    output_path = f"output_{chat_id}.mp4"
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    try:
        # Скачиваем видео от пользователя из BotHelp
        response = requests.get(video_url, stream=True)
        if response.status_code == 200:
            with open(input_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
        
        # Накладываем водяной знак watermark.png в правый нижний угол ролика
        cmd = f'"{ffmpeg_exe}" -y -i {input_path} -i watermark.png -filter_complex "overlay=main_w-overlay_w-15:main_h-overlay_h-15" -codec:a copy {output_path}'
        os.system(cmd)
        
        # Отправляем готовое видео обратно пользователю в Telegram
        url = f"https://telegram.org{TELEGRAM_TOKEN}/sendVideo"
        with open(output_path, 'rb') as f:
            requests.post(url, data={'chat_id': chat_id, 'caption': 'Ваше видео с водяным знаком!'}, files={'video': f})

    except Exception as e:
        print(f"Ошибка при обработке видео: {e}")
    finally:
        # Очищаем память сервера от временных файлов
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)

@app.post("/webhook")
async def handle_bothelp_webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    video_url = data.get("video_url") 
    chat_id = data.get("chat_id")
    
    if video_url and chat_id:
        background_tasks.add_task(process_video_in_background, video_url, chat_id)
        return {"status": "processing"}
        
    return {"status": "error", "message": "Missing data"}
