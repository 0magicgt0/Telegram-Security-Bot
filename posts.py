"""
handlers/posts.py

Система постов через Telegram Mini App.
- /newpost -> кнопка открыть редактор (Mini App)
- Принимает данные из WebApp и публикует пост
"""
import json
import logging
from aiogram import Router, Bot, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command

router = Router()
log = logging.getLogger(__name__)

# Укажи HTTPS-ссылку на задеплоенный post_editor.html.
# Примеры:
# WEBAPP_URL = "https://username.github.io/repo/post_editor.html"
# WEBAPP_URL = "https://my-miniapp.netlify.app/post_editor.html"
WEBAPP_URL = "https://0magicgt0.github.io/Telegram-Security-Bot/"

# ID канала для публикации. Оставь None, если пока нужна только подготовка Mini App.
CHANNEL_ID = None

# Username чата для кнопки "Открыть чат". Пример: "mychat"
CHAT_USERNAME = ""


def build_editor_keyboard() -> InlineKeyboardMarkup | None:
    if not WEBAPP_URL:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="✍️ Открыть редактор",
                web_app=WebAppInfo(url=WEBAPP_URL),
            )
        ]]
    )


@router.message(Command("newpost"))
async def cmd_newpost(message: Message):
    """Открывает редактор постов через Mini App."""
    keyboard = build_editor_keyboard()
    if keyboard is None:
        return await message.reply(
            "🛠 <b>Mini App ещё не настроен</b>\n\n"
            "Что сделать:\n"
            "1. Залить файл <code>post_editor.html</code> на HTTPS-хостинг\n"
            "2. В <code>handlers/posts.py</code> указать <code>WEBAPP_URL</code>\n"
            "3. Перезапустить бота\n\n"
            "Пример ссылки:\n"
            "<code>https://username.github.io/repo/post_editor.html</code>",
            parse_mode="HTML",
        )

    await message.reply(
        "📝 <b>Редактор постов</b>\n\n"
        "Нажми кнопку ниже, чтобы открыть редактор.\n"
        "В нём можно добавить заголовок, текст и выбрать параметры публикации.\n\n"
        "⚠️ <i>Убедись, что в GitHub Pages опубликован файл index.html, а бот добавлен в канал как администратор.</i>",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@router.message(F.web_app_data)
async def handle_webapp_data(message: Message, bot: Bot):
    try:
        data = json.loads(message.web_app_data.data)
    except Exception:
        return await message.reply("❌ Ошибка при чтении данных из редактора.")

    title = data.get("title", "").strip()
    comment = data.get("comment", "").strip()
    template = data.get("template", "").strip()
    open_chat = data.get("open_chat", False)
    pin = data.get("pin", False)
    silent = data.get("silent", False)

    parts = []
    if title:
        parts.append(f"<b>{title}</b>")
    if comment:
        parts.append(comment)
    if template:
        parts.append(template)

    post_text = "\n\n".join(parts).strip()
    if not post_text:
        return await message.reply("❌ Пост пустой.")

    keyboard = None
    if open_chat and CHAT_USERNAME:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text="💬 Открыть чат", url=f"https://t.me/{CHAT_USERNAME}")
            ]]
        )

    if CHANNEL_ID is None:
        return await message.reply(
            "✅ <b>Данные из Mini App получены</b>\n\n"
            f"📌 Закрепить: {'да' if pin else 'нет'}\n"
            f"🔕 Тихо: {'да' if silent else 'нет'}\n"
            f"💬 Кнопка чата: {'да' if open_chat else 'нет'}\n\n"
            "Публикация пока отключена, потому что не задан <code>CHANNEL_ID</code> в <code>handlers/posts.py</code>.",
            parse_mode="HTML",
        )

    try:
        sent = await bot.send_message(
            CHANNEL_ID,
            post_text,
            parse_mode="HTML",
            reply_markup=keyboard,
            disable_notification=silent,
        )
        if pin:
            await bot.pin_chat_message(CHANNEL_ID, sent.message_id, disable_notification=True)
        await message.reply("✅ Пост опубликован!", parse_mode="HTML")
    except Exception as e:
        await message.reply(f"❌ Ошибка публикации: {e}")

    log.info(
        "POST by %s (%d): title=%r, comment=%d chars, template=%d chars, open_chat=%s, pin=%s, silent=%s",
        getattr(message.from_user, "username", None),
        message.from_user.id,
        title,
        len(comment),
        len(template),
        open_chat,
        pin,
        silent,
    )


@router.message(Command("posts"))
async def cmd_posts_help(message: Message):
    await message.reply(
        "📢 <b>Система постов</b>\n\n"
        "✍️ /newpost - открыть редактор постов\n\n"
        "<b>Что нужно для запуска Mini App:</b>\n"
        "• залить <code>post_editor.html</code> на HTTPS-хостинг\n"
        "• указать <code>WEBAPP_URL</code> в <code>handlers/posts.py</code>\n"
        "• для публикации указать <code>CHANNEL_ID</code>\n"
        "• для кнопки чата указать <code>CHAT_USERNAME</code>\n\n"
        "<i>В архиве уже есть файл DEPLOY_MINIAPP.md с готовыми шагами для GitHub Pages.</i>",
        parse_mode="HTML",
    )
