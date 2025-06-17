
import sys
import os


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from run_profile_generation import app
    print("Starting Profile Generation Web Server...")
    print("Open your browser and go to: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    
    app.run(debug=False, host='0.0.0.0', port=5000)