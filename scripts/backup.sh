#!/bin/bash
echo "Starting backup..."
# Remove old backup if it exists
if [ -d "backup" ]; then
  echo "Removing old backup directory..."
  rm -rf backup
fi
# Create a new backup directory
mkdir -p backup/owl
mkdir -p backup/examples
mkdir -p backup/scripts
# Copy key directories to the backup
echo "Copying key directories (owl, examples, scripts) to backup/..."
cp -r owl/* backup/owl/
cp -r examples/* backup/examples/
cp -r scripts/* backup/scripts/
echo "Backup completed successfully."
