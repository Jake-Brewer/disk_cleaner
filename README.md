# Disk Cleaner

A Python utility to analyze and clean up disk space on Windows, focusing on the `C:` drive user data. It identifies duplicate files, temporary files, misplaced items, and large development folders (`node_modules`, `venv`, etc.).

Key features:

- Duplicate file detection with suggested actions
- Identification of files/folders that can be moved or removed
- Cleanup of temp files
- Detection of bulky development artifacts
- Dynamic thread adjustment for optimal performance
- Background / foreground modes to minimize system impact
- Rich terminal UI to show progress

This project follows **Test-Driven Development** using the *Multi-Persona TDD Protocol* provided in the project brief.
