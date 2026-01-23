from dataclasses import dataclass
import logging
from pathlib import Path
import time
import uuid

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.asr.whisper_asr import transcribe
from app.bot import messages
from app.llm.task_extractor import extract_tasks
from app.schemas.task import Task, TaskRecord
from app.services.tasks import create_tasks

router = Router()

AUDIO_DIR = Path("data/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

PENDING_TTL_SECONDS = 15 * 60
_pending: dict[str, "PendingVoice"] = {}
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PendingVoice:
    user_id: int
    text: str
    created_at: float
    ogg_path: Path


def _cleanup_pending() -> None:
    now = time.time()
    expired = [
        request_id
        for request_id, pending in _pending.items()
        if now - pending.created_at > PENDING_TTL_SECONDS
    ]
    for request_id in expired:
        _pending.pop(request_id, None)


def _format_tasks(items: list[Task]) -> str:
    lines = []
    for i, task in enumerate(items, 1):
        date_str = task.due_date.isoformat() if task.due_date else "no date"
        lines.append(f"{i}. {task.title} - {date_str}")
    return "\n".join(lines)


def _format_records(records: list[TaskRecord]) -> str:
    return _format_tasks([record.task for record in records])


@router.message(F.voice)
async def handle_voice(message: Message):
    file = await message.bot.get_file(message.voice.file_id)

    filename = f"{uuid.uuid4()}.ogg"
    ogg_path = AUDIO_DIR / filename

    await message.bot.download_file(file.file_path, destination=ogg_path)
    await message.answer(messages.VOICE_PROCESSING)

    try:
        text = transcribe(ogg_path)
    except Exception:
        logger.exception("Voice transcribe failed")
        await message.answer(messages.VOICE_TRANSCRIBE_ERROR)
        return

    if not text:
        await message.answer(messages.NO_TASKS_FOUND)
        return

    tasks = extract_tasks(text)
    if not tasks:
        await message.answer(messages.NO_TASKS_FOUND)
        return

    _cleanup_pending()
    request_id = uuid.uuid4().hex
    _pending[request_id] = PendingVoice(
        user_id=message.from_user.id,
        text=text,
        created_at=time.time(),
        ogg_path=ogg_path,
    )

    preview = "\n".join(
        [
            messages.VOICE_PREVIEW_HEADER,
            text,
            "",
            messages.VOICE_TASKS_HEADER,
            _format_tasks(tasks),
        ]
    )

    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text=messages.VOICE_CONFIRM_BUTTON,
            callback_data=f"confirm:{request_id}",
        )
    )
    builder.add(
        InlineKeyboardButton(
            text=messages.VOICE_CANCEL_BUTTON,
            callback_data=f"cancel:{request_id}",
        )
    )
    builder.adjust(2)

    await message.answer(preview, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("confirm:"))
async def confirm_voice(callback: CallbackQuery):
    request_id = callback.data.split(":", maxsplit=1)[1]
    _cleanup_pending()
    pending = _pending.get(request_id)
    if not pending:
        await callback.answer(messages.VOICE_EXPIRED, show_alert=True)
        return

    if pending.user_id != callback.from_user.id:
        await callback.answer(messages.VOICE_NOT_ALLOWED, show_alert=True)
        return

    _pending.pop(request_id, None)
    records = create_tasks(pending.user_id, pending.text)
    if not records:
        await callback.message.edit_text(messages.NO_TASKS_FOUND)
        await callback.answer()
        return

    reply = messages.TASKS_ADDED
    details = _format_records(records)
    if details:
        reply = f"{reply}\n{details}"

    await callback.message.edit_text(reply)
    await callback.answer()


@router.callback_query(F.data.startswith("cancel:"))
async def cancel_voice(callback: CallbackQuery):
    request_id = callback.data.split(":", maxsplit=1)[1]
    _cleanup_pending()
    pending = _pending.get(request_id)
    if not pending:
        await callback.answer(messages.VOICE_EXPIRED, show_alert=True)
        return

    if pending.user_id != callback.from_user.id:
        await callback.answer(messages.VOICE_NOT_ALLOWED, show_alert=True)
        return

    _pending.pop(request_id, None)
    await callback.message.edit_text(messages.VOICE_CANCELLED)
    await callback.answer()
