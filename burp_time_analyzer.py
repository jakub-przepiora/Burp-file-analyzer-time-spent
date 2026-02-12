#!/usr/bin/env python3
"""
Burp Project Time Analyzer
Analyzes time spent on a project based on request timestamps.
"""

import subprocess
import sys
import os
from datetime import datetime
from collections import defaultdict

def extract_timestamps(burp_file):
    """
    Extracts Unix timestamps from Burp file.
    Searches for 13-digit numbers starting with 177 (2026).
    """
    file_size = os.path.getsize(burp_file)
    print(f"    File size: {file_size / (1024**3):.2f} GB")

    timestamps = set()
    chunk_size = 100 * 1024 * 1024  # 100MB chunks

    # For large files, sample every chunk
    if file_size > 500 * 1024 * 1024:  # > 500MB
        # Sample every 500MB plus start and end
        positions = [0]
        pos = 500 * 1024 * 1024
        while pos < file_size - chunk_size:
            positions.append(pos)
            pos += 500 * 1024 * 1024
        positions.append(max(0, file_size - chunk_size))
        positions = sorted(set(positions))
    else:
        positions = [0]

    print(f"    Analyzing {len(positions)} file sections...")

    for i, pos in enumerate(positions):
        # Use dd + strings + grep for speed
        cmd = f"dd if='{burp_file}' bs=1M skip={pos // (1024*1024)} count={chunk_size // (1024*1024)} 2>/dev/null | strings | grep -oE '177[0-9]{{10}}'"

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )

            for line in result.stdout.strip().split('\n'):
                if line and line.isdigit() and len(line) == 13:
                    timestamps.add(int(line))

        except subprocess.TimeoutExpired:
            print(f"    [!] Timeout at position {pos/(1024**3):.2f}GB")
            continue

    return sorted(timestamps)

def analyze_sessions(timestamps, session_gap_minutes=30):
    """Groups timestamps into sessions."""
    if not timestamps:
        return []

    gap_ms = session_gap_minutes * 60 * 1000
    sessions = []

    current_session = {
        'start': timestamps[0],
        'end': timestamps[0],
        'requests': 1
    }

    for ts in timestamps[1:]:
        if ts - current_session['end'] > gap_ms:
            sessions.append(current_session)
            current_session = {
                'start': ts,
                'end': ts,
                'requests': 1
            }
        else:
            current_session['end'] = ts
            current_session['requests'] += 1

    sessions.append(current_session)
    return sessions

def format_duration(ms):
    """Formats duration from milliseconds."""
    if ms < 0:
        return "0s"
    seconds = ms / 1000
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"

def ms_to_datetime(ms):
    """Converts timestamp ms to datetime."""
    return datetime.fromtimestamp(ms / 1000)

def analyze_burp_project(burp_file, session_gap=30):
    """Main function for Burp project analysis."""
    print(f"\n{'='*60}")
    print(f"  TIME ANALYSIS - BURP PROJECT")
    print(f"  {burp_file.split('/')[-1]}")
    print(f"{'='*60}\n")

    print("[*] Extracting timestamps...")
    timestamps = extract_timestamps(burp_file)

    if not timestamps:
        print("[!] No timestamps found in file.")
        return None

    print(f"\n[+] Found {len(timestamps)} unique timestamps\n")

    # Basic statistics
    first_ts = timestamps[0]
    last_ts = timestamps[-1]

    print(f"[*] TIME RANGE:")
    print(f"    First request: {ms_to_datetime(first_ts).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"    Last request:  {ms_to_datetime(last_ts).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"    Total range:   {format_duration(last_ts - first_ts)}\n")

    # Session analysis
    sessions = analyze_sessions(timestamps, session_gap)

    print(f"[*] WORK SESSIONS (gap > {session_gap} min = new session):")
    print(f"    Number of sessions: {len(sessions)}\n")

    total_work_time = 0
    daily_work = defaultdict(lambda: {'time': 0, 'sessions': 0, 'requests': 0})

    print(f"    {'No':<4} {'Date':<12} {'Start':<8} {'End':<8} {'Duration':<10} {'Req.':<6}")
    print(f"    {'-'*54}")

    for i, session in enumerate(sessions, 1):
        start_dt = ms_to_datetime(session['start'])
        end_dt = ms_to_datetime(session['end'])
        duration = session['end'] - session['start']

        # Minimum session is 5 minutes (even for single request)
        if duration < 300000:
            duration = 300000

        total_work_time += duration
        day_key = start_dt.strftime('%Y-%m-%d')
        daily_work[day_key]['time'] += duration
        daily_work[day_key]['sessions'] += 1
        daily_work[day_key]['requests'] += session['requests']

        # Show max 30 sessions
        if i <= 30:
            print(f"    {i:<4} {start_dt.strftime('%Y-%m-%d'):<12} "
                  f"{start_dt.strftime('%H:%M'):<8} {end_dt.strftime('%H:%M'):<8} "
                  f"{format_duration(duration):<10} {session['requests']:<6}")
        elif i == 31:
            print(f"    ... ({len(sessions) - 30} more sessions)")

    # Summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"\n    Total work time:       {format_duration(total_work_time)}")
    print(f"    Number of sessions:    {len(sessions)}")
    print(f"    Average session time:  {format_duration(total_work_time // max(1, len(sessions)))}")
    print(f"    Total requests:        {len(timestamps)}")

    # Daily breakdown
    print(f"\n[*] WORK TIME PER DAY:")
    print(f"    {'Date':<12} {'Time':<12} {'Sessions':<8} {'Requests':<10}")
    print(f"    {'-'*42}")

    for day in sorted(daily_work.keys()):
        d = daily_work[day]
        print(f"    {day:<12} {format_duration(d['time']):<12} {d['sessions']:<8} {d['requests']:<10}")

    # Total
    total_hours = total_work_time / (1000 * 3600)
    total_days = len(daily_work)
    print(f"\n    {'TOTAL':<12} {format_duration(total_work_time):<12} {len(sessions):<8} {len(timestamps):<10}")
    print(f"\n    === ESTIMATED TIME: ~{total_hours:.1f} hours ({total_days} working days) ===")

    print(f"\n{'='*60}\n")

    return {
        'total_hours': total_hours,
        'total_days': total_days,
        'sessions': len(sessions),
        'requests': len(timestamps)
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 burp_time_analyzer.py <file.burp> [gap_minutes]")
        print("  gap_minutes - minutes of inactivity for new session (default 30)")
        print("               use a large value (e.g. 99999) to disable session splits")
        print("\nExamples:")
        print("  python3 burp_time_analyzer.py 2026-02-01-dell.burp")
        print("  python3 burp_time_analyzer.py 2026-02-01-dell.burp 20")
        print("  python3 burp_time_analyzer.py 2026-02-01-dell.burp 99999  # no breaks")
        sys.exit(1)

    burp_file = sys.argv[1]
    session_gap = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    analyze_burp_project(burp_file, session_gap)
