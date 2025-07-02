from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes
)
from gramchekly import check_follow_status
import os
TOKEN = os.environ.get("7216432249:AAEkJM0ULK7rMZfurD3i9xSazRIfx2uI6EA")
import csv

file_dict = {}
latest_results = []  # disimpan global untuk fitur /cari

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Selamat datang di Gramchekly Bot!\n\n"
        "Perintah yang tersedia:\n"
        "📂 /kirimfile - Panduan kirim file\n"
        "📥 /caradownload - Panduan download data Instagram\n"
        "🔍 /cari <username> - Cari status follow-back spesifik\n\n"
        "Setelah itu kirim:\n• followers_1.json\n• following.json",
        parse_mode="Markdown"
    )

async def kirimfile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📂 Kirim File yang Dibutuhkan:\n"
        "- followers_1.json\n- following.json\n"
        "Kamu bisa dapatkan file ini dari Instagram (lihat /caradownload)",
        parse_mode="Markdown"
    )

async def caradownload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📥 Cara Download Data Instagram:\n"
        "1. Instagram App > Profil > Settings\n"
        "2. Pilih Your Activity > Download your Information\n"
        "3. Pilih format JSON, kirim via email\n"
        "4. Ekstrak file ZIP, cari:\n• followers_1.json\n• following.json",
        parse_mode="Markdown"
    )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global latest_results
    document = update.message.document
    file_name = document.file_name
    os.makedirs("downloads", exist_ok=True)
    file_path = os.path.join("downloads", file_name)

    await document.get_file().download_to_drive(file_path)
    await update.message.reply_text(f"✅ File {file_name} diterima.", parse_mode="Markdown")

    file_dict[file_name] = file_path

    if "followers_1.json" in file_dict and "following.json" in file_dict:
        await update.message.reply_text("🔍 Memproses data...")

        try:
            results = check_follow_status(file_dict["followers_1.json"], file_dict["following.json"])

            if results is None:
                await update.message.reply_text("⚠ File tidak valid.")
                return

            latest_results = results  # simpan hasil global

            followers_back = [u for u in results if u["is_following_back"]]
            unfollowers = [u for u in results if not u["is_following_back"]]

            # Ringkasan
            summary = (
                f"👤 Total following: {len(results)}\n"
                f"✅ Follow balik: {len(followers_back)}\n"
                f"❌ Tidak follow balik: {len(unfollowers)}"
            )
            await update.message.reply_text(summary)

            # Simpan CSV
            csv_path = "downloads/follow_status.csv"
            with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=["username", "status", "followed_since"])
                writer.writeheader()
                for row in results:
                    writer.writerow({
                        "username": row["username"],
                        "status": "Follow Back" if row["is_following_back"] else "Not Follow Back",
                        "followed_since": row["followed_since"]
                    })

            await update.message.reply_document(InputFile(csv_path), filename="follow_status.csv")

        except Exception as e:
            await update.message.reply_text(f"❌ Error saat proses:\n{e}")

async def cari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global latest_results
    if not latest_results:
        await update.message.reply_text("❗ Belum ada data. Kirim file terlebih dahulu.")
        return

    if not context.args:
        await update.message.reply_text("Contoh: /cari username123")
        return

    search_username = context.args[0].lower()
    found = next((u for u in latest_results if u["username"].lower() == search_username), None)

    if found:
        status = "✅ Follow Back" if found["is_following_back"] else "❌ Not Follow Back"
        await update.message.reply_text(
            f"🔍 Hasil pencarian:\n\n"
            f"👤 Username: {found['username']}\n"
            f"📌 Status: {status}\n"
            f"⏱ Followed sejak: {found['followed_since']}"
        )
    else:
        await update.message.reply_text(f"Username {search_username} tidak ditemukan.", parse_mode="Markdown")

if _name_ == "_main_":
    import asyncio
    TOKEN = "7216432249:AAEkJM0ULK7rMZfurD3i9xSazRIfx2uI6EA"

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("kirimfile", kirimfile))
    app.add_handler(CommandHandler("caradownload", caradownload))
    app.add_handler(CommandHandler("cari", cari))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    print("Bot berjalan...")
    asyncio.run(app.run_polling())