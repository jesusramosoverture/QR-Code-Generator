################################################################################
# Author: Embedded Team
# Version: 1.0
# Project: DaVitri
# Overture Life S.L.
################################################################################
from PyQt6 import uic

with open('QRCode6.ui', 'r') as file_in:
    with open('../../QRCode_Raw_GUI.py', 'w') as file_out:
        uic.compileUi(file_in, file_out, execute=True)

if file_out:
    print("Conversion successfully")
else:
    print("Task failed successfully")
