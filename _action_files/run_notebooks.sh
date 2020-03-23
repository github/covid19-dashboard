#!/bin/sh
set -e
cd $(dirname "$0")/..

ERRORS=""

for file in _notebooks/*.ipynb
do
    if papermill --kernel "${file}" "${file}"; then
        git add "${file}"
    else
        ERRORS="${ERRORS}\n${file}"
done

# Emit Errors If Exists So Downstream Task Can Open An Issue
if [ -z "$ERRORS" ]
then
    echo "::set-output name=error_bool::true"
     echo "::set-output name=error_str::${ERRORS}"
else
    echo "::set-output name=error_bool::false"
fi
