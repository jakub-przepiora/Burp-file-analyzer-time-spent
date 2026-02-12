# Burp Project Time Analyzer

A Python script that estimates time spent on penetration testing projects by analyzing request timestamps from Burp Suite project files.

## Features

- Extracts timestamps from Burp Suite `.burp` project files
- Groups requests into work sessions based on configurable inactivity gaps
- Handles large files (10GB+) efficiently using chunk sampling
- Provides detailed breakdown by session and day
- Estimates total working hours

## Requirements

- Python 3.6+
- Linux/Unix environment (uses `dd`, `strings`, `grep`)

## Installation

```bash
git clone https://github.com/yourusername/burp-time-analyzer.git
cd burp-time-analyzer
chmod +x burp_time_analyzer.py
```

## Usage

```bash
python3 burp_time_analyzer.py <file.burp> [gap_minutes]
```

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `file.burp` | Path to Burp Suite project file | Required |
| `gap_minutes` | Minutes of inactivity to start new session | 30 |

### Examples

```bash
# Basic usage with 30-minute session gap
python3 burp_time_analyzer.py project.burp

# Custom 20-minute session gap
python3 burp_time_analyzer.py project.burp 20

# No session splits (count as single continuous session)
python3 burp_time_analyzer.py project.burp 99999
```

## Sample Output

```
============================================================
  TIME ANALYSIS - BURP PROJECT
  2026-02-01-dell.burp
============================================================

[*] Extracting timestamps...
    File size: 9.25 GB
    Analyzing 20 file sections...

[+] Found 1813 unique timestamps

[*] TIME RANGE:
    First request: 2026-02-02 03:42:18
    Last request:  2026-02-11 16:47:05
    Total range:   229h 4m

[*] WORK SESSIONS (gap > 30 min = new session):
    Number of sessions: 35

    No   Date         Start    End      Duration   Req.
    ------------------------------------------------------
    1    2026-02-02   03:42    03:42    5m 0s      1
    2    2026-02-02   10:58    10:58    5m 0s      1
    ...

============================================================
  SUMMARY
============================================================

    Total work time:       6h 29m
    Number of sessions:    35
    Average session time:  11m 7s
    Total requests:        1813

[*] WORK TIME PER DAY:
    Date         Time         Sessions Requests
    ------------------------------------------
    2026-02-02   15m 0s       3        3
    2026-02-03   1h 14m       9        37
    2026-02-04   1h 30m       6        393
    ...

    === ESTIMATED TIME: ~6.5 hours (10 working days) ===
```

## How It Works

1. **Timestamp Extraction**: Scans the Burp project file for 13-digit Unix timestamps (milliseconds)
2. **Session Grouping**: Groups timestamps into sessions based on the inactivity gap threshold
3. **Time Calculation**: Calculates duration for each session (minimum 5 minutes per session)
4. **Aggregation**: Summarizes time by day and provides total estimates

## Limitations

- For large files (>500MB), the script samples data at intervals rather than scanning the entire file
- Timestamps are extracted using pattern matching, which may miss some requests
- Time estimates are approximate and based on request activity, not actual screen time

## Use Cases

- Bug bounty time tracking
- Penetration testing project reporting
- Estimating effort for client billing
- Personal productivity analysis

## License

MIT License

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
