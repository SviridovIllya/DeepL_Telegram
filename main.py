import deepl
import os
from pathlib import Path
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

API_KEY = ""

TELEGRAM_TOKEN = ""

translator = deepl.Translator(API_KEY)


FORMALITY_SUPPORTED_LANGUAGES = {"DE", "FR", "IT", "ES", "NL", "PL", "PT", "RU"}

# Функція для створення глосарію
def create_glossary(source_lang="EN", target_lang="UK"):
    glossary_entries = {
        "Artificial Intelligence": "Штучний інтелект",
        "Machine Learning": "Машинне навчання",
        "DeepL": "DeepL"
    }
    glossary = translator.create_glossary(
        name="TechGlossary",
        source_lang=source_lang,
        target_lang=target_lang,
        entries=glossary_entries
    )
    return glossary.glossary_id

# Функція для перекладу тексту
async def translate_text(text, source_lang="EN", target_lang="UK", formality="formal"):
    try:
        glossary_id = create_glossary(source_lang, target_lang)
        translation_options = {
            "source_lang": source_lang,
            "target_lang": target_lang,
            "glossary": glossary_id
        }
        if target_lang in FORMALITY_SUPPORTED_LANGUAGES:
            translation_options["formality"] = formality
        result = translator.translate_text(text, **translation_options)
        translator.delete_glossary(glossary_id)
        return result.text
    except Exception as e:
        return f"Помилка: {str(e)}"

# Функція для перекладу документа
async def translate_document(input_path, output_path, source_lang="EN", target_lang="UK"):
    try:
        with open(input_path, "rb") as in_file, open(output_path, "wb") as out_file:
            translator.translate_document(
                from_file=in_file,
                to_file=out_file,
                source_lang=source_lang,
                target_lang=target_lang
            )
        return output_path
    except Exception as e:
        return f"Помилка при перекладі документа: {str(e)}"

# Команда /start для бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! Я бот для перекладу за допомогою DeepL API.\n"
                                    "Надішли мені текст або файл (.txt, .docx), і я перекладу його на українську!")

# Обробка текстових повідомлень
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    translated = await translate_text(text)
    await update.message.reply_text(translated)

# Обробка файлів
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    file_name = document.file_name
    file_extension = os.path.splitext(file_name)[1].lower()

    # Завантажуємо файл
    file = await document.get_file()
    input_path = f"temp_{file_name}"
    await file.download_to_drive(input_path)

    # Перевіряємо тип файлу
    if file_extension in [".txt"]:
        with open(input_path, "r", encoding="utf-8") as f:
            text = f.read()
        translated = await translate_text(text)
        await update.message.reply_text(translated)
    elif file_extension in [".docx", ".pdf"]:
        output_path = f"translated_{file_name}"
        result = await translate_document(input_path, output_path)
        if os.path.exists(output_path):
            with open(output_path, "rb") as f:
                await update.message.reply_document(f, filename=output_path)
        else:
            await update.message.reply_text(result)
    else:
        await update.message.reply_text("Підтримуються лише .txt, .docx або .pdf файли!")

    # Видаляємо тимчасові файли
    if os.path.exists(input_path):
        os.remove(input_path)
    if os.path.exists(output_path):
        os.remove(output_path)

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("Бот запущений!")
    application.run_polling()

if __name__ == "__main__":
    main()