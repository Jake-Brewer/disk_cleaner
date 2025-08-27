# Disk Cleaner Requirements Analysis

## Overview
A Python-based disk cleaning utility for Windows systems that focuses on the C: drive user data. The tool will analyze disk usage, identify opportunities for cleanup, and provide intelligent suggestions while maintaining system performance and user control.

## Core Requirements

### 1. File System Analysis
- **Target Scope**: Initially focus on user directories (Documents, Downloads, Desktop, AppData, etc.)
- **Exclusion Rules**: Avoid system-critical directories (Windows/, Program Files/, System32/)
- **Depth Control**: Configurable scan depth with default reasonable limits
- **File Types**: Support all file types with special handling for large media files

### 2. Duplicate File Detection
- **Detection Method**: Content-based hashing (MD5 for speed, SHA256 for accuracy)
- **Performance Optimization**:
  - Size pre-filtering (only hash files >1KB)
  - Chunked reading for large files (>100MB)
  - Parallel processing of hash calculations
- **Similarity Thresholds**: Exact duplicates only (no fuzzy matching)
- **Performance Targets**: <5 seconds per GB of data scanned
- **Suggestions**: Intelligent recommendations with clear reasoning:
  - Keep file with longest path (likely more organized)
  - Keep newest modification time
  - Keep file in user directory over temp/cache locations
- **Safety**: Never auto-delete; always require explicit user confirmation with detailed preview

### 3. File Classification & Suggestions
- **Temporary Files**: Identify and suggest removal of:
  - Browser cache/temp files (Chrome, Firefox, Edge)
  - Windows temp directories (`%TEMP%`, `%TMP%`, prefetch files)
  - Application-specific temp data (old installer files, crash dumps)
  - Log files older than 30 days
- **Relocatable Files**: Suggest moving large files to other drives:
  - Media files >500MB (videos, photos, music)
  - Archives >100MB (.zip, .rar, .7z)
  - Virtual machine disks (.vhd, .vhdx)
  - Database files (.db, .sqlite)
- **Development Artifacts**: Detect and suggest cleanup of:
  - `node_modules` directories >50MB
  - Python virtual environments (`venv/`, `env/`, `.venv/`)
  - Build artifacts (`dist/`, `build/`, `.eggs/`)
  - IDE/editor cache directories (`.vscode/`, `.idea/`, `.vs/`)

### 4. Performance & Resource Management
- **Threading Model**:
  - Dynamic thread pool: 1-8 threads based on CPU cores and available memory
  - Background mode: Maximum 2 threads, low priority (ProcessPriorityClass.BelowNormal)
  - Foreground mode: 50-100% of available CPU cores
- **Resource Monitoring**: Track and limit:
  - CPU usage <80% in background mode, unlimited in foreground
  - Memory usage <1GB per scan session
  - Disk I/O throttling in background mode
- **Adaptive Performance**: Automatically reduce thread count if system becomes unresponsive
- **Cancellation**: Graceful shutdown with cleanup of partial operations

### 5. User Interface
- **Configuration Management**: YAML/JSON config file for:
  - Scan paths and exclusions
  - Size thresholds for different file categories
  - Thread pool settings
  - UI preferences (colors, verbosity)
- **Progress Display**:
  - Real-time progress bars with file count and size processed
  - ETA calculations based on current scan rate
  - Current operation status with file path
- **Interactive Mode**: Allow users to:
  - Review suggestions before execution
  - Select/deselect specific actions
  - Preview file details before decisions
- **Batch Mode**: Non-interactive mode for automation scripts
- **Logging**: Structured logging with configurable levels

### 6. Safety & Reliability
- **Dry Run Mode**: Complete analysis without making changes
- **Data Persistence**: Store scan results in local SQLite database for:
  - Historical comparisons
  - Incremental scans (only scan changed files)
  - Undo functionality for recent operations
- **Error Handling**:
  - Continue scanning on individual file errors (permission denied, corrupted files)
  - Detailed error reporting with suggested remediation
  - Automatic retry for transient failures
- **Backup Integration**: Optional integration with Windows File History and System Restore

### 7. Windows-Specific Features
- **Shell Integration**: Context menu options for directories
- **Recycle Bin Integration**: Move deleted files to Recycle Bin instead of permanent deletion
- **Volume Shadow Copy**: Leverage VSS for safe scanning of locked files
- **NTFS Features**: Utilize hard link detection, file compression awareness
- **Power Management**: Respect system power plans and battery status

## Technical Constraints
- **Platform**: Windows-specific initially (leverage Windows APIs where beneficial)
- **Python Version**: ^3.9 (support modern async/concurrency features)
- **Dependencies**: Minimize external dependencies, prefer stdlib where possible
- **Security**: No network access, read-only operations by default

## Success Criteria
- **Performance**: Complete full C: drive scan in reasonable time (< 30 min on typical systems)
- **Accuracy**: >95% accuracy in duplicate detection and file classification
- **Safety**: Zero data loss in normal operation scenarios
- **Usability**: Intuitive interface suitable for both technical and non-technical users

## Open Source Package Analysis

### Trustworthy Packages Identified
1. **psutil** (Already included)
   - Cross-platform system and process utilities
   - CPU/memory/disk monitoring
   - Process management
   - Highly maintained, used by major projects

2. **rich** (Already included)
   - Rich text and beautiful formatting in terminal
   - Progress bars, tables, trees
   - Actively maintained by Textualize

3. **concurrent.futures** (Stdlib)
   - Thread/process pool management
   - Futures-based concurrency
   - Built-in, no additional dependencies

4. **pathlib** (Stdlib)
   - Object-oriented filesystem paths
   - Cross-platform compatibility
   - Modern Python stdlib

5. **hashlib** (Stdlib)
   - Cryptographic hashing (MD5, SHA256)
   - Fast file content comparison
   - Built-in security

### Package Evaluation Criteria
- **Trustworthiness**: Active maintenance, security audits, large user base
- **Relevance**: Direct applicability to disk cleaning functionality
- **Minimal Dependencies**: Avoid packages with extensive dependency trees
- **Performance**: Efficient resource usage
- **Documentation**: Well-documented APIs

### Recommended Additional Packages
None identified at this stage. Current dependencies cover all major needs while maintaining minimal attack surface and dependency complexity.
