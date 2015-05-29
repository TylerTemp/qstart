# QStart

A simple windows keyboard logger that helps your open a file/run a command
with three hotkeys.

## Download & Install

1. Click the `Download ZIP` button on the right
2. Unzip the `qstart.zip`
3. Double click the `run.vbs`

## Usage

When started the application:

1. Click the button beside `Primary Key`
2. When `Catch a Hotkey` window popup, enter a hotkey and click `OK`
3. The same way to set the `Secondary Key` as secondary hotkey
4. Click the `...` button
5. The same way to set the `Hotkey`
6. Set `Name` as an alias
7. Select a file you want to open or input a command below
8. Click `OK`

Then you could open the file/run the command you set by pressing `Primary Key`
\+ `Secondary Key` + `Hotkey` on you keyboard

_Note_: You may get a `Open File - Security Warning`. This is not a issue that
I can solve. Sorry for that.

## Develop

1. ```bash
git clone https://github.com/TylerTemp/qstart.git
```
2. copy `dist/src` folder to the root folder of the project
3. install python3 or python2.7+ at <http://python.org>
4. install wxpython_phoenix:
   ```bash
   pip install -U --pre -f http://wxpython.org/Phoenix/snapshot-builds/ wxPython_Phoenix --trusted-host wxpython.org
   ```
   if you use python2 and prefer classic wxpython you can get it from: <http://www.wxpython.org/download.php>
5. install pywin32 lib. Get it from <http://sourceforge.net/projects/pywin32/files/pywin32/Build%20219/>. Note that you need to choose one that fit your system & your python version.
6. pyHook.
   for python2: First you need to install wheel:
   ```bash
   pip install wheel
   ```
   Then Downland a `.whl` from <http://www.lfd.uci.edu/~gohlke/pythonlibs/#pyhook> and install by
   ```bash
   pip install path/to/file.whl
   ```
   for python3 please check here: <https://github.com/Answeror/pyhook_py3k.git>

for compiling to exe you can install pyinstaller

```bash
pip install pyinstaller
```

and compile it by

```bash
pyinstaller --onefile --windowed --icon=src\img\exe.ico -F run.py
```

and copy `dist\run.exe` to root dir

```bash
copy dist\run.exe .\
```
