# Voice Agent for Transport Booking

A modular voice agent system for collecting transport/logistics booking information through natural conversation.

## Features

- 🎤 **Real-time Speech-to-Text** using Deepgram
- 🤖 **Intelligent Conversation** powered by OpenAI
- 🔊 **Natural Text-to-Speech** using Deepgram TTS
- 📋 **Structured Data Collection** for transport bookings
- 🖨️ **Post-Call Summary** of all collected information

## Required Information

The agent collects the following booking details:

1. **Pickup Location** (City / Area / Full Address)
2. **Drop Location**
3. **Vehicle Type** (Truck or specific vehicle model)
4. **Body Type** ("Open" or "Container")
5. **Goods/Material Type** (e.g., cement, FMCG, machinery)
6. **Trip Date** (Required date of the trip)

## Architecture

The system is organized into modular components:

- **`main.py`** - Main orchestrator, manages conversation loop
- **`stt.py`** - Speech-to-Text using Deepgram real-time API
- **`tts.py`** - Text-to-Speech synthesis and playback
- **`llm.py`** - OpenAI integration and conversation management
- **`prompt.py`** - System prompt and booking data structure

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
DEEPGRAM_API_KEY=your_deepgram_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

**Get API Keys:**
- Deepgram: https://console.deepgram.com/
- OpenAI: https://platform.openai.com/api-keys

### 3. Run the Agent

```bash
python main.py
```

## Usage

1. **Start the agent**: Run `python main.py`
2. **Speak naturally**: The agent will greet you and start collecting information
3. **Provide booking details**: Answer the agent's questions about your transport needs
4. **End the call**: Press `ENTER` or `Ctrl+C` when done
5. **View summary**: All collected information will be printed after the call ends

## Example Conversation

```
Agent: Hello! I'm here to help you book transport services. 
       Could you tell me where you need the pickup from?

You: I need pickup from Mumbai, Andheri West.

Agent: Great! And where would you like the goods delivered to?

You: To Pune, Hinjewadi.

Agent: Perfect. What type of vehicle do you need?

You: I need a truck.

Agent: Got it. Would you prefer an open truck or a container?

You: Container please.

Agent: What type of goods will you be transporting?

You: FMCG products.

Agent: And when do you need this trip?

You: Tomorrow, December 25th.

Agent: Excellent! Let me confirm the details...
```

After ending the call, you'll see:

```
============================================================
BOOKING INFORMATION COLLECTED
============================================================
Pickup Location.................... Mumbai, Andheri West
Drop Location...................... Pune, Hinjewadi
Vehicle Type....................... Truck
Body Type.......................... Container
Goods/Material Type................ FMCG products
Trip Date.......................... December 25th
============================================================
```

## Platform Support

- **macOS**: Full support (uses `afplay` for audio)
- **Linux**: Supported (requires `aplay` or `mpg123`)
- **Windows**: Supported (uses `start` command)

## Troubleshooting

### Connection Issues

If you see connection errors:

1. Verify your `DEEPGRAM_API_KEY` is valid
2. Check your internet connection
3. Ensure no VPN/proxy is interfering
4. Try upgrading the SDK: `pip install --upgrade deepgram-sdk`

### Audio Issues

If audio playback doesn't work:

- **macOS**: `afplay` should be pre-installed
- **Linux**: Install `aplay` (ALSA) or `mpg123`
  ```bash
  sudo apt-get install alsa-utils  # for aplay
  # or
  sudo apt-get install mpg123
  ```

### API Errors

If you see OpenAI API errors:

1. Verify your `OPENAI_API_KEY` is valid
2. Check you have sufficient API credits
3. Ensure the model name is correct (default: `gpt-4o-mini`)


### Deployment Steps

1. **Package the application**:
   ```bash
   # Create deployment package
   zip -r voice_agent.zip *.py requirements.txt .env.example
   ```

2. **Configure Antigravity Agent**:
   - Set environment variables in the Antigravity console
   - Upload the packaged application
   - Configure entry point: `main.py`

3. **Set Environment Variables** in Antigravity:
   ```
   DEEPGRAM_API_KEY=<your_key>
   OPENAI_API_KEY=<your_key>
   OPENAI_MODEL=gpt-4o-mini
   ```

4. **Deploy and Test**:
   - Deploy the agent to Sonnet 4.5
   - Test with a sample conversation
   - Monitor logs for any issues

### Antigravity-Specific Configuration

For deployment on Antigravity Agents, you may need to:

- Adjust audio input/output handling based on the platform's audio interface
- Modify the `main.py` entry point if Antigravity requires a specific function signature
- Configure webhook endpoints if the agent needs to send booking data to external systems

> [!NOTE]
> Contact your Antigravity Agents administrator for platform-specific deployment requirements and audio interface specifications.

## Development

### Project Structure

```
Voice_Agent/
├── main.py           # Main orchestrator
├── stt.py            # Speech-to-Text module
├── tts.py            # Text-to-Speech module
├── llm.py            # LLM integration
├── prompt.py         # Prompts and data structures
├── requirements.txt  # Python dependencies
├── .env.example      # Environment template
├── .env              # Your API keys (gitignored)
└── audio_output/     # Generated audio files (auto-created)
```

### Extending the Agent

To add more booking fields:

1. Update `REQUIRED_FIELDS` in `prompt.py`
2. Add fields to `BookingData` class
3. Update `SYSTEM_PROMPT` to include new fields
4. The agent will automatically collect the new information

## License

This project is provided as-is for transport booking automation.

## Support

For issues or questions:
- Check the troubleshooting section above
- Review Deepgram documentation: https://developers.deepgram.com/
- Review OpenAI documentation: https://platform.openai.com/docs/
