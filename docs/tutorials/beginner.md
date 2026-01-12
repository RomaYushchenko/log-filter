# Beginner Tutorial: Getting Started with Log Filter

**Duration:** 10 minutes  
**Level:** Beginner  
**Prerequisites:** Python 3.10+, pip installed  
**Last Updated:** January 8, 2026

---

## Learning Objectives

By the end of this tutorial, you will be able to:

- ✅ Install Log Filter on your system
- ✅ Perform basic log searches
- ✅ Use simple boolean expressions (AND, OR, NOT)
- ✅ Save filtered results to a file
- ✅ View processing statistics
- ✅ Use configuration files

---

## Step 1: Installation (2 minutes)

### Install via pip

Open your terminal and run:

```bash
pip install log-filter
```

### Verify Installation

Check that Log Filter is installed correctly:

```bash
log-filter --version
```

You should see:
```
Log Filter v2.0.0
```

### Check Help

View available commands:

```bash
log-filter --help
```

---

## Step 2: Prepare Sample Data (1 minute)

Let's create a sample log file to practice with:

```bash
# Create a sample log file
cat > sample.log << 'EOF'
2026-01-08 10:00:00 INFO Application started successfully
2026-01-08 10:00:15 INFO User john logged in
2026-01-08 10:01:30 WARNING Database connection slow (500ms)
2026-01-08 10:02:45 ERROR Failed to process payment for order #12345
2026-01-08 10:03:10 INFO Payment retry successful
2026-01-08 10:04:22 ERROR Database connection timeout
2026-01-08 10:05:33 CRITICAL System out of memory - shutting down
2026-01-08 10:06:00 INFO System restarted
2026-01-08 10:07:15 WARNING High CPU usage detected (85%)
2026-01-08 10:08:30 INFO Scheduled backup completed
EOF
```

**On Windows PowerShell:**

```powershell
@"
2026-01-08 10:00:00 INFO Application started successfully
2026-01-08 10:00:15 INFO User john logged in
2026-01-08 10:01:30 WARNING Database connection slow (500ms)
2026-01-08 10:02:45 ERROR Failed to process payment for order #12345
2026-01-08 10:03:10 INFO Payment retry successful
2026-01-08 10:04:22 ERROR Database connection timeout
2026-01-08 10:05:33 CRITICAL System out of memory - shutting down
2026-01-08 10:06:00 INFO System restarted
2026-01-08 10:07:15 WARNING High CPU usage detected (85%)
2026-01-08 10:08:30 INFO Scheduled backup completed
"@ | Out-File -FilePath sample.log -Encoding UTF8
```

---

## Step 3: Your First Search (1 minute)

### Search for a Simple Term

Let's find all ERROR messages:

```bash
log-filter --expr "ERROR" --input sample.log
```

**Output:**
```
2026-01-08 10:02:45 ERROR Failed to process payment for order #12345
2026-01-08 10:04:22 ERROR Database connection timeout
```

**What happened:**
- Log Filter searched through `sample.log`
- Found all lines containing "ERROR"
- Displayed the matching lines

### Case Sensitivity

By default, searches are case-insensitive. Try:

```bash
log-filter --expr "error" --input sample.log
```

You'll get the same results! To make searches case-sensitive:

```bash
log-filter --expr "ERROR" --input sample.log --case-sensitive
```

---

## Step 4: Boolean Expressions (3 minutes)

### Using OR - Find Multiple Terms

Find ERROR or CRITICAL messages:

```bash
log-filter --expr "ERROR OR CRITICAL" --input sample.log
```

**Output:**
```
2026-01-08 10:02:45 ERROR Failed to process payment for order #12345
2026-01-08 10:04:22 ERROR Database connection timeout
2026-01-08 10:05:33 CRITICAL System out of memory - shutting down
```

### Using AND - Find Combined Terms

Find messages about database that are errors:

```bash
log-filter --expr "ERROR AND database" --input sample.log
```

**Output:**
```
2026-01-08 10:04:22 ERROR Database connection timeout
```

### Using NOT - Exclude Terms

Find all errors except database-related:

```bash
log-filter --expr "ERROR AND NOT database" --input sample.log
```

**Output:**
```
2026-01-08 10:02:45 ERROR Failed to process payment for order #12345
```

### Combining Operators with Parentheses

Find ERROR or WARNING messages related to database:

```bash
log-filter --expr "(ERROR OR WARNING) AND database" --input sample.log
```

**Output:**
```
2026-01-08 10:01:30 WARNING Database connection slow (500ms)
2026-01-08 10:04:22 ERROR Database connection timeout
```

