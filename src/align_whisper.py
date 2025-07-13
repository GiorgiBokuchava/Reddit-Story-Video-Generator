import whisper
import sys

def main(audio_path: str):
    # Load the tiny English model (~75 MB)
    model = whisper.load_model("tiny.en")

    # Transcribe with word timestamps enabled
    result = model.transcribe(
        audio_path,
        word_timestamps=True,
        verbose=False
    )

    # Print out each word + its start/end (in seconds)
    print("Word-level timestamps:")
    for segment in result["segments"]:
        for w in segment["words"]:
            print(f"{w['word']!r}: {w['start']:.2f}s -> {w['end']:.2f}s")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python quick_test_whisper.py <path_to_audio.wav>")
        sys.exit(1)
    main(sys.argv[1])
