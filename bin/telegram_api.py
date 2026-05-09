#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "telegramify-markdown",
# ]
# ///

"""Telegram API wrapper for sending messages and media."""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

MAX_MESSAGE_LEN = 4096
CANCEL_KEYBOARD = '{"inline_keyboard":[[{"text":"Cancel","callback_data":"cancel"}]]}'


def eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def resolve_root_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def require_env(name: str) -> str:
    value = os.environ.get(name, "")
    if value:
        return value
    eprint(f"{name} is required in .env")
    sys.exit(1)


BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', "")


def clean_markdown(text: str) -> str:
    """Convert standard markdown to Telegram MarkdownV2."""
    try:
        from telegramify_markdown import markdownify
        return markdownify(text, normalize_whitespace=False)
    except Exception as exc:
        eprint(f"WARN: telegramify-markdown failed, fallback to raw text: {exc}")
        return text


def curl(args: list[str]) -> str:
    """Run curl with args, return stdout."""
    cmd = ["curl", "-fsS", *args]
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def send_text(
    text: str, parse_mode: str = "", *, chat_id: str = CHAT_ID, **opts
) -> str | None:
    """Send or edit text message. Returns message_id if return_id=True."""
    endpoint = "editMessageText" if opts.get("edit") else "sendMessage"
    if len(text) > MAX_MESSAGE_LEN:
        eprint(f"WARN: text truncated {len(text)} -> {MAX_MESSAGE_LEN}")
        text = text[:MAX_MESSAGE_LEN]
    eprint(f"sending text to {chat_id}: {text[:50]} ...")
    args = [
        f"{API_BASE}/{endpoint}",
        "-d", f"chat_id={chat_id}",
        "-d", "disable_web_page_preview=true",
        "--data-urlencode",
        f"text={text}",
    ]
    if parse_mode:
        args.extend(["-d", f"parse_mode={parse_mode}"])
    if opts.get("edit"):
        args.extend(["-d", f"message_id={opts['edit']}"])
    if opts.get("cancel_btn"):
        args.extend(["--data-urlencode", f"reply_markup={CANCEL_KEYBOARD}"])

    result = curl(args)

    if opts.get("return_id"):
        try:
            return str(json.loads(result)["result"]["message_id"])
        except (json.JSONDecodeError, KeyError):
            sys.exit(1)
    return None


def send_markdown(
    markdown: str, *, chat_id: str = CHAT_ID, **opts
) -> str | None:
    """Send markdown text."""
    markdown = clean_markdown(markdown)
    return send_text(markdown, parse_mode="MarkdownV2", chat_id=chat_id, **opts)


def send_media(
    path: str,
    method: str = "sendDocument",
    field: str = "document",
    caption: str = "",
    chat_id: str = CHAT_ID,
) -> None:
    """Send media file (photo, video, voice, document)."""
    if not Path(path).is_file():
        eprint(f"{field} file not found: {path}")
        sys.exit(1)
    args = [
        f"{API_BASE}/{method}",
        "-F", f"chat_id={chat_id}",
        "-F", f"{field}=@{path}",
    ]
    if caption:
        args.extend(["-F", f"caption={caption}"])
    return curl(args)


def send_document(path: str, caption: str = "", chat_id: str = CHAT_ID) -> None:
    """Send document file."""
    return send_media(
        path,
        method="sendDocument",
        field="document",
        caption=caption,
        chat_id=chat_id,
    )


def send_photo(path: str, caption: str = "", chat_id: str = CHAT_ID) -> None:
    """Send photo file."""
    return send_media(
        path,
        method="sendPhoto",
        field="photo",
        caption=caption,
        chat_id=chat_id,
    )


def send_audio(path: str, caption: str = "", chat_id: str = CHAT_ID) -> None:
    """Send audio file."""
    return send_media(
        path,
        method="sendAudio",
        field="audio",
        caption=caption,
        chat_id=chat_id,
    )


def send_video(path: str, caption: str = "", chat_id: str = CHAT_ID) -> None:
    """Send video file."""
    return send_media(
        path,
        method="sendVideo",
        field="video",
        caption=caption,
        chat_id=chat_id,
    )


def ensure_ogg_voice(path: str) -> tuple[str, bool]:
    """Return an OGG voice path and whether it was converted."""
    src = Path(path)
    assert src.is_file(), f"voice file not found: {path}"
    if src.suffix.lower() == ".ogg":
        return str(src), False

    fd, out_path = tempfile.mkstemp(prefix="telegram_voice_", suffix=".ogg")
    os.close(fd)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(src),
        "-c:a", "libopus",
        "-b:a", "48k",
        out_path,
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        Path(out_path).unlink(missing_ok=True)
        details = (exc.stderr or "").strip()
        eprint(f"ffmpeg conversion failed: {details or exc}")
        sys.exit(1)

    return out_path, True


