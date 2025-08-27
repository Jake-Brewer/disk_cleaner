# System Architecture & Design

## High-Level System Architecture

```mermaid
graph TB
    subgraph "User Interface Layer"
        CLI[CLI Entry Point]
        TUI[Terminal UI]
        Progress[Progress Display]
    end

    subgraph "Application Layer"
        Config[Configuration Manager]
        Perf[Performance Manager]
        Safety[Safety Manager]
    end

    subgraph "Core Processing Layer"
        Scanner[File System Scanner]
        Duplicate[Duplicate Detector]
        Classifier[File Classifier]
        Suggestions[Suggestions Engine]
    end

    subgraph "Data Layer"
        DB[(SQLite Database)]
        Cache[(Results Cache)]
    end

    subgraph "System Integration Layer"
        FS[File System APIs]
        WinAPI[Windows APIs]
        ThreadPool[Thread Pool Manager]
    end

    CLI --> Config
    CLI --> Perf
    Config --> Scanner
    Perf --> Scanner
    Perf --> ThreadPool
    Scanner --> Duplicate
    Scanner --> Classifier
    Duplicate --> Suggestions
    Classifier --> Suggestions
    Suggestions --> Safety
    Safety --> TUI
    Suggestions --> DB
    DB --> Scanner
    ThreadPool --> Duplicate
    ThreadPool --> Classifier
    FS --> Scanner
    WinAPI --> Safety
```

## Data Flow Architecture

```mermaid
flowchart TD
    A[Configuration Loaded] --> B[Scan Paths Determined]
    B --> C[File System Traversal]
    C --> D{File Found}
    D -->|Yes| E[Collect Metadata]
    D -->|No| F{Traversal Complete?}
    F -->|No| C
    F -->|Yes| G[Metadata Analysis]
    G --> H[Duplicate Detection]
    G --> I[File Classification]
    H --> J[Generate Duplicate Suggestions]
    I --> K[Generate Cleanup Suggestions]
    J --> L[Combine All Suggestions]
    K --> L
    L --> M[Apply Safety Rules]
    M --> N[Present to User]
    N --> O{User Decision}
    O -->|Accept| P[Execute Actions]
    O -->|Modify| Q[Adjust Suggestions]
    Q --> N
    P --> R[Update Database]
    R --> S[Generate Report]
```

## Component Interaction Patterns

### Observer Pattern for Progress Updates
```mermaid
classDiagram
    class ProgressObserver {
        +update(progress: ProgressData)
    }

    class FileScanner {
        -observers: List<ProgressObserver>
        +attach(observer: ProgressObserver)
        +detach(observer: ProgressObserver)
        +notify()
    }

    class DuplicateDetector {
        -observers: List<ProgressObserver>
    }

    class TerminalUI {
        +update(progress: ProgressData)
    }

    ProgressObserver <|.. TerminalUI
    FileScanner --> ProgressObserver : notifies
    DuplicateDetector --> ProgressObserver : notifies
```

### Strategy Pattern for File Classification
```mermaid
classDiagram
    class FileClassifier {
        +classify(file: FileInfo): ClassificationResult
    }

    class ClassificationStrategy {
        <<interface>>
        +classify(file: FileInfo): ClassificationResult
    }

    class TempFileStrategy {
        +classify(file: FileInfo): ClassificationResult
    }

    class DevArtifactStrategy {
        +classify(file: FileInfo): ClassificationResult
    }

    class LargeFileStrategy {
        +classify(file: FileInfo): ClassificationResult
    }

    FileClassifier --> ClassificationStrategy
    ClassificationStrategy <|.. TempFileStrategy
    ClassificationStrategy <|.. DevArtifactStrategy
    ClassificationStrategy <|.. LargeFileStrategy
```

## Database Schema Design

