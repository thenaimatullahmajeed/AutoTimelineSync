"""Review candidate only. Does not install or replace the existing application."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','windows')
from bootstrap import install
install(ui=True)
from ats_studio.__main__ import main
if __name__=='__main__':main()

