"""
Text-to-Speech module using Deepgram's TTS API.
Handles speech synthesis and audio playback.
"""

import os
import time
import platform
from deepgram import DeepgramClient


class TextToSpeech:
    """Manages text-to-speech synthesis using Deepgram."""
    
    def __init__(self, api_key: str = None, model: str = "aura-asteria-en"):
        """
        Initialize TTS with Deepgram API key.
        
        Args:
            api_key: Deepgram API key (reads from env if not provided)
            model: Deepgram TTS model to use
        """
        self.api_key = api_key or os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DEEPGRAM_API_KEY is required. Set it in environment or .env file."
            )
        
        self.client = DeepgramClient(api_key=self.api_key)
        self.model = model
        self.output_dir = "audio_output"
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    def synthesize(self, text: str, play: bool = True) -> str:
        """
        Synthesize text to speech and optionally play it.
        
        Args:
            text: Text to synthesize
            play: Whether to play the audio after synthesis
            
        Returns:
            Path to the generated audio file
        """
        if not text or not text.strip():
            print("⚠️  No text to synthesize")
            return ""
        
        # Generate unique filename
        timestamp = int(time.time() * 1000)
        filename = f"assistant_reply_{timestamp}.mp3"
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            print("🔊 Synthesizing speech...")
            
            # Generate speech using Deepgram
            speak_stream = self.client.speak.v1.audio.generate(
                text=text,
                model=self.model,
            )
            
            # Write audio to file
            with open(filepath, "wb") as f:
                for chunk in speak_stream:
                    f.write(chunk)
            
            print(f"✅ Audio saved to: {filepath}")
            
            # Play audio if requested
            if play:
                self._play_audio(filepath)
            
            return filepath
            
        except Exception as e:
            print(f"❌ TTS synthesis failed: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def _play_audio(self, filepath: str):
        """
        Play audio file using platform-specific command.
        
        Args:
            filepath: Path to audio file to play
        """
        if not os.path.exists(filepath):
            print(f"⚠️  Audio file not found: {filepath}")
            return
        
        try:
            print("▶️  Playing audio...")
            
            system = platform.system()
            if system == "Darwin":  # macOS
                os.system(f"afplay '{filepath}'")
            elif system == "Linux":
                # Try common Linux audio players
                if os.system("which aplay > /dev/null 2>&1") == 0:
                    os.system(f"aplay '{filepath}'")
                elif os.system("which mpg123 > /dev/null 2>&1") == 0:
                    os.system(f"mpg123 '{filepath}'")
                else:
                    print("⚠️  No audio player found (aplay or mpg123)")
            elif system == "Windows":
                os.system(f"start {filepath}")
            else:
                print(f"⚠️  Unsupported platform for audio playback: {system}")
                return
            
            print("✅ Playback complete")
            
        except Exception as e:
            print(f"❌ Audio playback failed: {e}")
    
    def cleanup_old_files(self, max_age_seconds: int = 3600):
        """
        Remove old audio files from output directory.
        
        Args:
            max_age_seconds: Maximum age of files to keep (default: 1 hour)
        """
        try:
            current_time = time.time()
            for filename in os.listdir(self.output_dir):
                filepath = os.path.join(self.output_dir, filename)
                if os.path.isfile(filepath):
                    file_age = current_time - os.path.getmtime(filepath)
                    if file_age > max_age_seconds:
                        os.remove(filepath)
                        print(f"🗑️  Removed old audio file: {filename}")
        except Exception as e:
            print(f"⚠️  Cleanup failed: {e}")
