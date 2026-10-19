import os
import requests
from fastapi import FastAPI, Request, BackgroundTasks
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip

app = FastAPI()

# ⚠️ Вставьте сюда ваш токен от BotFather (внутри кавычек)
TELEGRAM_TOKEN = "8947491742:AAEJLwVy9ZTt_uDdQK0O2zuvEcLO83D6J4o"

def process_video_in_background(video_url: str, chat_id: str):
    input_path = f"input_{chat_id}.mp4"
    output_path = f"output_{chat_id}.mp4"
    
    try:
        # 1. Скачиваем видео, которое пользователь прислал в BotHelp
        response = requests.get(video_url, stream=True)
        if response.status_code == 200:
            with open(input_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
        
        # 2. Открываем видео и накладываем водяной знак
        video = VideoFileClip(input_path)
        
        # Загружаем вашу картинку watermark.png
        watermark = (ImageClip("watermark.png")
                     .set_duration(video.duration)
                     .resize(height=40)  # Высота логотипа в пикселях (можно менять)
                     .margin(right=15, bottom=15, opacity=0) # Отступы от краев
                     .set_pos(("right", "bottom"))) # Позиция: правый нижний угол
        
        # Соединяем слои
        final_video = CompositeVideoClip([video, watermark])
        final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")
        
        # Закрываем файлы, чтобы очистить память сервера
        video.close()
        final_video.close()
        
        # 3. Отправляем готовый результат обратно пользователю в Telegram
        url = f"https://telegram.org{TELEGRAM_TOKEN}/sendVideo"
        with open(output_path, 'rb') as f:
            requests.post(url, data={'chat_id': chat_id, 'caption': 'Ваше видео с водяным знаком!'}, files={'video': f})

    except Exception as e:
        print(f"Ошибка при обработке: {e}")
    finally:
        # Удаляем временные файлы с сервера Render
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)

# Этот адрес примет запрос от BotHelp
@app.post("/webhook")
async def handle_bothelp_webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    
    # Извлекаем ссылку на видео и ID чата, которые пришлет BotHelp
    video_url = data.get("video_url") 
    chat_id = data.get("chat_id")
    
    if video_url and chat_id:
        # Запускаем обработку в фоновом режиме, чтобы BotHelp не ждал слишком долго
        background_tasks.add_task(process_video_in_background, video_url, chat_id)
        return {"status": "processing"}
        
    return {"status": "error", "message": "Missing data"}
