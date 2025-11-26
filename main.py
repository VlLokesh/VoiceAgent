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
from core.logger import WorkflowLogger
from core.audio_recorder import ConversationRecorder
from core.api_client import DropTruckAPIClient


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
        
        # Initialize logger with storage/logs directory
        self.logger = WorkflowLogger(logs_dir="storage/logs")
        self.logger.log_info("Voice Agent initialization started")

        # Initialize audio recorder
        self.audio_recorder = ConversationRecorder(self.logger.session_id)
        self.audio_recorder.start_recording()
        self.logger.log_info(f"Audio recording started: session_{self.logger.session_id}")

        # Initialize STT, TTS, and LLM with logger
        self.logger.log_info("Initializing Speech-to-Text component")
        self.stt = SpeechToText()

        self.logger.log_info("Initializing Text-to-Speech component")
        # Pass session directory to TTS for saving audio files
        session_audio_dir = f"storage/audio_output/session_{self.logger.session_id}"
        self.tts = TextToSpeech(output_dir=session_audio_dir)

        self.logger.log_info("Initializing LLM Agent component")
        self.llm = LLMAgent(logger=self.logger)
        
        # Conversation state
        self.current_transcript = []
        self.segment_ready = False
        self.audio_stream = None
        self.call_complete = False  # Flag to trigger shutdown
        
        self.logger.log_info("Voice Agent initialization complete")
        print("✅ DropTruck AI Sales Agent initialized")
        print(f"📼 Recording conversation to: audio_output/session_{self.logger.session_id}/")
    
    def on_transcript(self, text: str):
        """Handle partial transcript from STT."""
        print(f"You: {text}")
        self.current_transcript.append(text)
    
    def on_final(self, text: str):
        """Handle final transcript segment from STT."""
        self.segment_ready = True
    
    def on_error(self, error):
        """Handle STT errors."""
        error_msg = f"STT Error: {error}"
        print(f"⚠️  {error_msg}")
        self.logger.log_error(error_msg)

    def process_user_input(self, user_text: str):
        """
        Process user input through LLM and generate TTS response.
        
        Args:
            user_text: Final transcribed user text
        """
        if not user_text.strip():
            return
        
        print(f"\n📝 User (final): {user_text}")
        self.logger.log_info(f"Processing user input: {user_text[:50]}...")

        # Generate LLM response
        assistant_response = self.llm.generate_response(user_text)
        print(f"💬 Assistant: {assistant_response}")
        
        # Synthesize and play response
        audio_path = self.tts.synthesize(assistant_response, play=True)
        
        # If audio was saved to file, record it for conversation merge
        if audio_path:
            self.audio_recorder.add_assistant_response(audio_path)

        self.logger.log_info("TTS synthesis and playback successful")
        print("🎵 Response complete\n")

        # Check if call should be completed
        if self.llm.is_call_complete():
            print("\n✅ Call completed - closing conversation")
            self.logger.log_info("Call auto-completed based on closing phrase")
            self.call_complete = True
    
    def run(self):
        """Run the main conversation loop."""
        try:
            # Start STT
            self.logger.log_info("Starting Speech-to-Text stream")
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
            
            self.logger.log_info("Voice Agent ready - Conversation loop started")

            # Custom audio callback that records AND sends to STT
            def audio_callback(indata, frames, time_info, status):
                if status:
                    print("Audio status:", status)
                
                # Record user audio for conversation merge
                self.audio_recorder.add_audio_chunk(indata.tobytes())
                
                # Send to STT
                try:
                    if self.stt.connection:
                        self.stt.connection.send_media(indata.tobytes())
                except Exception as e:
                    print("Failed sending audio:", e)

            with sd.InputStream(
                callback=audio_callback,  # Use our custom callback
                channels=1,
                samplerate=16000,
                dtype='int16'
            ):
                while True:
                    # Check if call is complete
                    if self.call_complete:
                        print("\n📞 Call ending gracefully...")
                        break
                    
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
            self.logger.log_info("Call ended by user (KeyboardInterrupt)")

        except Exception as e:
            error_msg = f"Runtime error: {e}"
            print(f"\n❌ {error_msg}")
            self.logger.log_error(error_msg)
            import traceback
            traceback.print_exc()
        
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown of all components."""
        print("\n🛑 Shutting down...")
        self.logger.log_info("Shutdown initiated")

        # Stop STT
        self.stt.stop()
        
        # Stop audio recording
        self.audio_recorder.stop_recording()
        
        # Small delay to ensure TTS playback completes and files are written
        print("⏳ Waiting for audio processing to complete...")
        time.sleep(2)
        
        # Print collected booking information
        self.print_booking_summary()
        
        # Save session logs
        booking_data = self.llm.get_booking_data()
        self.logger.log_session_end(booking_data.to_dict())
        
        # Merge conversation audio into single file
        print("\n🎬 Creating full conversation audio...")
        conversation_path = self.audio_recorder.merge_conversation()
        
        if conversation_path:
            print(f"✅ Full conversation audio saved: {conversation_path}")
            self.logger.log_info(f"Full conversation audio: {conversation_path}")
        
        # Get recording stats
        stats = self.audio_recorder.get_recording_stats()
        if stats.get('conversation_exists'):
            print(f"\n📊 Audio Recording Stats:")
            print(f"   Assistant responses recorded: {stats['assistant_responses']}")
            if stats.get('conversation_size_mb'):
                print(f"   Full conversation: {stats.get('conversation_size_mb', 0):.2f} MB")
        
        # Cleanup old audio files (files older than 1 hour in base audio_output dir)
        self.tts.cleanup_old_files()
        
        # Send booking data to API if confirmed
        if self.llm.booking_data.confirmation_status == "confirmed":
            print("\n📡 Sending booking to DropTruck API...")
            api_client = DropTruckAPIClient()
            success = api_client.send_booking(booking_data.to_dict())
            if success:
                self.logger.log_info("Booking data sent to API successfully")
            else:
                self.logger.log_warning("Failed to send booking data to API")
        else:
            print(f"\n⚠️  Booking not confirmed (status: {self.llm.booking_data.confirmation_status}), skipping API submission")
        
        self.logger.log_info("Shutdown complete")
        print("\n✅ Shutdown complete")
        print(f"\n📄 Logs saved to:")
        print(f"   Session (text): {self.logger.get_log_path()}")
        print(f"   Session (JSON): {self.logger.get_json_log_path()}")
        print(f"\n📝 Unified logs:")
        print(f"   Runtime log: {self.logger.get_runtime_log_path()}")
        print(f"   Sessions log: {self.logger.get_sessions_log_path()}")
        print(f"\n💡 To tail runtime logs, run:")
        print(f"   tail -f {self.logger.get_runtime_log_path()}")
        print(f"\n💡 To tail sessions logs, run:")
        print(f"   tail -f {self.logger.get_sessions_log_path()}")

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
