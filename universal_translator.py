#!/usr/bin/env python3
"""
universal_translator.py
========================
A "universal translator": converts speech (any audio) OR typed text in one
language into spoken audio in another language.

Pipeline:
    audio  -> [1. Speech-to-Text]  -> text (source language)
    text   -> [2. Machine Translation] -> text (target language)
    text   -> [3. Text-to-Speech]  -> audio (target language)

This uses free, no-API-key-needed backends so it works out of the box:
    - Speech-to-text: Google's free Web Speech API, via SpeechRecognition
    - Translation:    Google Translate (unofficial, via deep-translator)
    - Text-to-speech: Google Text-to-Speech (via gTTS)

All three need an internet connection to work (they call free public web
services). This script will NOT work in a fully offline/sandboxed
environment with no internet access — but works fine on a normal machine,
Replit, Colab, etc. See the bottom of this file for an offline-alternative
note.

INSTALL:
    pip install SpeechRecognition deep-translator gTTS pydub
    # For microphone input you also need PyAudio:
    pip install pyaudio
    # pydub needs ffmpeg installed on your system for format conversion/playback:
    #   Ubuntu/Debian: sudo apt-get install ffmpeg
    #   macOS:         brew install ffmpeg
    #   Windows:       download from ffmpeg.org and add to PATH

USAGE:
    # Text -> spoken audio in another language
    python3 universal_translator.py text2audio --text "Hello, how are you?" \\
        --target es --output hello_es.mp3

    # Audio file -> spoken audio in another language (auto-detects source language)
    python3 universal_translator.py audio2audio --input input.wav \\
        --target fr --output output_fr.mp3

    # Live microphone -> spoken audio in another language
    python3 universal_translator.py mic --target ja --output spoken_ja.mp3

    # List common language codes
    python3 universal_translator.py langs
"""

import argparse
import os
import sys

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None

try:
    from gtts import gTTS
except ImportError:
    gTTS = None

try:
    from pydub import AudioSegment
    from pydub.playback import play
except ImportError:
    AudioSegment = None
    play = None


COMMON_LANGUAGES = {
    "en": "English", "es": "Spanish", "fr": "French", "de": "German",
    "it": "Italian", "pt": "Portuguese", "ru": "Russian", "ja": "Japanese",
    "ko": "Korean", "zh-CN": "Chinese (Simplified)", "ar": "Arabic",
    "hi": "Hindi", "nl": "Dutch", "tr": "Turkish", "pl": "Polish",
    "sv": "Swedish", "vi": "Vietnamese", "th": "Thai", "he": "Hebrew",
}


def require(module, name, pip_name):
    if module is None:
        sys.exit(f"Missing dependency '{name}'. Install it with:\n    pip install {pip_name}")


# ---------------------------------------------------------------------------
# 1. Speech-to-Text
# ---------------------------------------------------------------------------
def transcribe_audio_file(path: str, language_hint: str = None) -> str:
    """Convert an audio file (wav/aiff/flac; use pydub to convert mp3 first) to text."""
    require(sr, "SpeechRecognition", "SpeechRecognition")
    recognizer = sr.Recognizer()
    with sr.AudioFile(path) as source:
        audio = recognizer.record(source)
    try:
        # language_hint uses BCP-47 codes, e.g. "en-US", "es-ES"; None = auto
        text = recognizer.recognize_google(audio, language=language_hint)
        return text
    except sr.UnknownValueError:
        sys.exit("Could not understand the audio (no speech detected or too noisy).")
    except sr.RequestError as e:
        sys.exit(f"Speech recognition service error (check internet connection): {e}")


def transcribe_from_microphone(language_hint: str = None, timeout: int = 8) -> str:
    """Record a short clip from the default microphone and transcribe it."""
    require(sr, "SpeechRecognition", "SpeechRecognition")
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        print("Adjusting for ambient noise... please wait.")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Listening... speak now.")
        audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=15)
    try:
        text = recognizer.recognize_google(audio, language=language_hint)
        print(f"Heard: {text}")
        return text
    except sr.UnknownValueError:
        sys.exit("Could not understand the audio.")
    except sr.RequestError as e:
        sys.exit(f"Speech recognition service error (check internet connection): {e}")


# ---------------------------------------------------------------------------
# 2. Translation
# ---------------------------------------------------------------------------
def translate_text(text: str, target: str, source: str = "auto") -> str:
    require(GoogleTranslator, "deep-translator", "deep-translator")
    translated = GoogleTranslator(source=source, target=target).translate(text)
    return translated


