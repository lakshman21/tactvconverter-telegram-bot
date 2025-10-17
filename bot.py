import os
import telebot
import subprocess
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

def convert_video(input_file):
    output_file = input_file.rsplit('.', 1)[0] + "_Converted.mpg"
    cmd = [
        "ffmpeg", "-i", input_file,
        "-c:v", "mpeg2video", "-b:v", "6000k", "-maxrate", "9000k", "-bufsize", "1835k",
        "-vf", "scale=720:576,format=yuv420p,setsar=12/11",
        "-r", "25", "-top", "1", "-flags", "+ildct+ilme", "-aspect", "4:3",
        "-c:a", "mp2", "-b:a", "192k", "-ar", "48000",
        output_file
    ]
    subprocess.run(cmd, check=True)
    return output_file

def upload_to_gdrive(file_path):
    subprocess.run(["rclone", "copy", file_path, "gdrive:/ConvertedVideos", "--drive-chunk-size", "64M", "-P"])
    link = subprocess.check_output(["rclone", "link", f"gdrive:/ConvertedVideos/{os.path.basename(file_path)}"]).decode().strip()
    return link

@bot.message_handler(content_types=['video'])
def handle_video(message):
    msg = bot.reply_to(message, "🎬 Downloading video...")
    file_info = bot.get_file(message.video.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    input_filename = message.video.file_name or "input.mp4"
    with open(input_filename, 'wb') as f:
        f.write(downloaded_file)

    bot.edit_message_text("⚙️ Converting video, please wait...", chat_id=msg.chat.id, message_id=msg.message_id)
    output_file = convert_video(input_filename)

    bot.edit_message_text("☁️ Uploading to Google Drive...", chat_id=msg.chat.id, message_id=msg.message_id)
    link = upload_to_gdrive(output_file)

    bot.edit_message_text(f"✅ Done!\nHere’s your converted file:\n{link}", chat_id=msg.chat.id, message_id=msg.message_id)

bot.polling()
