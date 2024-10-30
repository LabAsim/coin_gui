import os
import shutil
import PyInstaller.__main__

dir_path = os.path.dirname(os.path.realpath(__file__))

print(dir_path)

to_move = os.path.join(dir_path, 'multimedia')

PyInstaller.__main__.run(
    [
        'main.py',
        '--onedir',
        '--windowed',
        '--console',
        f'--add-data={dir_path}\\multimedia;multimedia',
        f'--add-data={dir_path}\\src;src',
        '-y'
    ]
)
shutil.copytree(src=to_move, dst=os.path.join(dir_path, 'dist\\main\\multimedia'))
# Manually move azure.tcl to the same dir with the exe.
# '--bootloader-ignore-signals',
# To hide the console, use '--noconsole'
# https://stackoverflow.com/questions/17584698/getting-rid-of-console-output-when-freezing-python-programs-using-pyinstaller