# ---------------------------------------------------------------------------
# 3. Text-to-Speech
# ---------------------------------------------------------------------------
def speak_text(text: str, lang: str, output_path: str, auto_play: bool = True):
    require(gTTS, "gTTS", "gTTS")
    tts = gTTS(text=text, lang=lang)
    tts.save(output_path)
    print(f"Saved translated speech to: {output_path}")

    if auto_play:
        if AudioSegment is not None and play is not None:
            try:
                audio = AudioSegment.from_file(output_path, format="mp3")
                play(audio)
            except Exception as e:
                print(f"(Could not auto-play audio: {e}. The file is saved and can be played manually.)")
        else:
            print("(Install pydub + ffmpeg to auto-play; file is saved and can be played manually.)")


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------
def mode_text2audio(args):
    print(f"Original text: {args.text}")
    translated = translate_text(args.text, target=args.target, source=args.source)
    print(f"Translated ({args.target}): {translated}")
    speak_text(translated, lang=args.target, output_path=args.output, auto_play=not args.no_play)


def mode_audio2audio(args):
    text = transcribe_audio_file(args.input, language_hint=args.source_hint)
    print(f"Transcribed text: {text}")
    translated = translate_text(text, target=args.target, source=args.source)
    print(f"Translated ({args.target}): {translated}")
    speak_text(translated, lang=args.target, output_path=args.output, auto_play=not args.no_play)


def mode_mic(args):
    text = transcribe_from_microphone(language_hint=args.source_hint)
    translated = translate_text(text, target=args.target, source=args.source)
    print(f"Translated ({args.target}): {translated}")
    speak_text(translated, lang=args.target, output_path=args.output, auto_play=not args.no_play)


def mode_langs(args):
    print("Common language codes (use with --target / --source):")
    for code, name in sorted(COMMON_LANGUAGES.items()):
        print(f"  {code:<8} {name}")
    print("\nMany more are supported — deep-translator and gTTS both follow")
    print("Google Translate's language codes.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser():
    parser = argparse.ArgumentParser(
        description="Universal translator: audio-to-audio and text-to-audio translation."
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    p_text = sub.add_parser("text2audio", help="Translate typed text into spoken audio")
    p_text.add_argument("--text", required=True, help="Text to translate")
    p_text.add_argument("--source", default="auto", help="Source language code, e.g. 'en' (default: auto-detect)")
    p_text.add_argument("--target", required=True, help="Target language code, e.g. 'es'")
    p_text.add_argument("--output", default="translated.mp3", help="Output audio file path")
    p_text.add_argument("--no-play", action="store_true", help="Don't auto-play the result")
    p_text.set_defaults(func=mode_text2audio)

    p_audio = sub.add_parser("audio2audio", help="Translate a spoken audio file into spoken audio")
    p_audio.add_argument("--input", required=True, help="Path to input audio file (wav/flac/aiff)")
    p_audio.add_argument("--source", default="auto", help="Source language code for translation step (default: auto-detect)")
    p_audio.add_argument("--source-hint", default=None, help="BCP-47 hint for speech recognition, e.g. 'en-US' (improves accuracy)")
    p_audio.add_argument("--target", required=True, help="Target language code, e.g. 'fr'")
    p_audio.add_argument("--output", default="translated.mp3", help="Output audio file path")
    p_audio.add_argument("--no-play", action="store_true", help="Don't auto-play the result")
    p_audio.set_defaults(func=mode_audio2audio)

    p_mic = sub.add_parser("mic", help="Translate live microphone speech into spoken audio")
    p_mic.add_argument("--source", default="auto", help="Source language code for translation step")
    p_mic.add_argument("--source-hint", default=None, help="BCP-47 hint for speech recognition, e.g. 'en-US'")
    p_mic.add_argument("--target", required=True, help="Target language code, e.g. 'ja'")
    p_mic.add_argument("--output", default="translated.mp3", help="Output audio file path")
    p_mic.add_argument("--no-play", action="store_true", help="Don't auto-play the result")
    p_mic.set_defaults(func=mode_mic)

    p_langs = sub.add_parser("langs", help="List common language codes")
    p_langs.set_defaults(func=mode_langs)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# OFFLINE ALTERNATIVE (note, not implemented above)
# ---------------------------------------------------------------------------
# If you need this to work with NO internet connection at all, swap each
# stage for an offline-capable library instead:
#   1. Speech-to-text: openai-whisper or vosk (run fully local, but need a
#      one-time model download, e.g. a few hundred MB to a few GB)
#   2. Translation:    argos-translate (downloads small offline language
#      packs once, then translates fully offline)
#   3. Text-to-speech: espeak-ng (fully offline, already used in the C++
#      text_to_audio program from earlier in this conversation) or a local
#      neural TTS like Coqui TTS for more natural voices
# Ask if you'd like this offline variant built out instead/as well — it's a
# heavier install but needs no internet at runtime.
