#!/usr/bin/env python3
"""
Streamlit App Launcher with Proper Signal Handling

This script launches the Streamlit application with proper signal handling
to ensure immediate termination when Ctrl+C is pressed.
"""

import os
import sys
import signal
import subprocess
import time
from pathlib import Path

class StreamlitLauncher:
    def __init__(self):
        self.streamlit_process = None
        self.running = True
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C signal"""
        print("\n🛑 Stopping application...")
        self.running = False
        
        if self.streamlit_process:
            try:
                # Terminate the Streamlit process
                self.streamlit_process.terminate()
                
                # Wait a moment for graceful shutdown
                try:
                    self.streamlit_process.wait(timeout=3)
                    print("✅ Application stopped gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't stop gracefully
                    print("⚠️ Force stopping application...")
                    self.streamlit_process.kill()
                    self.streamlit_process.wait()
                    print("✅ Application force stopped")
                    
            except Exception as e:
                print(f"❌ Error stopping application: {e}")
        
        sys.exit(0)
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self.signal_handler)  # Ctrl+C
        signal.signal(signal.SIGTERM, self.signal_handler)  # Termination signal
        
        # On Windows, also handle SIGBREAK (Ctrl+Break)
        if sys.platform == "win32":
            signal.signal(signal.SIGBREAK, self.signal_handler)
    
    def launch_streamlit(self):
        """Launch the Streamlit application"""
        # Get the path to the Streamlit app
        app_path = Path(__file__).parent / "app" / "ui" / "app.py"
        
        if not app_path.exists():
            print(f"❌ Error: Streamlit app not found at {app_path}")
            sys.exit(1)
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
        print("🚀 Starting MartinGales Trading Bot...")
        print(f"📁 App location: {app_path}")
        print("💡 Press Ctrl+C to stop the application")
        print("-" * 50)
        
        try:
            # Launch Streamlit as a subprocess
            cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]
            
            # Add Streamlit configuration for better shutdown behavior
            env = os.environ.copy()
            env["STREAMLIT_SERVER_HEADLESS"] = "true"
            env["STREAMLIT_SERVER_ENABLE_CORS"] = "false"
            env["STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION"] = "false"
            
            self.streamlit_process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Monitor the process and output
            while self.running and self.streamlit_process.poll() is None:
                try:
                    # Read output line by line
                    line = self.streamlit_process.stdout.readline()
                    if line:
                        print(line.rstrip())
                    time.sleep(0.1)
                except KeyboardInterrupt:
                    # This should be caught by signal handler, but just in case
                    break
            
            # Check if process ended unexpectedly
            if self.streamlit_process.poll() is not None and self.running:
                return_code = self.streamlit_process.returncode
                if return_code != 0:
                    print(f"❌ Streamlit process ended unexpectedly with code {return_code}")
                    sys.exit(return_code)
                else:
                    print("✅ Streamlit process ended normally")
                    
        except Exception as e:
            print(f"❌ Error launching Streamlit: {e}")
            sys.exit(1)
        finally:
            if self.streamlit_process and self.streamlit_process.poll() is None:
                try:
                    self.streamlit_process.terminate()
                    self.streamlit_process.wait(timeout=3)
                except:
                    try:
                        self.streamlit_process.kill()
                    except:
                        pass

def main():
    """Main entry point"""
    launcher = StreamlitLauncher()
    launcher.launch_streamlit()

if __name__ == "__main__":
    main()