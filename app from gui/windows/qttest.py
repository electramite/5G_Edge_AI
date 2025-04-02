from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QIcon
import sys

class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clickable PyQt App")
        self.setGeometry(100, 100, 400, 300)  # Set window size
        self.setWindowIcon(QIcon("logo.png"))  # Set app icon (replace with your file)

app = QApplication(sys.argv)
window = MyApp()
window.show()
sys.exit(app.exec_())
