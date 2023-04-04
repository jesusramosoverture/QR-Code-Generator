################################################################################
# Author: Jesus Ramos Membrive
# E-Mail: ramos.membrive@gmail.com
################################################################################
import contextlib
import json
import sys
import traceback

import qrcode
from PIL.ImageQt import ImageQt
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QMainWindow, QApplication, QMessageBox, QWidget, QLabel
from PyQt6.QtWidgets import QFileDialog
from PIL import Image
from QRCode_Raw_GUI import Ui_MainWindow
import qimage2ndarray
from PyQt6 import uic
from PyQt6.QtWidgets import QFileDialog
from PIL import Image


# Ui_MainWindow, _ = uic.loadUiType("modules\\UI_RAW\\QRCode.ui")

class ResizableQLabel(QLabel):
    resized = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def resizeEvent(self, event):
        """

        :param event:
        :return:
        """
        super().resizeEvent(event)
        self.resized.emit()


class MainWindow(QMainWindow):
    """
    The QMainWindow class provides a main application window.
    Before displaying the screen a basic configuration takes place
    and the module that connects the button signals to the corresponding slots is loaded.
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.qr_label = ResizableQLabel()
        self.ui.gridLayout_qrCode.addWidget(self.qr_label)

        # WIDGET CONFIGURATION
        self.data = {
            "key": "value",
            "numbers": [1, 2, 3],
            "nested": {
                "a": "b",
                "c": "d"
            }
        }
        self.json_string = json.dumps(self.data, indent=4)
        self.ui.textEdit_JSON.setStyleSheet("font: 57 14pt Gotham")
        self.ui.textEdit_JSON.append(self.json_string)

        # CLOSE -> Initial condition
        self.isDirectlyClose = False

        # SIGNALS AND SLOTS
        self.ui.textEdit_JSON.textChanged.connect(self.QR_generator_routine)
        self.ui.plainTextEdit_string.textChanged.connect(self.QR_generator_routine)
        self.ui.tabWidget.currentChanged.connect(self.QR_generator_routine)
        self.ui.pushButton_export.clicked.connect(self.export_image)
        self.qr_label.resized.connect(self._handler_size_window)

        # MAIN WINDOW SHOW
        self.QR_generator_routine()
        self.show()

    # --------------------------------------------------------
    # EVENT-> TO CLOSE THE WINDOW
    # --------------------------------------------------------

    def close(self) -> None:
        """
        Closes the current widget and deletes all its child widgets and global variables.

        :return: None
        """
        for childQWidget in self.findChildren(QWidget):
            QWidget(childQWidget).close()
        self.isDirectlyClose = True
        for name in dir():
            if not name.startswith('_'):
                del globals()[name]
        return super().close()

    def closeEvent(self, eventQCloseEvent) -> None:
        """
        Close the windows and terminate all the connections before close.

        :return:
        """
        if self.isDirectlyClose:
            eventQCloseEvent.accept()
        else:
            answer = QMessageBox.question(
                self,
                'Close the program?',
                'Are you sure?',
                QMessageBox.StandardButton.Yes,
                QMessageBox.StandardButton.No)
            if (answer == QMessageBox.StandardButton.Yes) or (self.isDirectlyClose is True):
                eventQCloseEvent.accept()
                sys.exit(0)
            else:
                eventQCloseEvent.ignore()

    def QR_generator_routine(self) -> None:
        """
        Generates a QR code based on the current tab's input data.

        :return: None
        """
        match self.ui.tabWidget.currentIndex():
            case 0:
                self._format_json_text()
                if self.__check_JSON_is_well_formed() is True:
                    self.ui.label_JSON_state.setText("JSON valid")
                    qr_image = MainWindow.generate_qr_code(self.ui.textEdit_JSON.toPlainText())
                    self.qr_label.setPixmap(qr_image)
                else:
                    self._handler_a_bad_JSON()
            case 1:
                qr_image = MainWindow.generate_qr_code(self.ui.plainTextEdit_string.toPlainText())
                self.qr_label.setPixmap(qr_image)

    def _format_json_text(self) -> None:
        """
        Formats the JSON input text in the text edit box.

        :return: None
        """
        with contextlib.suppress(json.JSONDecodeError):
            text = self.ui.textEdit_JSON.toPlainText()
            json_data = json.loads(text)
            formatted_json = json.dumps(json_data, indent=4)
            if text != formatted_json:
                cursor_position = self.ui.textEdit_JSON.textCursor().position()
                self.ui.textEdit_JSON.setPlainText(formatted_json)
                cursor = self.ui.textEdit_JSON.textCursor()
                cursor.setPosition(cursor_position)
                self.ui.textEdit_JSON.setTextCursor(cursor)

    def _handler_size_window(self) -> None:
        """
        Resizes the main window if the QR code label is larger than the group box.

        :return: None
        """
        if self.ui.groupBox_QRCode.size().height() < self.qr_label.size().height() or \
                self.ui.groupBox_QRCode.size().width() < self.qr_label.size().width():
            self.ui.centralwidget.setMinimumSize(self.qr_label.width() + 40, self.qr_label.height() + 40)
            self.adjustSize()

    def __check_JSON_is_well_formed(self) -> bool:
        """
        Checks if the JSON input in the text edit box is well-formed.

        :return: True if the JSON input is well-formed, False otherwise.
        """
        try:
            json.loads(self.ui.textEdit_JSON.toPlainText())
            return True
        except json.JSONDecodeError:
            return False

    def _handler_a_bad_JSON(self):
        """
        Handles a bad JSON input in the text edit box.

        :return: None
        """
        self.ui.label_JSON_state.setText("JSON invalid")
        self.qr_label.setText("Cannot generate a QR with a invalid JSON.")

    @staticmethod
    def text_to_JSON_format(string_to_JSON: object) -> str:
        """
        Converts a string to a JSON formatted string.

        :param string_to_JSON: The string to convert to JSON format.
        :return: The string in JSON format.
        """
        return json.dumps(string_to_JSON, indent=4)

    @staticmethod
    def generate_qr_code(data: str | dict) -> QPixmap:
        """
        Generates a QR code image based on the given data.

        :param data: The data to encode in the QR code. Can be a string or a dictionary.
        :return: A QPixmap object representing the generated QR code image.
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=8,
            border=4,
        )
        qr.add_data(str(data))
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        image = ImageQt(img)
        q_image = QImage(image)
        return QPixmap.fromImage(q_image)

    def export_image(self) -> None:
        """
        Exports the QR code image as a file.

        :return: None
        """
        with contextlib.suppress(Exception):
            qimage = self.qr_label.pixmap().toImage()
            pil_image = Image.fromarray(qimage2ndarray.rgb_view(qimage))
            file_name, _ = QFileDialog.getSaveFileName(self, "Save Image", "",
                                                       "Images (*.png *.xpm *.jpg *.bmp);;All Files (*)")
            if file_name:
                pil_image.save(file_name)


if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        MainWindow = MainWindow()
        ui = Ui_MainWindow()
        MainWindow.show()
        sys.exit(app.exec())
    except OSError:
        print(f"Error produced in the init: {traceback.format_exc()}")
