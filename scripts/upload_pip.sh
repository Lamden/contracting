if [ "$CIRCLE_BRANCH" == "dev" ]
then
  sudo python3 setup.py build_ext -i
  sudo python3 setup.py sdist bdist_wheel
  echo "Uploading using twine via user $PYPI_USERNAME ..."
  twine upload -u $PYPI_USERNAME -p $PYPI_PASSWORD dist/*
fi
