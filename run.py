#!/usr/bin/env python3
"""
Simple startup script for the Charge Anywhere Country Change Tool
"""

import os
import sys


def check_dependencies():
    """Check if required dependencies are installed"""
    required_modules = ["flask", "requests", "dotenv"]
    missing_modules = []

    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            if module == "dotenv":
                missing_modules.append("python-dotenv")
            else:
                missing_modules.append(module)

    if missing_modules:
        print("Missing required modules:")
        for module in missing_modules:
            print(f"  - {module}")
        print("\nPlease install them using:")
        print("pip install -r requirements.txt")
        return False
    return True


def check_env_file():
    """Check if .env file exists and has required variables"""
    if not os.path.exists(".env"):
        print("Warning: .env file not found!")
        print("Please copy .env.example to .env and fill in your credentials")
        return False

    # Check if required environment variables are set
    required_vars = ["CHANNEL_NAME", "USERNAME", "PASSWORD"]
    with open(".env", "r") as f:
        env_content = f.read()

    for var in required_vars:
        if f"{var}=your_" in env_content or f"{var}=" not in env_content:
            print(f"Warning: {var} may not be properly set in .env file")

    return True


def main():
    """Main startup function"""
    print("Charge Anywhere Country Change Tool")
    print("=" * 40)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Check environment file
    check_env_file()

    print("Starting Flask application...")
    print("Access the application at: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print()

    # Import and run the Flask app
    try:
        from app import app

        app.run(debug=True, host="0.0.0.0", port=5000)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
