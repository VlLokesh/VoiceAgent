"""
Example of integrating ConversationRecorder with main.py
This shows how to enable full audio recording (user + assistant).
"""

# In main.py, add this import at the top:
# from audio_recorder import ConversationRecorder

# Then modify the VoiceAgent class:

class VoiceAgent:
    def __init__(self):
        # ... existing initialization ...
        
        # Initialize audio recorder
        session_id = self.logger.session_id
        self.audio_recorder = ConversationRecorder(session_id)
        self.audio_recorder.start_recording()
        
    def process_user_input(self, user_text: str):
        # ... existing code ...
        
        # After TTS synthesis
        audio_path = self.tts.synthesize(assistant_response, play=True)
        
        # Record assistant response
        if audio_path:
            self.audio_recorder.add_assistant_response(audio_path)
            
    def run(self):
        # ... existing STT start code ...
        
        # Modify the audio stream callback to include recording
        def audio_callback(indata, frames, time_info, status):
            if status:
                print("Audio status:", status)
            
            # Record user audio
            self.audio_recorder.add_audio_chunk(indata.tobytes())
            
            # Send to STT
            try:
                if self.stt.connection:
                    self.stt.connection.send_media(indata.tobytes())
            except Exception as e:
                print("Failed sending audio:", e)
        
        # Use modified callback
        with sd.InputStream(
            callback=audio_callback,  # Use our callback instead
            channels=1,
            samplerate=16000,
            dtype='int16'
        ):
            # ... rest of conversation loop ...
    
    def shutdown(self):
        # ... existing shutdown code ...
        
        # Stop audio recording and merge
        self.audio_recorder.stop_recording()
        conversation_audio = self.audio_recorder.merge_conversation()
        
        if conversation_audio:
            print(f"🎧 Full conversation audio: {conversation_audio}")
        
        # Get recording stats
        stats = self.audio_recorder.get_recording_stats()
        print(f"📊 Audio stats: {stats}")
        
        # Optionally cleanup temp files
        # self.audio_recorder.cleanup_temp_files()


# COMPLETE MODIFIED main.py EXAMPLE
# Copy this to main.py to enable full audio recording:

"""
from audio_recorder import ConversationRecorder

class VoiceAgent:
    def __init__(self):
        load_dotenv()
        
        if not os.getenv("DEEPGRAM_API_KEY"):
            raise SystemExit("❌ DEEPGRAM_API_KEY is not set.")
        
        print("🚀 Initializing DropTruck AI Sales Agent...")
        
        self.logger = WorkflowLogger()
        self.logger.log_info("Voice Agent initialization started")
        
        # Initialize audio recorder FIRST (needs session_id)
        self.audio_recorder = ConversationRecorder(self.logger.session_id)
        self.audio_recorder.start_recording()
        
        self.logger.log_info("Initializing Speech-to-Text component")
        self.stt = SpeechToText()
        
        self.logger.log_info("Initializing Text-to-Speech component")
        self.tts = TextToSpeech()
        
        self.logger.log_info("Initializing LLM Agent component")
        self.llm = LLMAgent(logger=self.logger)
        
        self.current_transcript = []
        self.segment_ready = False
        self.audio_stream = None
        
        self.logger.log_info("Voice Agent initialization complete")
        print("✅ DropTruck AI Sales Agent initialized")
        print(f"📼 Recording to: audio_output/session_{self.logger.session_id}/")
    
    def on_transcript(self, text: str):
        print(f"You: {text}")
        self.current_transcript.append(text)
    
    def on_final(self, text: str):
        self.segment_ready = True
    
    def on_error(self, error):
        error_msg = f"STT Error: {error}"
        print(f"⚠️  {error_msg}")
        self.logger.log_error(error_msg)
    
    def process_user_input(self, user_text: str):
        if not user_text.strip():
            return
        
        print(f"\n📝 User (final): {user_text}")
        self.logger.log_info(f"Processing user input: {user_text[:50]}...")
        
        assistant_response = self.llm.generate_response(user_text)
        print(f"💬 Assistant: {assistant_response}")
        
        # Synthesize and record
        audio_path = self.tts.synthesize(assistant_response, play=True)
        
        if audio_path:
            self.audio_recorder.add_assistant_response(audio_path)
            self.logger.log_info("TTS synthesis and playback successful")
            print("🎵 Response complete\n")
        else:
            self.logger.log_warning("TTS synthesis failed")
            print("⚠️  TTS failed, continuing...\n")
    
    def run(self):
        try:
            self.logger.log_info("Starting Speech-to-Text stream")
            self.stt.start(
                on_transcript=self.on_transcript,
                on_final=self.on_final,
                on_error=self.on_error
            )
            
            print("\n" + "="*60)
            print("🎤 DROPTRUCK AI SALES AGENT READY")
            print("Press ENTER or Ctrl+C to end the call")
            print("="*60 + "\n")
            
            self.logger.log_info("Voice Agent ready - Conversation loop started")
            
            # Custom audio callback that records AND sends to STT
            def audio_callback(indata, frames, time_info, status):
                if status:
                    print("Audio status:", status)
                
                # Record user audio
                self.audio_recorder.add_audio_chunk(indata.tobytes())
                
                # Send to STT
                try:
                    if self.stt.connection:
                        self.stt.connection.send_media(indata.tobytes())
                except Exception as e:
                    print("Failed sending audio:", e)
            
            with sd.InputStream(
                callback=audio_callback,
                channels=1,
                samplerate=16000,
                dtype='int16'
            ):
                while True:
                    if self.segment_ready:
                        self.segment_ready = False
                        
                        user_text = " ".join(self.current_transcript).strip()
                        self.current_transcript.clear()
                        
                        if user_text:
                            self.process_user_input(user_text)
                    
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
        print("\n🛑 Shutting down...")
        self.logger.log_info("Shutdown initiated")
        
        # Stop STT
        self.stt.stop()
        
        # Stop audio recording
        self.audio_recorder.stop_recording()
        
        # Print booking summary
        self.print_booking_summary()
        
        # Save session logs
        booking_data = self.llm.get_booking_data()
        self.logger.log_session_end(booking_data.to_dict())
        
        # Merge conversation audio
        print("\n🎬 Creating full conversation audio...")
        conversation_path = self.audio_recorder.merge_conversation()
        
        if conversation_path:
            print(f"✅ Full conversation audio: {conversation_path}")
        
        # Get recording stats
        stats = self.audio_recorder.get_recording_stats()
        print(f"\n📊 Audio Recording Stats:")
        print(f"   User audio: {stats.get('user_audio_size_mb', 0):.2f} MB")
        print(f"   Assistant responses: {stats['assistant_responses']}")
        print(f"   Full conversation: {stats.get('conversation_size_mb', 0):.2f} MB")
        
        # Cleanup old audio files
        self.tts.cleanup_old_files()
        
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
        booking_data = self.llm.get_booking_data()
        print(booking_data)
        print(self.llm.get_conversation_summary())


def main():
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
"""
