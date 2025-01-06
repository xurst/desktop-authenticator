# main.py
import sys
from ui import run_app
from logic import AuthenticatorLogic
from typing import NoReturn

def main() -> NoReturn:
    try:
        logic = AuthenticatorLogic()
        run_app(logic)

    except ImportError as e:
        print(f"Error: Missing required dependencies. Please ensure PyQt6 is installed.\n{str(e)}")
        print("Install using: pip install PyQt6")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to start application.\n{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()