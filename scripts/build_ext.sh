rm -r build dist
python3 setup.py build_ext -i
cp -R build/lib*/ .
