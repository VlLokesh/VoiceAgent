"""
Main orchestration module for the voice agent.
Coordinates STT, LLM, and TTS components to manage booking conversations.
"""

import os
import sys
import time
import sounddevice as sd
from dotenv import load_dotenv

from app.stt import SpeechToText
from app.tts import TextToSpeech
from app.llm import LLMAgent
from prompt import BookingData
from logs.logger import WorkflowLogger


class VoiceAgent:
    """Main voice agent orchestrator."""
    
    def __init__(self):
        """Initialize the voice agent with all components."""
        # Load environment variables
        load_dotenv()
        
        # Validate required API keys
        if not os.getenv("DEEPGRAM_API_KEY"):
            raise SystemExit(
                "❌ DEEPGRAM_API_KEY is not set.\n"
                "Please set it in your .env file or environment:\n"
                "  export DEEPGRAM_API_KEY=your_key_here\n"
            )
        
        # Initialize components
        print("🚀 Initializing DropTruck AI Sales Agent...")
        
        # Initialize logger
        self.logger = WorkflowLogger()
        
        # Initialize STT, TTS, and LLM with logger
        self.stt = SpeechToText()
        self.tts = TextToSpeech()
        self.llm = LLMAgent(logger=self.logger)
        
        # Conversation state
        self.current_transcript = []
        self.segment_ready = False
        self.audio_stream = None
        
        print("✅ DropTruck AI Sales Agent initialized")
    
    def on_transcript(self, text: str):
        """Handle partial transcript from STT."""
        print(f"You: {text}")
        self.current_transcript.append(text)
    
    def on_final(self, text: str):
        """Handle final transcript segment from STT."""
        self.segment_ready = True
    
    def on_error(self, error):
        """Handle STT errors."""
        print(f"⚠️  STT Error: {error}")
    
    def process_user_input(self, user_text: str):
        """
        Process user input through LLM and generate TTS response.
        
        Args:
            user_text: Final transcribed user text
        """
        if not user_text.strip():
            return
        
        print(f"\n📝 User (final): {user_text}")
        
        # Generate LLM response
        assistant_response = self.llm.generate_response(user_text)
        print(f"💬 Assistant: {assistant_response}")
        
        # Synthesize and play response
        audio_path = self.tts.synthesize(assistant_response, play=True)
        
        if audio_path:
            print("🎵 Response complete\n")
        else:
            print("⚠️  TTS failed, continuing...\n")
    
    def run(self):
        """Run the main conversation loop."""
        try:
            # Start STT
            self.stt.start(
                on_transcript=self.on_transcript,
                on_final=self.on_final,
                on_error=self.on_error
            )
            
            # Start audio stream
            print("\n" + "="*60)
            print("🎤 DROPTRUCK AI SALES AGENT READY")
            print("Press ENTER or Ctrl+C to end the call")
            print("="*60 + "\n")
            
            with sd.InputStream(
                callback=self.stt.get_audio_callback(),
                channels=1,
                samplerate=16000,
                dtype='int16'
            ):
                while True:
                    # Check if we have a complete segment to process
                    if self.segment_ready:
                        self.segment_ready = False
                        
                        # Consolidate transcript
                        user_text = " ".join(self.current_transcript).strip()
                        self.current_transcript.clear()
                        
                        if user_text:
                            self.process_user_input(user_text)
                    
                    # Small sleep to prevent busy waiting
                    time.sleep(0.1)
        
        except KeyboardInterrupt:
            print("\n\n⏹️  Call ended by user (Ctrl+C)")
        
        except Exception as e:
            print(f"\n❌ Runtime error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown of all components."""
        print("\n🛑 Shutting down...")
        
        # Stop STT
        self.stt.stop()
        
        # Print collected booking information
        self.print_booking_summary()
        
        # Save session logs
        booking_data = self.llm.get_booking_data()
        self.logger.log_session_end(booking_data.to_dict())
        
        # Cleanup old audio files
        self.tts.cleanup_old_files()
        
        print("✅ Shutdown complete")
        print(f"\n📄 Logs saved to:")
        print(f"   Text: {self.logger.get_log_path()}")
        print(f"   JSON: {self.logger.get_json_log_path()}")
    
    def print_booking_summary(self):
        """Print the collected booking information after call ends."""
        booking_data = self.llm.get_booking_data()
        print(booking_data)
        
        # Additional conversation stats
        print(self.llm.get_conversation_summary())


def main():
    """Entry point for the voice agent."""
    try:
        agent = VoiceAgent()
        agent.run()
    except Exception as e:
        print(f"\n❌ Failed to start voice agent: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
