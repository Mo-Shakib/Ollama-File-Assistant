import asyncio
import logging
from desktop_agent import DesktopAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO, # Keep this at INFO to ensure file logging captures INFO messages
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('main.log'), # Add a file handler for main.py logs
        logging.StreamHandler() # This is the console handler
    ]
)
logger = logging.getLogger(__name__)

# Set the console handler's level to WARNING or ERROR
for handler in logging.getLogger().handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.setLevel(logging.WARNING) # Changed to WARNING to suppress INFO messages 

# Set the console handler's level back to INFO to show actions
for handler in logging.getLogger().handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.setLevel(logging.INFO) # Set to INFO to show action messages

async def main():
    """Main function to run the desktop agent"""
    print("🤖 Desktop Agent Starting...")
    print("=" * 50)
    
    try:
        # Initialize the agent
        agent = DesktopAgent("/Users/shakib/Desktop/TestFolder")
        print("✅ Agent initialized successfully!")
        print("💡 You can ask me to:")
        print("   - List files and directories")
        print("   - Read file contents")
        print("   - Create files and directories")
        print("   - Move/rename files")
        print("   - Delete files (including 'delete all files')")
        print("   - Get file information")
        print("\n🔧 Available commands:")
        print("   - 'quit' or 'exit' to stop")
        print("   - 'clear' to clear conversation history")
        print("=" * 50)
        
        while True:
            try:
                # Get user input
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if user_input.lower() == 'clear':
                    agent.clear_history()
                    print("🧹 Conversation history cleared!")
                    continue
                
                if not user_input:
                    continue
                
                print("🤖 Agent: Thinking...")
                
                # Process the input
                response = await agent.process_user_input(user_input)
                
                print(f"🤖 Agent: {response}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                print(f"❌ Error: {e}")
    
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        print(f"❌ Failed to start agent: {e}")

if __name__ == "__main__":
    asyncio.run(main())
