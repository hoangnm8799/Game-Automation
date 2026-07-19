"""
main.py

Entry point WITH a console window - run this (`python main.py`) while
debugging, since exceptions print here. For normal day-to-day use with
no console window, double-click main.pyw instead - same app, same
`run()`, just launched through pythonw instead of python on Windows.
"""

import features  # noqa: F401  (importing triggers registration of all features)
from ui.main_menu import MainMenu


def run() -> None:
    app = MainMenu()
    app.mainloop()


if __name__ == "__main__":
    run()