```mermaid
erDiagram
    SCAN_SESSIONS {
        id INTEGER PK
        timestamp DATETIME
        scan_path TEXT
        total_files INTEGER
        total_size_bytes INTEGER
        duration_seconds REAL
        status TEXT
    }

    FILES {
        id INTEGER PK
        scan_session_id INTEGER FK
        file_path TEXT
        file_size_bytes INTEGER
        modified_time DATETIME
        file_hash TEXT
        classification TEXT
        suggested_action TEXT
        action_taken TEXT
    }

    DUPLICATE_GROUPS {
        id INTEGER PK
        group_hash TEXT
        file_count INTEGER
        total_size_bytes INTEGER
        recommended_keep_file_id INTEGER FK
    }

    DUPLICATE_GROUP_FILES {
        duplicate_group_id INTEGER FK
        file_id INTEGER FK
        PK(duplicate_group_id, file_id)
    }

    SUGGESTIONS {
        id INTEGER PK
        file_id INTEGER FK
        suggestion_type TEXT
        description TEXT
        potential_savings_bytes INTEGER
        confidence_score REAL
    }

    SCAN_SESSIONS ||--o{ FILES : contains
    SCAN_SESSIONS ||--o{ DUPLICATE_GROUPS : generates
    FILES ||--o{ DUPLICATE_GROUP_FILES : belongs_to
    DUPLICATE_GROUPS ||--o{ DUPLICATE_GROUP_FILES : contains
    FILES ||--o{ SUGGESTIONS : has
    DUPLICATE_GROUPS }o--|| FILES : recommends_keeping
```

## Thread Pool Management Design

```mermaid
stateDiagram-v2
    [*] --> Initialized
    Initialized --> AssessingResources
    AssessingResources --> BackgroundMode: CPU cores <= 2
    AssessingResources --> ForegroundMode: CPU cores > 2
    BackgroundMode --> MonitoringResources
    ForegroundMode --> MonitoringResources
    MonitoringResources --> ReducingThreads: High resource usage
    ReducingThreads --> MonitoringResources
    MonitoringResources --> IncreasingThreads: Low resource usage
    IncreasingThreads --> MonitoringResources
    MonitoringResources --> [*]: Scan complete
    note right of BackgroundMode
        Max 2 threads
        Low priority
        I/O throttling
    end note
    note right of ForegroundMode
        50-100% CPU cores
        Normal priority
        Full I/O speed
    end note
```

## Error Handling Architecture

```mermaid
flowchart TD
    A[Operation Request] --> B{Operation Type}
    B -->|File Operation| C[File System Check]
    B -->|Database Operation| D[Database Check]
    B -->|Network Operation| E[Network Check]
    C --> F{Error Occurred?}
    D --> G{Error Occurred?}
    E --> H{Error Occurred?}
    F -->|Yes| I[Log Error]
    G -->|Yes| I
    H -->|Yes| I
    F -->|No| J[Execute Operation]
    G -->|No| J
    H -->|No| J
    I --> K{Recoverable?}
    K -->|Yes| L[Attempt Recovery]
    K -->|No| M[Graceful Degradation]
    L --> N{Success?}
    N -->|Yes| J
    N -->|No| M
    M --> O[Continue with Reduced Functionality]
    J --> P[Operation Complete]
    O --> P
```

## Security Considerations

### Data Protection
- **No External Network Access**: All operations are local to the system
- **File Content Isolation**: File hashes only, never stores actual file contents
- **Configuration Security**: Sensitive paths excluded from logs and reports
- **Temporary File Cleanup**: Automatic cleanup of temporary files and caches

### Access Control
- **File System Permissions**: Respect Windows file system permissions
- **User Context**: Operations run in user context, no privilege escalation
- **Audit Trail**: All operations logged with timestamps and file paths

### Error Handling Security
- **Information Disclosure**: Error messages don't expose sensitive file paths
- **Resource Exhaustion**: Limits on memory usage and thread counts
- **Input Validation**: All file paths and configuration values validated

## Performance Characteristics

### Expected Performance Metrics
- **File Discovery**: ~10,000 files/second on SSD
- **Hash Calculation**: ~50MB/second (MD5), ~25MB/second (SHA256)
- **Memory Usage**: <1GB for typical scans (<500K files)
- **Database Operations**: <100ms per 1K file operations
- **UI Responsiveness**: Progress updates every 100ms

### Scalability Considerations
- **Large File Systems**: Incremental scanning with database caching
- **Memory Constraints**: Streaming processing for very large file sets
- **CPU Optimization**: Parallel processing with thread pool optimization
- **I/O Optimization**: Asynchronous I/O for better disk utilization

## Deployment Architecture

```mermaid
graph TB
    subgraph "Source Control"
        Git[Git Repository]
    end

    subgraph "Build Process"
        Poetry[Poetry Build]
        Tests[Run Tests]
        Lint[Code Quality Checks]
    end

    subgraph "Packaging"
        Wheel[Python Wheel]
        Exe[Standalone Executable]
    end

    subgraph "Distribution"
        PyPI[PyPI Package]
        GitHub[GitHub Releases]
    end

    Git --> Poetry
    Poetry --> Tests
    Tests --> Lint
    Lint --> Wheel
    Wheel --> Exe
    Wheel --> PyPI
    Exe --> GitHub
```
