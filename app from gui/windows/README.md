# PyQt GUI Application (Windows)

## Overview
This project is a PyQt-based GUI application that can be packaged into a standalone executable for Windows using **PyInstaller**. The executable will have a custom icon and a user-friendly interface.

## Installation
### Prerequisites
Make sure you have **Python** installed. You can download it from [python.org](https://www.python.org/). Also, ensure that `pip` is installed and up-to-date:
```bash
python -m ensurepip --default-pip
python -m pip install --upgrade pip
```

### Install Dependencies
Before running the application, install **PyQt** and **PyInstaller**:
```bash
pip install PyQt5 PyInstaller
```

## Running the Application
To run the PyQt application, execute the following command:
```bash
python qttest.py
```

## Creating an Executable
To create a standalone Windows executable, run the following command:
```bash
python -m PyInstaller --onefile --windowed --icon=favicon.ico qttest.py
```

### Explanation:
- `--onefile`: Generates a single executable file.
- `--windowed`: Runs the application without a terminal window.
- `--icon=favicon.ico`: Sets the icon for the executable (replace `icon.ico` with your actual icon file).

## Icon Setup
To set a custom icon, use an **ICO** file. If you don't have one, you can convert an image to ICO using:
- [https://www.icoconverter.com/](https://www.icoconverter.com/)
- [https://convertico.com/](https://convertico.com/)

Place `favicon.ico` in the same directory as `qtttest.py` before running the PyInstaller command.

## Output
After running PyInstaller, the executable will be available in the `dist/` folder:
```bash
/dist/qttest.exe
```
You can now distribute `qttest.exe` as a standalone application!

## Troubleshooting
- If `pyinstaller` is not recognized, ensure you have installed it using:
  ```bash
  pip install pyinstaller
  ```
- If the application does not start after packaging, try running it in the terminal to check for errors:
  ```bash
  dist/qttest.exe
  ```

## License
This project is licensed under the **MIT License**.

