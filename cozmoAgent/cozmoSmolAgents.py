import threading
import logging
import re
from typing import List, Dict, Any
import json


import retico_core, smolagents

from retico_core import abstract
from retico_core.text import SpeechRecognitionIU
from retico_core.dialogue import GenericDictIU
from smolagents import  CodeAgent, DuckDuckGoSearchTool
from smolagents.models import OpenAIServerModel
from smolagents.tools import tool



"""
SmolAgents module for Retico framework
"""
class CozmoSmolAgentsModule(abstract.AbstractModule):
    #Define agent
    prompt ="""
            You are a Cozmo robot control agent. Your responsibility is to convert voice commands into executable Cozmo function calls.

            PROCESS:
            1. Parse the voice command to extract:
            - Action (move, turn, lift, etc.)
            - Direction (forward, backward, left, right, etc.)
            - Distance/Amount with units
            - Target object (cube, etc.)

            2. If the command is unclear or missing critical information, ALWAYS ask for clarification using this EXACT pattern:
            - Call say_text() tool with your question
            - Return the result from say_text() as your final answer
            - Do NOT call final_answer() separately
            - Do NOT return None
           

            3. If you have enough information, create a step-by-step execution plan using available Cozmo functions with correct parameters. Add all the step of the plan to the final_answer()

            UNIT CONVERSION RULE:
            - Check each function parameter's expected unit in the tool description
            - If the voice command unit doesn't match the function parameter unit, convert it accordingly
            - Examples: 
            - Voice: "10 cm" → Function expects mm → Convert to 100
            - Voice: "half turn" → Function expects degrees → Convert to 180
            - Voice: "fast" → Function expects speed value → Use appropriate speed number

            4. OUTPUT FORMAT:
            Return ONLY ALL the execution steps in this exact format. DO NOT include explanations, confirmations, or additional text. 
            DO NOT INVENT new functions or combine multiple actions into a single "macro" tool.
            Only use the provided functions (move_head, say_text, etc.) in your answer.
           

            If a command requires multiple steps (e.g., lowering the head and counting), always return a list of allowed tool calls, one for each action.

            5. EXAMPLE:
            - Voice command: "Bring the first cube to the charger"
            - Eecution plan: Find the first cube -> bring it to the charger
            - Output:{
                {
                "decision": "go_to_object",
                "concepts":{
                    "distance": 70mm
                }},
                {
                "decision": "drive_to_charger",
                "concepts":{}
                }
                }


    """
    model = OpenAIServerModel(
        model_id= "deepseek/deepseek-chat-v3-0324:free",
        api_base = "https://openrouter.ai/api/v1",
        api_key="YOUR-API_KEY" # Insert your API key here
        ) 


    # Wrap cozmo function behavior as a tool
    @tool
    def drive_straight(distance_mm: float, speed: int = 50) -> dict:
        """
        Move Cozmo straight forward or backward at specified speed
        
        Args:
            distance_mm: Distance (millimet) to move (e.g., 10.5, 25.0, 100.0)
            speed: Speed in centimeters per second (default: 50.0, range: 10-200)
            direction: "forward" or "backward"
        
        Examples:
            - "move forward 20cm" → distance=20.0, direction="forward"
            - "go back 15cm" → distance=15.0, speed=20.0, direction="backward"
            - "drive straight 50cm fast" → distance=50.0, speed=100.0, direction="forward"
        IMPORTANT: When asking for clarification, call this tool and return its result directly.
        Do NOT call final_answer() after this tool.
        """
        
        
        return {
            "decision": "drive_straight",
            "concepts": {
                "distance_mm": distance_mm, 
                "speed_mmps": speed
                }      
        }


    @tool
    def say_text(text: str) -> dict:
        """
        Make Cozmo speak the given text out loud 
        
        Args:
            text: The text for Cozmo to say (any string)
        
        Examples:
            - "say hello" → text="hello"
            - "tell me you're ready" → text="I'm ready"
            - "say good morning everyone" → text="good morning everyone"
            - "speak the word banana" → text="banana"
        """
        return {
            "decision": "say_text",
            "concepts": {
                "text": str(text).strip()
            }
        }


    @tool
    def turn_in_place(angle: float) -> dict:
        """Turn Cozmo in place
        
        Args:
            angle: Angle in degrees (positive=left/counter-clockwise, negative=right/clockwise)
        
        Returns:
            Dictionary with function name and parameters
        """
        return {
            "decision": "turn_in_place",
            "concepts": {
                "angle_degrees": angle
                }
    }



    @tool
    def move_head(radians: int) -> dict:
        """Tell cozmo to move head
        
        Args:
           radians: radians per second, negative for lower head and positive to lift head
        
        Returns:
            Dictionary with function name and parameters
        """
        
        return {
            "decision": "move_head",
            "concepts": {
                "radians": radians
                }
        }
    

    @tool
    def go_to_object(distance_mm: 70) -> dict:
        """Tell Cozmo to find a cube, and then drive up to it
        
        Args:
            distance_mm: Drive to 70mm away from the cube (much closer and Cozmo
            will likely hit the cube) and then stop
        
        Returns:
            Dictionary with function name 
        """
        return {
            "decision": "go_to_object",
            "concepts": {
                "distance_mm": 70
                }
        }
    
    @tool
    def look_around() -> dict:
        """Make Cozmo look around for a cube. 
        Cozmo looks around, reponse if the cube is found or not
        
        
        Returns:
            Dictionary with function name 
        """
        return {
            "decision": "look_around",
            "concepts": {
                }
        }
    
    @tool
    def drive_to_charger() -> dict:
        """Tell Cozmo to drive to charger
        
        Returns:
            Dictionary with function name 
        """
        return {
            "decision": "drive_to_charger",
            "concepts": {}
        }




    #Initiate agent
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agent = CodeAgent(
            tools = [
                self.drive_straight,
                self.say_text,
                self.turn_in_place,
                self.move_head,
                self.look_around,
                self.go_to_object,
                self.drive_to_charger
                # DuckDuckGoSearchTool()
                ],
            model=self.model,
            instructions = self.prompt,
           
        )
        self.conversation_context = [] # template message
        self.processing = False
        self.lock = threading.Lock()
        self.logger = logging.getLogger(self.name())
    
    
    @staticmethod
    def name() -> str:
        return "CozmoSmolAgents"
    
    @staticmethod
    def description() -> str:
        return "SmolAgents module for processing speech and generating robot commands"
    
    @staticmethod
    def input_ius() -> List[type]:  
        return [SpeechRecognitionIU]
    
    @staticmethod
    def output_iu():
        return GenericDictIU
    
    def process_update(self, update_message) -> abstract.UpdateMessage:
        """Process incoming speech recognition updates"""
        if self.processing:
            return None
            
        # Extract text from committed speech recognition IUs only
        user_text_input = []
        source_iu = None
        
        for iu, update_type in update_message:
            if (update_type == abstract.UpdateType.COMMIT and 
                isinstance(iu, SpeechRecognitionIU)):
                if iu.text and iu.text.strip():
                    user_text_input.append(iu.text.strip())
                    source_iu = iu


        # Process if we have committed text
        if user_text_input and source_iu:
            complete_text = " ".join(user_text_input)
            self.logger.info(f"Processing committed text: '{complete_text}'")
            
            return self.process_iu(source_iu, complete_text)
        
        return None
    
    def process_iu(self, source_iu: SpeechRecognitionIU, user_input: str) -> abstract.UpdateMessage:
        """Process user input with SmolAgent and create update message"""
        with self.lock:
            self.processing = True

            # Build context prompt
            if self.conversation_context:
                recent_context = "\n".join(self.conversation_context[-8:])  # Last 8 exchanges
                context_prompt = f"""Recent conversation:{recent_context}
                                Current user input: {user_input}"""
            else:
                context_prompt = user_input

            # Get agent response
            response = self.agent.run(context_prompt)

            # Update chat history
            self.conversation_context.append(f"User: {user_input}")
            self.conversation_context.append(f"Agent: {response}")

            self.logger.info(f"Agent response: {response}")
            print(f"agent response: {response}")
            
            steps = response if isinstance(response, list) else [response]

        self.processing = False

       # Create update message with cozmo command IUs
        um = abstract.UpdateMessage()
        
        for i, step in enumerate(steps):
            payload = {
                'function': step.get('decision', 'unknown'),
                'parameters': step.get('concepts', {}),
                'step_number': i + 1,
                'tool_result': step
            }

            print(f"payload: {payload}")
            
            # Create new GenericDictIU grounded in the speech recognition
            command_iu = self.create_iu(grounded_in=source_iu)
            command_iu.set_payload(payload)
            
            # Update um
            um.add_iu(command_iu, abstract.UpdateType.ADD)
            um.add_iu(command_iu, abstract.UpdateType.COMMIT)
        return um
        

    def setup(self) -> None:
        """Initialize the module"""
        super().setup()
        self.logger.info("CozmoSmolAgents module ready")
    
    def shutdown(self) -> None:
        """Shutdown the module"""
        super().shutdown()
        self.processing = False
        self.logger.info("CozmoSmolAgents module shutdown")


