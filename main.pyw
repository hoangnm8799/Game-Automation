"""
main.pyw

Same app as main.py - the only difference is the .pyw extension, which on
Windows is associated with pythonw.exe instead of python.exe, so
double-clicking this launches with NO console window alongside it.

Use main.py (`python main.py` from a terminal) instead while debugging -
main.pyw has no console, so if something raises an exception here you
won't see any traceback, just the window disappearing.
"""

from main import run

if __name__ == "__main__":
    run()
