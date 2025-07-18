# cozmoAgent
A voice-controlled Cozmo robot agent built with SmolAgents and Retico framework. Transform natural speech commands into executable robot behaviors!

## Overview 📋
This module bridges speech recognition with Cozmo robot control using AI agents. This module transforms voice commands into step-by-step execution plans using Cozmo behavior functions. It doesn't actually control the robot - instead, it creates GenericDictIU that you can pass to a DM or CozmoModule to make Cozmo execute the tasks
***Available Commands 🎯***
- "drive_straight()"
- "turn_in_place()"
- "say_text()"
- "look_around()"
- "go_to_object()"
- "drive_to_charger()"
- "move_head()"

## Installation 🚀
**Requirements**
- Python 3.10.
- smolagent: 1.19.x

**Set up**
1. Clone this repository:
   ```bash
   git clone: https://github.com/AnhBui1108/cozmoAgent.git
   cd cozmoAgent
   ```
   
2. Replace "YOUR-API_KEY" in the code with your actual key

### Example:
```bash
import os, sys

from smolagents import CodeAgent, DuckDuckGoSearchTool
from smolagents.models import OpenAIServerModel

prefix = '<path-to-retico-module-repositories>'

os.environ['RETICO'] = prefix +'retico_core'
os.environ['WS']= prefix + 'retico-whisperasr'
os.environ['AG']= prefix + 'cozmoAgent'
os.environ['TTS'] = prefix + 'retico-speechbraintts'

sys.path.append(os.environ['RETICO'])
sys.path.append(os.environ['WS'])
sys.path.append(os.environ['AG'])
sys.path.append(os.environ['TTS'])

from retico_core.debug import DebugModule
from retico_core.audio import MicrophoneModule,  SpeakerModule
from retico_whisperasr.whisperasr import WhisperASRModule
from cozmoSmolAgents import CozmoSmolAgentsModule

mic = MicrophoneModule(chunk_size = 320, rate = 16000)
debug = DebugModule()
asr = WhisperASRModule()
dm = CozmoSmolAgentsModule()

mic.subscribe(asr)
asr.subscribe(dm)
dm.subscribe(debug)

mic.run()
asr.run()
dm.run()
debug.run()

input()

asr.stop()
mic.stop()
dm.stop()
debug.stop()