**💡 Tip:** Use parentheses `()` to control the order of operations!

---

## Step 5: Saving Results (1 minute)

### Save to a File

Instead of printing to screen, save results to a file:

```bash
log-filter --expr "ERROR OR CRITICAL" --input sample.log --output errors.txt
```

Check the output file:

```bash
cat errors.txt
```

**On Windows:**
```powershell
Get-Content errors.txt
```

### View Statistics

Add the `--stats` flag to see processing statistics:

```bash
log-filter --expr "ERROR" --input sample.log --output errors.txt --stats
```

**Output:**
```
================================================================================
Processing Statistics
================================================================================

Files:
  Processed:     1
  Matched:       1 (100.0%)
  Skipped:       0

Records:
  Total:         10
  Matched:       2 (20.0%)

Performance:
  Time:          0.01s
  Throughput:    1,000 records/sec
  Speed:         0.5 MB/sec

================================================================================
```

**What the statistics tell you:**
- **Files Processed:** How many files were analyzed
- **Records Total:** How many log lines were processed
- **Records Matched:** How many lines matched your search
- **Time:** How long the search took
- **Throughput:** How many records per second were processed

---

## Step 6: Using Configuration Files (2 minutes)

### Create a Configuration File

Instead of typing long commands, save your settings to a file:

```yaml
# config.yaml
search:
  expression: "ERROR OR WARNING"
  ignore_case: false

files:
  search_root: .
  include_patterns:
    - "*.log"

output:
  output_file: filtered_results.txt
  show_stats: true
```

Save this as `config.yaml`

### Run with Configuration

```bash
log-filter --config config.yaml
```

This will:
1. Search for ERROR or WARNING
2. Look for all `.log` files in the current directory
3. Save results to `filtered_results.txt`
4. Show statistics

**💡 Tip:** Configuration files are great for repeated tasks!

### JSON Configuration

You can also use JSON format:

```json
{
  "search": {
    "expression": "ERROR OR WARNING",
    "ignore_case": false
  },
  "files": {
    "search_root": ".",
    "include_patterns": ["*.log"]
  },
  "output": {
    "output_file": "filtered_results.txt",
    "show_stats": true
  }
}
```

Save as `config.json` and run:

```bash
log-filter --config config.json
```

---

## Practice Exercises

Try these exercises to reinforce your learning:

### Exercise 1: Find All Severity Levels

Find all ERROR, WARNING, or CRITICAL messages:

```bash
log-filter --expr "ERROR OR WARNING OR CRITICAL" --input sample.log
```

<details>
<summary>Expected Output (Click to reveal)</summary>

```
2026-01-08 10:01:30 WARNING Database connection slow (500ms)
2026-01-08 10:02:45 ERROR Failed to process payment for order #12345
2026-01-08 10:04:22 ERROR Database connection timeout
2026-01-08 10:05:33 CRITICAL System out of memory - shutting down
2026-01-08 10:07:15 WARNING High CPU usage detected (85%)
```
</details>

### Exercise 2: Exclude INFO Messages

Find all messages except INFO:

```bash
log-filter --expr "NOT INFO" --input sample.log
```

<details>
<summary>Expected Output (Click to reveal)</summary>

```
2026-01-08 10:01:30 WARNING Database connection slow (500ms)
2026-01-08 10:02:45 ERROR Failed to process payment for order #12345
2026-01-08 10:04:22 ERROR Database connection timeout
2026-01-08 10:05:33 CRITICAL System out of memory - shutting down
2026-01-08 10:07:15 WARNING High CPU usage detected (85%)
```
</details>

### Exercise 3: Find Specific Topics

Find messages about "payment" or "backup":

```bash
log-filter --expr "payment OR backup" --input sample.log
```

<details>
<summary>Expected Output (Click to reveal)</summary>

```
2026-01-08 10:02:45 ERROR Failed to process payment for order #12345
2026-01-08 10:03:10 INFO Payment retry successful
2026-01-08 10:08:30 INFO Scheduled backup completed
```
</details>

### Exercise 4: Complex Expression

Find ERROR or CRITICAL messages, but exclude "payment" related ones:

```bash
log-filter --expr "(ERROR OR CRITICAL) AND NOT payment" --input sample.log
```

<details>
<summary>Expected Output (Click to reveal)</summary>

```
2026-01-08 10:04:22 ERROR Database connection timeout
2026-01-08 10:05:33 CRITICAL System out of memory - shutting down
```
</details>

---

## Common Beginner Mistakes

