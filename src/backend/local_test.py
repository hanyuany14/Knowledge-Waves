"""This module is used to run the backend locally for testing purposes.
And need to be ignored in the github.
"""

from datetime import datetime

from main import Main

if __name__ == "__main__":

    main = Main()
    print("Start preparing news...")
    main.prepare_news()
    print("Done!")
