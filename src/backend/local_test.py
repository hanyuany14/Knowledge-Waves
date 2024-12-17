"""This module is used to run the backend locally for testing purposes.
And need to be ignored in the github.
"""

from src.backend.main import Main

if __name__ == "__main__":
    main = Main()
    main.prepare_news()
    print("Done!")