def send_voice(path: str, caption: str = "", chat_id: str = CHAT_ID) -> None:
    """Send voice file."""
    ogg_path, _ = ensure_ogg_voice(path)
    return send_media(
        ogg_path,
        method="sendVoice",
        field="voice",
        caption=caption,
        chat_id=chat_id,
    )


def get_text_or_read_file(input: str | Path) -> str:
    if not input:
        return ""
    if isinstance(input, Path):
        return input.read_text()
    input = str(input)
    if input.startswith('@'):  # curl style
        return Path(input[1:]).read_text()
    return input


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Telegram API wrapper",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--chat_id",
        default=os.environ.get("TELEGRAM_CHAT_ID"),
        help="Receiver Chat ID, defaults to $TELEGRAM_CHAT_ID)",
    )
    group = parser.add_mutually_exclusive_group(required=True)

    # text
    group.add_argument("-t", "--text", help="Send plain text, starts with @ for file path")
    group.add_argument("-m", "--markdown", help="Send markdown text, starts with @ for file path")

    # media
    group.add_argument("-o", "--voice", help="Send voice file")
    group.add_argument("-p", "--photo", help="Send photo file")
    group.add_argument("-d", "--document", help="Send document file")
    group.add_argument("-a", "--audio", help="Send audio file")
    group.add_argument("-v", "--video", help="Send video file")
    parser.add_argument("--caption", default="", help="Caption for media")

    # action
    group.add_argument("-T", "--typing", action="store_true", help="Send typing action")
    group.add_argument("-R", "--remove-keyboard", metavar="MSG_ID", help="Remove inline keyboard")
    group.add_argument("-A", "--answer-callback", metavar="CB_ID", help="Answer callback query")

    # modifier
    parser.add_argument("-E", "--edit", metavar="MSG_ID", help="Edit a existing message")
    parser.add_argument("-I", "--return-id", action="store_true", help="Print sent message ID")
    parser.add_argument("-B", "--with-cancel-btn", action="store_true", help="Attach Cancel button")
    args = parser.parse_args()

    chat_id = args.chat_id
    if not chat_id:
        eprint("chat_id is required (set TELEGRAM_CHAT_ID or use --chat_id)")
        sys.exit(1)

    # Text modes
    if args.markdown:
        markdown = get_text_or_read_file(args.markdown)
        msg_id = send_markdown(
            markdown,
            chat_id=chat_id,
            edit=args.edit,
            return_id=args.return_id,
            cancel_btn=args.with_cancel_btn,
        )
        if args.return_id and msg_id:
            print(msg_id)
    elif args.text:
        text = get_text_or_read_file(args.text)
        msg_id = send_text(
            text,
            parse_mode="",
            chat_id=chat_id,
            edit=args.edit,
            return_id=args.return_id,
            cancel_btn=args.with_cancel_btn,
        )
        if args.return_id and msg_id:
            print(msg_id)
    # Media modes
    elif args.voice:
        voice_path, was_converted = ensure_ogg_voice(args.voice)
        try:
            send_voice(voice_path, args.caption, chat_id=chat_id)
        finally:
            if was_converted:
                Path(voice_path).unlink(missing_ok=True)
    elif args.photo:
        send_photo(args.photo, args.caption, chat_id=chat_id)
    elif args.audio:
        send_audio(args.audio, args.caption, chat_id=chat_id)
    elif args.video:
        send_video(args.video, args.caption, chat_id=chat_id)
    elif args.document:
        send_document(args.document, args.caption, chat_id=chat_id)

    # Action modes
    elif args.typing:
        curl(
            [
                f"{API_BASE}/sendChatAction",
                "-d", f"chat_id={chat_id}",
                "-d", "action=typing",
            ]
        )
    elif args.remove_keyboard:
        curl(
            [
                f"{API_BASE}/editMessageReplyMarkup",
                "-d", f"chat_id={chat_id}",
                "-d", f"message_id={args.remove_keyboard}",
                "-d", "reply_markup={}",
            ]
        )
    elif args.answer_callback:
        curl(
            [
                f"{API_BASE}/answerCallbackQuery",
                "-d", f"callback_query_id={args.answer_callback}",
                "-d", "text=Cancelled",
            ]
        )


if __name__ == "__main__":
    main()
