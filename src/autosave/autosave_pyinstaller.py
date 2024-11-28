import os
import shutil

import PyInstaller.__main__

dir_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

print(dir_path)

PyInstaller.__main__.run(
    [
        'autosave.py',
        '--onefile',
        '--windowed',
        '--console',
        '-y'
    ]
)
shutil.move(
    src=os.path.join(dir_path, "src\\autosave\\dist\\autosave.exe"),
    dst=os.path.join(dir_path, 'autosave.exe')
)

PyInstaller.__main__.run(
    [
        'start_hidden.py',
        '--onefile',
        '--windowed',
        '--console',
        '-y'
    ]
)

shutil.move(
    src=os.path.join(dir_path, "src\\autosave\\dist\\start_hidden.exe"),
    dst=os.path.join(dir_path, 'start_hidden.exe')
)
