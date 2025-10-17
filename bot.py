import os
import subprocess
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

BOT_TOKEN = os.getenv("8458485625:AAE7d2CDx4mi_RzpyhNmMdY0vT7IfJCkKLY")
WORKDIR = "/app/workdir"
REMOTE_NAME = "gdrive"
UPLOAD_FOLDER = "FFmpegConverted"

os.makedirs(WORKDIR, exist_ok=True)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("🎬 Send me a video file. I'll convert it for TACTV STB and upload to Google Drive.")

def handle_video(update: Update, context: CallbackContext):
    msg = update.message
    file_obj = msg.video or msg.document
    if not file_obj:
        msg.reply_text("❌ Please send a video file.")
        return

    file_id = file_obj.file_id
    in_name = os.path.join(WORKDIR, f"in_{file_id}.mkv")
    out_name = os.path.join(WORKDIR, f"out_{file_id}.mpg")

    msg.reply_text("⬇️ Downloading file...")
    file_obj.get_file().download(custom_path=in_name)

    msg.reply_text("⚙️ Converting to MPEG2 format (TACTV spec)...")
    ff_cmd = [
        "ffmpeg", "-y", "-i", in_name,
        "-c:v", "mpeg2video", "-b:v", "6000k", "-maxrate", "9000k", "-bufsize", "1835k",
        "-vf", "scale=720:576,format=yuv420p,setsar=12/11",
        "-r", "25", "-top", "1", "-flags", "+ildct+ilme", "-aspect", "4:3",
        "-c:a", "mp2", "-b:a", "192k", "-ar", "48000",
        out_name
    ]
    proc = subprocess.run(ff_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        msg.reply_text("❌ FFmpeg failed:\n" + proc.stderr[-500:])
        return

    msg.reply_text("✅ Conversion done! Uploading to Google Drive...")

    subprocess.run(["rclone", "mkdir", f"{REMOTE_NAME}:{UPLOAD_FOLDER}"])
    upload_path = f"{REMOTE_NAME}:{UPLOAD_FOLDER}/{os.path.basename(out_name)}"
    subprocess.run(["rclone", "copyto", out_name, upload_path, "--progress"])
    share_link = subprocess.check_output(["rclone", "link", upload_path], text=True).strip()

    msg.reply_text(f"📤 Uploaded Successfully!\n🔗 {share_link}")

    os.remove(in_name)
    os.remove(out_name)

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.video | Filters.document, handle_video))
    updater.start_polling()
    updater.idle()

if name == "main":
    main()
