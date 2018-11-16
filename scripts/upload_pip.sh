if [ "$CIRCLE_BRANCH" == "dev" ]
then
  python3 setup.py build
  python3 setup.py sdist bdist_wheel
  twine upload -u $PYPI_USERNAME -p $PYPI_PASSWORD dist/*
fi
