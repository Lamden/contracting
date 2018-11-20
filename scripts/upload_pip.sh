if [ "$CIRCLE_BRANCH" == "dev" ] || [ "$CIRCLE_BRANCH" == "master" ]
then
  sudo -E python3 setup.py build_ext -i
  sudo -E python3 setup.py sdist bdist_wheel
  echo "Uploading using twine via user $PYPI_USERNAME ..."
  sudo rename 's/linux_x86_64.whl/macosx_10_9_x86_64.whl/' dist/*
  twine upload -u "$PYPI_USERNAME" -p "$PYPI_PASSWORD" dist/*
fi
