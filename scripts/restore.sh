#!/bin/bash
echo "Starting restore from backup..."
if [ ! -d "backup" ]; then
  echo "Error: Backup directory not found. Cannot restore."
  exit 1
fi
# Copy the backed-up directories back to their original locations
echo "Copying files from backup/ to root..."
cp -r backup/owl/* owl/
cp -r backup/examples/* examples/
cp -r backup/scripts/* scripts/
echo "Restore completed successfully."
