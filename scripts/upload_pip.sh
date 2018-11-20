if [ "$CIRCLE_BRANCH" == "dev" ] || [ "$CIRCLE_BRANCH" == "master" ]
then
  sudo -E python3 setup.py build_ext -i
  sudo -E python3 setup.py sdist
  echo "Uploading using twine via user $PYPI_USERNAME ..."
  twine upload -u "$PYPI_USERNAME" -p "$PYPI_PASSWORD" dist/*
fi
