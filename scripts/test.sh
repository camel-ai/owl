#!/bin/bash
echo "Running smoke test..."
# Try to import the main 'owl' module. If it fails, the application is likely broken.
python -c "import owl"
if [ $? -eq 0 ]; then
  echo "Smoke test passed: Basic import of 'owl' module was successful."
  exit 0
else
  echo "Smoke test FAILED: Could not import the 'owl' module."
  exit 1
fi
