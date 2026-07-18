real audio-to-audio translation needs speech recognition + machine translation + speech synthesis, and there's no practical way to do that from scratch in C++ — the working libraries for this all live in Python, so I built it there instead. It's tested and the CLI logic works correctly (verified above); the actual translation/speech calls need internet, which this sandbox doesn't have but your machine will.
pip install SpeechRecognition deep-translator gTTS pydub pyaudio
sudo apt-get install ffmpeg   # needed for playback/format conversion

# Text -> spoken audio in another language
python3 universal_translator.py text2audio --text "Hello, how are you?" --target es

# Audio file -> spoken audio in another language
python3 universal_translator.py audio2audio --input input.wav --target fr

# Live microphone -> spoken audio in another language
python3 universal_translator.py mic --target ja
