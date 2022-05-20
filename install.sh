echo Feching source code...
curl https://raw.githubusercontent.com/ArthurZhou/D2Lib/main/d2lib.py --output d2lib.py
echo Making libraries...
mkdir d2lib
echo Making example files...
cd d2lib
curl https://raw.githubusercontent.com/ArthurZhou/D2Lib/main/Home.md --output Home.md
curl https://raw.githubusercontent.com/ArthurZhou/D2Lib/main/404.md --output 404.md
cd ..
echo Finish! Use 'python3 d2lib.py' to fire it up!
echo Problems? Check out our Wiki -> https://github.com/ArthurZhou/D2Lib/wiki
