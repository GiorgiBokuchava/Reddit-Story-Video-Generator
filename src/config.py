import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

def _load_subreddits() -> list[str]:
    raw = os.getenv("SUBREDDITS", "")
    return [s.strip() for s in raw.split(",") if s.strip()]

def _str_to_bool(val: str) -> bool:
    return val.strip().lower() in ("1","true","yes","y","on")

@dataclass(frozen=True)
class Settings:
    # Reddit
    reddit_client_id: str = os.getenv("REDDIT_CLIENT_ID","")
    reddit_client_secret: str = os.getenv("REDDIT_CLIENT_SECRET","")
    reddit_user_agent: str = os.getenv("REDDIT_USER_AGENT","")

    # TTS
    tts_provider: str = os.getenv("TTS_PROVIDER","elevenlabs")
    edge_tts_voice: str = os.getenv("EDGE_TTS_VOICE","en-US-JennyNeural")
    edge_tts_rate: str = os.getenv("EDGE_TTS_RATE","+10%")
    elevenlabs_api_key: str = os.getenv("ELEVENLABS_API_KEY","")
    elevenlabs_voice_id: str = os.getenv("ELEVENLABS_VOICE_ID","21m00Tcm4TlvDq8ikWAM")
    elevenlabs_use_ssml: bool = _str_to_bool(os.getenv("ELEVENLABS_USE_SSML","false"))
    elevenlabs_prosody_rate:str= os.getenv("ELEVENLABS_PROSODY_RATE","100%")
    elevenlabs_stability: float= float(os.getenv("ELEVENLABS_STABILITY","0.75"))
    elevenlabs_similarity_boost: float = float(os.getenv("ELEVENLABS_SIMILARITY_BOOST","0.85"))

    # Subtitles
    template_ass: str = "captions/captions.ass"
    output_ass: str = "captions/captions_karaoke.ass"

    # Audio
    audio_mp3: str = "output/combined.mp3"
    audio_wav: str = "output/combined.wav"

    # Fonts/models
    model_dir: str = "model"
    fonts_dir: str = "assets/font"

    # Post‐finder
    subreddits: list[str] = field(default_factory=_load_subreddits)
    min_comments: int = int(os.getenv("MIN_COMMENTS","10"))
    min_post_length: int = int(os.getenv("MIN_POST_LENGTH","100"))
    used_posts_file: str = "used_posts.json"
    allow_nsfw: bool = _str_to_bool(os.getenv("ALLOW_NSFW","false"))

    # Drive
    drive_backgrounds_folder_id: str = os.getenv("DRIVE_BACKGROUNDS_FOLDER_ID","")
    drive_outputs_folder_id:     str = os.getenv("DRIVE_OUTPUTS_FOLDER_ID","")

    # Toggles
    upload_to_drive: bool = _str_to_bool(os.getenv("UPLOAD_DRIVE","true"))
    upload_to_youtube: bool = _str_to_bool(os.getenv("UPLOAD_YT","true"))

    # Thumbnail
    thumbnail_template_svg: str = "assets/Reddit Thumbnail.svg"
    thumbnail_populated_svg: str = "output/populated.svg"
    thumbnail_output_png: str = "output/thumbnail.png"
    thumbnail_font_path: str = "assets/fonts/Inter_18pt-Bold.ttf"
    thumbnail_sub_font_size: int = 56
    thumbnail_title_font_size:int = 68
    thumbnail_padding: int = 32

    # YouTube tags
    youtube_video_tags: list[str] = field(default_factory=lambda: ["#TIFU","#RedditStories","#StoryTime","#Reddit"])

settings = Settings()
