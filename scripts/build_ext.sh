rm -r build dist
python3 setup.py build
cp -R build/lib*/ .