### ❌ Mistake 1: Forgetting Quotes

```bash
# Wrong - will not work
log-filter --expr ERROR OR WARNING --input sample.log

# Correct
log-filter --expr "ERROR OR WARNING" --input sample.log
```

**Why:** The shell interprets spaces, so wrap expressions in quotes.

### ❌ Mistake 2: Wrong Operator Order

```bash
# This might not work as expected
log-filter --expr "ERROR OR WARNING AND database"

# Better - use parentheses
log-filter --expr "(ERROR OR WARNING) AND database"
```

**Why:** Without parentheses, `AND` binds tighter than `OR`, leading to unexpected results.

### ❌ Mistake 3: Case Sensitivity Confusion

```bash
# If your log has "Error" (mixed case)
log-filter --expr "ERROR" --input sample.log --case-sensitive
# Might not match!

# Solution: Don't use --case-sensitive, or use "Error"
log-filter --expr "ERROR" --input sample.log
```

**Why:** Case-insensitive (default) is more flexible for most use cases.

---

## Quick Reference Card

### Basic Commands

| Task | Command |
|------|---------|
| Search single term | `log-filter --expr "ERROR" --input app.log` |
| OR expression | `log-filter --expr "ERROR OR WARNING" --input app.log` |
| AND expression | `log-filter --expr "ERROR AND database" --input app.log` |
| NOT expression | `log-filter --expr "NOT INFO" --input app.log` |
| Save to file | `log-filter --expr "ERROR" --input app.log --output errors.txt` |
| Show statistics | `log-filter --expr "ERROR" --input app.log --stats` |
| Use config file | `log-filter --config config.yaml` |

### Boolean Operators

| Operator | Symbol | Example | Meaning |
|----------|--------|---------|---------|
| AND | `AND` | `ERROR AND database` | Both must appear |
| OR | `OR` | `ERROR OR WARNING` | Either can appear |
| NOT | `NOT` | `NOT INFO` | Must not appear |

### Special Flags

| Flag | Purpose |
|------|---------|
| `--case-sensitive` | Make search case-sensitive |
| `--stats` | Show processing statistics |
| `--quiet` | Suppress progress output |
| `--highlight` | Highlight matching terms |

---

## What's Next?

Congratulations! You've completed the beginner tutorial. 🎉

### You learned:
- ✅ How to install Log Filter
- ✅ Basic search operations
- ✅ Boolean expressions (AND, OR, NOT)
- ✅ Saving results to files
- ✅ Viewing statistics
- ✅ Using configuration files

### Next Steps:

1. **[Intermediate Tutorial](intermediate.md)** - Learn about:
   - Date and time filtering
   - Working with multiple files
   - Regular expressions
   - Advanced configuration options
   - Performance tuning

2. **[Advanced Usage Guide](../advanced_usage.md)** - Explore:
   - Multi-worker configuration
   - Large file processing
   - Complex expression patterns
   - Production deployment

3. **[Integration Guide](../integration_guide.md)** - Integrate with:
   - CI/CD pipelines
   - Monitoring systems
   - Docker and Kubernetes

---

## Getting Help

### Documentation
- [Quick Start Guide](../quickstart.md)
- [Configuration Reference](../configuration.md)
- [Error Handling Guide](../error_handling.md)
- [Troubleshooting](../troubleshooting.md)

### Support
- GitHub Issues: https://github.com/your-org/log-filter/issues
- Documentation: https://log-filter.readthedocs.io

### Community
- Discord/Slack: [Join our community]
- Stack Overflow: Tag `log-filter`

---

## Appendix: Sample Log Files

### Application Log

```
2026-01-08 10:00:00 INFO [startup] Application initialized
2026-01-08 10:00:01 INFO [startup] Connecting to database
2026-01-08 10:00:02 INFO [startup] Database connection established
2026-01-08 10:00:05 INFO [api] API server listening on port 8080
2026-01-08 10:01:23 INFO [request] GET /api/users - 200 OK (15ms)
2026-01-08 10:02:34 WARNING [database] Slow query detected (500ms)
2026-01-08 10:03:45 ERROR [payment] Payment gateway timeout
2026-01-08 10:04:56 ERROR [payment] Failed to process transaction #12345
2026-01-08 10:05:12 INFO [payment] Payment retry successful
2026-01-08 10:06:23 CRITICAL [memory] Out of memory - shutting down
```

Save this to practice with more realistic log data!

---

**Tutorial Version:** 1.0  
**Last Updated:** January 8, 2026  
**Feedback:** Please report issues or suggestions on GitHub
