# Troubleshooting Guide

Solutions to common issues and problems.

## Installation Issues

### Issue: `pip: command not found`

**Symptom**: Terminal doesn't recognize `pip` command.

**Solutions**:

1. Use `python -m pip` instead:
   ```bash
   python -m pip install log-filter
   ```

2. Install pip:
   ```bash
   # Ubuntu/Debian
   sudo apt install python3-pip
   
   # macOS
   python3 -m ensurepip --upgrade
   
   # Windows
   python -m ensurepip --upgrade
   ```

### Issue: `Permission denied` during installation

**Symptom**: Error installing package due to permissions.

**Solutions**:

1. Install to user directory (recommended):
   ```bash
   pip install --user log-filter
   ```

2. Use virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install log-filter
   ```

3. Use sudo (not recommended):
   ```bash
   sudo pip install log-filter
   ```

### Issue: `Python version too old`

**Symptom**: Error message about Python version.

**Solution**: Upgrade to Python 3.10+:

```bash
# Ubuntu
sudo apt install python3.10

# macOS
brew install python@3.12

# Windows
# Download from python.org
```

### Issue: `ModuleNotFoundError: No module named 'log_filter'`

**Symptom**: Python cannot find the log_filter module.

**Solutions**:

1. Verify installation:
   ```bash
   pip show log-filter
   python -c "import log_filter; print(log_filter.__version__)"
   ```

2. Check you're using the right Python:
   ```bash
   which python  # Linux/macOS
   where python  # Windows
   ```

3. Reinstall:
   ```bash
   pip uninstall log-filter
   pip install log-filter
   ```

## Runtime Issues

### Issue: `FileNotFoundError: [Errno 2] No such file or directory`

**Symptom**: Cannot find specified file or directory.

**Solutions**:

1. Check path exists:
   ```bash
   ls /var/log  # Linux/macOS
   dir C:\logs  # Windows
   ```

2. Use absolute paths:
   ```bash
   log-filter "ERROR" /var/log  # Not: ./log or ../log
   ```

3. Check permissions:
   ```bash
   ls -la /var/log
   ```

### Issue: `PermissionError: [Errno 13] Permission denied`

**Symptom**: Cannot read log files due to permissions.

**Solutions**:

1. Run with sudo (if appropriate):
   ```bash
   sudo log-filter "ERROR" /var/log
   ```

2. Check file permissions:
   ```bash
   ls -la /var/log/*.log
   ```

3. Change permissions (if you own the files):
   ```bash
   chmod +r /path/to/logs/*.log
   ```

4. Copy logs to accessible location:
   ```bash
   sudo cp /var/log/*.log ~/logs/
   log-filter "ERROR" ~/logs
   ```

### Issue: No matches found

**Symptom**: Search returns 0 matches when you expect results.

**Solutions**:

1. Try case-insensitive search (default):
   ```bash
   log-filter "error" /var/log  # Matches ERROR, Error, error
   ```

2. Check expression syntax:
   ```bash
   # Wrong
   log-filter "ERROR" AND "database" /var/log
   
   # Correct
   log-filter "ERROR AND database" /var/log
   ```

3. Use verbose mode to see what's happening:
   ```bash
   log-filter "ERROR" /var/log --verbose
   ```

4. Test with simple search first:
   ```bash
   # Start simple
   log-filter "ERROR" /var/log
   
   # Then add complexity
   log-filter "ERROR AND database" /var/log
   ```

5. Check file patterns:
   ```bash
   # Make sure you're including the right files
   log-filter "ERROR" /var/log -i "*.log" --verbose
   ```

### Issue: `ParseError: Unexpected token` or syntax errors

**Symptom**: Expression parsing fails.

**Solutions**:

1. Check parentheses are balanced:
   ```bash
   # Wrong
   log-filter "(ERROR AND database" /var/log
   
   # Correct
   log-filter "(ERROR AND database)" /var/log
   ```

2. Quote the expression:
   ```bash
   # Wrong (shell interprets AND)
   log-filter ERROR AND database /var/log
   
   # Correct
   log-filter "ERROR AND database" /var/log
   ```

3. Use proper operators (AND, OR, NOT - all caps):
   ```bash
   # Wrong
   log-filter "ERROR and database" /var/log
   
   # Correct
   log-filter "ERROR AND database" /var/log
   ```

4. Test expression syntax:
   ```bash
   # Dry run to test
   log-filter "(ERROR OR WARNING) AND database" /var/log --dry-run
   ```

### Issue: Out of memory errors

**Symptom**: Process crashes or system runs out of memory.

**Solutions**:

1. Reduce worker count:
   ```bash
   log-filter "ERROR" /var/log -w 2
   ```

2. Reduce buffer size:
   ```bash
   log-filter "ERROR" /var/log --buffer-size 4096
   ```

3. Process smaller batches:
   ```bash
   # Process one directory at a time
   log-filter "ERROR" /var/log/app -o app-errors.txt
   log-filter "ERROR" /var/log/sys -o sys-errors.txt
   ```

4. Limit file size or depth:
   ```bash
   log-filter "ERROR" /var/log --max-depth 2
   ```

### Issue: Very slow performance

**Symptom**: Processing takes much longer than expected.

**Solutions**:

1. Increase worker threads:
   ```bash
   log-filter "ERROR" /var/log -w 8
   ```

2. Increase buffer size for large files:
   ```bash
   log-filter "ERROR" /var/log --buffer-size 65536
   ```

3. Use simpler expressions:
   ```bash
   # Complex (slower)
   log-filter "(ERROR OR WARN OR INFO) AND (db OR database OR sql)" /var/log
   
   # Simpler (faster)
   log-filter "ERROR AND database" /var/log
   ```

4. Limit search scope:
   ```bash
   # Narrow down file patterns
   log-filter "ERROR" /var/log -i "app.log" -i "system.log"
   ```

5. Use max-depth to limit traversal:
   ```bash
   log-filter "ERROR" /var/log --max-depth 3
   ```

6. Check disk I/O:
   ```bash
   # Slow storage can bottleneck processing
   # Consider moving logs to faster storage temporarily
   ```

### Issue: Output file already exists

**Symptom**: Error that output file exists.

**Solutions**:

1. Use `--overwrite` flag:
   ```bash
   log-filter "ERROR" /var/log -o errors.txt --overwrite
   ```

2. Use different output file:
   ```bash
   log-filter "ERROR" /var/log -o errors-$(date +%Y%m%d).txt
   ```

3. Delete existing file:
   ```bash
   rm errors.txt
   log-filter "ERROR" /var/log -o errors.txt
   ```

### Issue: Encoding errors (UnicodeDecodeError)

**Symptom**: Cannot decode file with specified encoding.

**Solutions**:

1. Use `replace` error handling (default):
   ```bash
   log-filter "ERROR" /var/log --errors replace
   ```

2. Try different encoding:
   ```bash
   # Try UTF-16
   log-filter "ERROR" /var/log --encoding utf-16
   
   # Try Latin-1
   log-filter "ERROR" /var/log --encoding latin-1
   ```

3. Ignore encoding errors:
   ```bash
   log-filter "ERROR" /var/log --errors ignore
   ```

4. Check file encoding:
   ```bash
   file -bi /var/log/app.log
   ```

## Configuration Issues

### Issue: Config file not found

**Symptom**: Cannot load configuration file.

**Solutions**:

1. Use absolute path:
   ```bash
   log-filter --config /path/to/config.yaml
   ```

2. Check file exists:
   ```bash
   ls -la config.yaml
   ```

3. Check YAML syntax:
   ```bash
   python -c "import yaml; yaml.safe_load(open('config.yaml'))"
   ```

### Issue: Invalid YAML syntax

**Symptom**: YAML parsing errors.

**Solutions**:

1. Check indentation (must use spaces, not tabs):
   ```yaml
   # Wrong (tabs)
   search:
   	expression: "ERROR"
   
   # Correct (spaces)
   search:
     expression: "ERROR"
   ```

2. Quote strings with special characters:
   ```yaml
   # Wrong
   search:
     expression: ERROR: Failed
   
   # Correct
   search:
     expression: "ERROR: Failed"
   ```

3. Validate YAML online:
   - Use https://yaml-online-parser.appspot.com/
   - Or install yamllint: `pip install yamllint`

### Issue: CLI arguments don't override config file

**Symptom**: Configuration file values used instead of CLI arguments.

**Solution**: CLI arguments should override config file. If not:

1. Check argument order:
   ```bash
   # Correct
   log-filter --config config.yaml "CRITICAL"
   
   # Arguments after --config
   log-filter --config config.yaml -o different.txt
   ```

2. Verify with verbose mode:
   ```bash
   log-filter --config config.yaml "CRITICAL" --verbose
   ```

## Performance Issues

### Issue: High memory usage

**Symptom**: Process consumes too much memory.

**Solutions**:

1. Reduce workers:
   ```bash
   log-filter "ERROR" /var/log -w 2
   ```

2. Process files sequentially:
   ```bash
   log-filter "ERROR" /var/log -w 1
   ```

3. Use smaller buffer:
   ```bash
   log-filter "ERROR" /var/log --buffer-size 4096
   ```

### Issue: High CPU usage

**Symptom**: Process uses excessive CPU.

**Solutions**:

1. Reduce worker count:
   ```bash
   log-filter "ERROR" /var/log -w 2
   ```

2. Simplify expressions:
   ```bash
   # Complex regex patterns can be CPU-intensive
   log-filter "ERROR" /var/log  # Simple is faster
   ```

## Output Issues

### Issue: No output displayed

**Symptom**: Command runs but produces no output.

**Solutions**:

1. Check if results written to file:
   ```bash
   log-filter "ERROR" /var/log -o errors.txt
   cat errors.txt
   ```

2. Disable quiet mode:
   ```bash
   log-filter "ERROR" /var/log  # Without --quiet
   ```

3. Enable verbose mode:
   ```bash
   log-filter "ERROR" /var/log --verbose
   ```

### Issue: Output format unexpected

**Symptom**: Output doesn't look right.

**Solutions**:

1. Check if terminal supports ANSI colors:
   ```bash
   # Disable colors
   NO_COLOR=1 log-filter "ERROR" /var/log
   ```

2. Redirect to file for plain text:
   ```bash
   log-filter "ERROR" /var/log -o errors.txt
   ```

## Debugging

### Enable Debug Logging

```bash
# Set log level
export LOG_LEVEL=DEBUG
log-filter "ERROR" /var/log --verbose
```

### Check System Resources

```bash
# Check disk space
df -h /var/log

# Check memory
free -h

# Check running processes
ps aux | grep log-filter
```

### Trace Execution

```bash
# Use strace (Linux)
strace -o trace.log log-filter "ERROR" /var/log

# Use dtruss (macOS)
sudo dtruss log-filter "ERROR" /var/log

# Use Process Monitor (Windows)
# Download from Microsoft Sysinternals
```

### Profile Performance

```bash
# Install profiling tools
pip install py-spy

# Profile execution
py-spy record -o profile.svg -- log-filter "ERROR" /var/log
```

## Getting Help

### Built-in Help

```bash
# General help
log-filter --help

# Check version
log-filter --version
```

### Collect Diagnostic Information

When reporting issues, include:

1. Version information:
   ```bash
   log-filter --version
   python --version
   pip show log-filter
   ```

2. Command that failed:
   ```bash
   log-filter "ERROR" /var/log --verbose 2>&1 | tee error.log
   ```

3. System information:
   ```bash
   # Linux
   uname -a
   lsb_release -a
   
   # macOS
   sw_vers
   
   # Windows
   systeminfo
   ```

4. Configuration (if using):
   ```bash
   cat config.yaml
   ```

### Report Issues

- **GitHub Issues**: https://github.com/your-org/log-filter/issues
- **Discussions**: https://github.com/your-org/log-filter/discussions

### Community Resources

- **Documentation**: https://log-filter.readthedocs.io
- **Examples**: https://github.com/your-org/log-filter/tree/main/examples
- **Stack Overflow**: Tag questions with `log-filter`

## Common Error Messages

### Complete Error Reference

#### FileNotFoundError

**Full Error:**
```
FileNotFoundError: [Errno 2] No such file or directory: '/var/log/app.log'
```

**Causes:**
- File or directory path doesn't exist
- Typo in path
- Relative path issue

**Solutions:**
```bash
# 1. Verify path exists
ls -la /var/log/app.log

# 2. Use absolute paths
log-filter "ERROR" $(pwd)/logs  # Not: ./logs

# 3. Check for typos
log-filter "ERROR" /var/log/app.log  # Not: /var/logs/app.log

# 4. Use wildcard if unsure
log-filter "ERROR" /var/log/*.log
```

#### PermissionError

**Full Error:**
```
PermissionError: [Errno 13] Permission denied: '/var/log/secure'
```

**Causes:**
- Insufficient permissions to read file
- Root-owned log files
- SELinux/AppArmor restrictions

**Solutions:**
```bash
# 1. Run with elevated privileges (if appropriate)
sudo log-filter "ERROR" /var/log/secure

# 2. Check file permissions
ls -la /var/log/secure
# Output: -rw------- 1 root root ... /var/log/secure

# 3. Add user to appropriate group
sudo usermod -a -G adm $USER  # For syslog access on Debian/Ubuntu

# 4. Copy logs to accessible location
sudo cp /var/log/secure ~/secure.log
sudo chown $USER ~/secure.log
log-filter "ERROR" ~/secure.log

# 5. Check SELinux context (if applicable)
ls -Z /var/log/secure
sudo setenforce 0  # Temporarily disable for testing
```

#### ParseError: Invalid Expression

**Full Error:**
```
ParseError: Unexpected token at position 15: 'AND'
Expression: ERROR (AND database)
                   ^
```

**Causes:**
- Missing operand
- Unbalanced parentheses
- Invalid operator syntax

**Solutions:**
```bash
# Wrong: Missing operand
log-filter "ERROR AND" /var/log

# Correct:
log-filter "ERROR AND database" /var/log

# Wrong: Unbalanced parentheses
log-filter "(ERROR AND database" /var/log

# Correct:
log-filter "(ERROR AND database)" /var/log

# Wrong: Invalid nesting
log-filter "ERROR (AND database)" /var/log

# Correct:
log-filter "ERROR AND database" /var/log
log-filter "(ERROR) AND (database)" /var/log
```

#### UnicodeDecodeError

**Full Error:**
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 123
```

**Causes:**
- File not in UTF-8 encoding
- Binary data in log file
- Corrupted file

**Solutions:**
```bash
# 1. Use error handling (default: replace)
log-filter "ERROR" /var/log --errors replace

# 2. Try different encodings
log-filter "ERROR" /var/log --encoding latin-1
log-filter "ERROR" /var/log --encoding utf-16
log-filter "ERROR" /var/log --encoding cp1252  # Windows

# 3. Detect encoding
file -bi /var/log/app.log
# Output: text/plain; charset=iso-8859-1

# 4. Ignore errors (may lose data)
log-filter "ERROR" /var/log --errors ignore

# 5. Convert file encoding
iconv -f iso-8859-1 -t utf-8 /var/log/app.log -o /tmp/app-utf8.log
log-filter "ERROR" /tmp/app-utf8.log
```

#### MemoryError

**Full Error:**
```
MemoryError: Unable to allocate array
```

**Causes:**
- Too many workers
- Very large files
- Insufficient system memory

**Solutions:**
```bash
# 1. Reduce workers
log-filter "ERROR" /var/log -w 2  # Instead of default

# 2. Reduce buffer size
log-filter "ERROR" /var/log --buffer-size 4096

# 3. Process in batches
for file in /var/log/*.log; do
  log-filter "ERROR" "$file" >> results.txt
  sleep 1  # Allow garbage collection
done

# 4. Filter by date first
log-filter "ERROR" /var/log --after 2026-01-01

# 5. Check available memory
free -h  # Linux
vm_stat  # macOS
```

#### ConfigurationError

**Full Error:**
```
ConfigurationError: Invalid configuration file: config.yaml
  - Missing required field: 'search.expression'
```

**Causes:**
- Invalid YAML/JSON syntax
- Missing required fields
- Type mismatch

**Solutions:**
```bash
# 1. Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# 2. Check required fields
cat config.yaml
# Must have:
# search:
#   expression: "..."
# files:
#   search_root: "..."

# 3. Use template as starting point
log-filter --generate-config > config.yaml

# 4. Validate with schema
jsonschema -i config.yaml config-schema.json
```

#### TimeoutError

**Full Error:**
```
TimeoutError: Processing timeout after 3600 seconds
```

**Causes:**
- Very large dataset
- Slow network storage
- Complex expressions

**Solutions:**
```bash
# 1. Increase timeout (config file)
processing:
  timeout: 7200  # 2 hours

# 2. Optimize performance
log-filter "ERROR" /var/log -w 16 --buffer-size 65536

# 3. Process in smaller batches
log-filter "ERROR" /var/log/2026-01 -o jan-errors.txt
log-filter "ERROR" /var/log/2026-02 -o feb-errors.txt

# 4. Use date filters
log-filter "ERROR" /var/log --after 2026-01-01 --before 2026-01-31
```

### Error Code Reference

| Exit Code | Meaning | Common Cause |
|-----------|---------|---------------|
| **0** | Success | Normal completion |
| **1** | General error | Invalid arguments, file not found |
| **2** | Parse error | Invalid expression syntax |
| **3** | Configuration error | Invalid config file |
| **4** | Permission error | Cannot access files |
| **5** | I/O error | Read/write failure |
| **130** | User interrupt | Ctrl+C pressed |
| **137** | Killed by system | Out of memory (OOM killer) |

**Check exit code:**
```bash
log-filter "ERROR" /var/log
echo "Exit code: $?"  # Linux/macOS

log-filter "ERROR" /var/log
echo "Exit code: $LASTEXITCODE"  # Windows PowerShell
```

## Platform-Specific Issues

### Linux

#### Issue: SELinux blocking file access

**Symptom:**
```
PermissionError even with correct file permissions
```

**Solutions:**
```bash
# 1. Check SELinux status
getenforce

# 2. Check context
ls -Z /var/log/app.log

# 3. Temporarily disable (testing only)
sudo setenforce 0
log-filter "ERROR" /var/log
sudo setenforce 1

# 4. Add SELinux policy (permanent)
sudo ausearch -c 'python' --raw | audit2allow -M log-filter-policy
sudo semodule -i log-filter-policy.pp

# 5. Change file context
sudo chcon -t user_home_t /var/log/app.log
```

#### Issue: systemd journal access

**Symptom:**
```
Cannot access journalctl logs
```

**Solutions:**
```bash
# 1. Export journal to file first
sudo journalctl -u myapp.service > /tmp/myapp.log
log-filter "ERROR" /tmp/myapp.log

# 2. Add user to systemd-journal group
sudo usermod -a -G systemd-journal $USER
# Log out and back in

# 3. Use journalctl directly
journalctl -u myapp.service | log-filter "ERROR" -
```

### macOS

#### Issue: System Integrity Protection (SIP) restrictions

**Symptom:**
```
Operation not permitted on system directories
```

**Solutions:**
```bash
# 1. Use unified logging tool
log show --predicate 'eventMessage contains "ERROR"' --last 1h > /tmp/system.log
log-filter "ERROR" /tmp/system.log

# 2. Access user-accessible logs
log-filter "ERROR" ~/Library/Logs
log-filter "ERROR" /usr/local/var/log

# 3. Don't disable SIP - use proper tools
```

#### Issue: Gatekeeper blocking execution

**Symptom:**
```
"python" cannot be opened because the developer cannot be verified
```

**Solutions:**
```bash
# 1. Allow in System Preferences
# System Preferences > Security & Privacy > Allow

# 2. Remove quarantine attribute
xattr -d com.apple.quarantine $(which log-filter)

# 3. Use official Python from python.org
brew uninstall python
# Download from python.org
```

### Windows

#### Issue: Path with spaces

**Symptom:**
```
FileNotFoundError: C:\Program not found
```

**Solutions:**
```powershell
# 1. Use quotes
log-filter "ERROR" "C:\Program Files\App\logs"

# 2. Use 8.3 short names
log-filter "ERROR" C:\PROGRA~1\App\logs

# 3. Use forward slashes
log-filter "ERROR" C:/Program Files/App/logs
```

#### Issue: PowerShell operator confusion

**Symptom:**
```
Expression parsed incorrectly
```

**Solutions:**
```powershell
# 1. Use single quotes (prevents PowerShell parsing)
log-filter 'ERROR AND database' C:\logs

# 2. Escape special characters
log-filter "ERROR `& database" C:\logs

# 3. Use --% to stop PowerShell parsing
log-filter --% "ERROR AND database" C:\logs
```

#### Issue: Windows Defender blocking

**Symptom:**
```
Process killed or extremely slow
```

**Solutions:**
```powershell
# 1. Add exclusion for Python
# Windows Security > Virus & threat protection > Exclusions
# Add: C:\Python311\python.exe

# 2. Add exclusion for log directory
# Add: C:\logs

# 3. Temporarily disable real-time protection (testing only)
```

#### Issue: Line ending issues (CRLF vs LF)

**Symptom:**
```
Unexpected \r characters in output
```

**Solutions:**
```powershell
# 1. Handle both line endings (automatic)
log-filter "ERROR" C:\logs  # Handles CRLF automatically

# 2. Convert files
(Get-Content file.log) | Set-Content -NoNewline file-unix.log

# 3. Use WSL for Unix-style logs
wsl log-filter "ERROR" /mnt/c/logs
```

### Docker/Container Issues

#### Issue: Permission denied in container

**Symptom:**
```
PermissionError accessing mounted volumes
```

**Solutions:**
```bash
# 1. Run as root
docker run --rm -v /var/log:/logs your/log-filter \
  log-filter "ERROR" /logs

# 2. Match host UID/GID
docker run --rm --user $(id -u):$(id -g) \
  -v /var/log:/logs your/log-filter \
  log-filter "ERROR" /logs

# 3. Change volume permissions
sudo chmod -R +r /var/log

# 4. Use :ro for read-only
docker run --rm -v /var/log:/logs:ro your/log-filter \
  log-filter "ERROR" /logs
```

#### Issue: Container OOM killed

**Symptom:**
```
Exit code 137 (killed by OOM)
```

**Solutions:**
```bash
# 1. Increase memory limit
docker run --rm --memory=2g -v /var/log:/logs your/log-filter \
  log-filter "ERROR" /logs

# 2. Reduce workers in container
docker run --rm -v /var/log:/logs your/log-filter \
  log-filter "ERROR" /logs -w 2

# 3. Check container memory
docker stats $(docker ps -q)
```

## Debugging Workflows

### Workflow 1: No Matches Found

```bash
# Step 1: Verify files are being scanned
log-filter "ERROR" /var/log --verbose
# Look for: "Scanning: /var/log/app.log"

# Step 2: Check if search term exists
grep -r "ERROR" /var/log | head

# Step 3: Test with simple expression
log-filter "ERROR" /var/log

# Step 4: Add complexity gradually
log-filter "ERROR" /var/log  # Works?
log-filter "ERROR AND database" /var/log  # Still works?
log-filter "(ERROR OR CRITICAL) AND database" /var/log  # Now?

# Step 5: Check file patterns
log-filter "ERROR" /var/log -i "*.log" --verbose

# Step 6: Test with known file
grep "ERROR" /var/log/app.log | head -1  # Get a line
log-filter "<that line>" /var/log/app.log  # Should match
```

### Workflow 2: Performance Issues

```bash
# Step 1: Baseline measurement
time log-filter "ERROR" /var/log --quiet
# Note: X seconds, Y lines/sec

# Step 2: Test worker scaling
for w in 1 2 4 8 16; do
  echo "Workers: $w"
  time log-filter "ERROR" /var/log -w $w --quiet
done

# Step 3: Check resource usage
# Terminal 1:
log-filter "ERROR" /var/log -w 8

# Terminal 2:
top -p $(pgrep -f log-filter)  # Check CPU, memory
iostat -x 1 10  # Check I/O

# Step 4: Profile expression
time log-filter "ERROR" /var/log --quiet
time log-filter "simple" /var/log --quiet
# Large difference? Expression is bottleneck

# Step 5: Check storage
dd if=/var/log/app.log of=/dev/null bs=1M
# Note: MB/s

# Step 6: Optimize based on findings
# If CPU < 50%: Increase workers, increase buffer
# If CPU > 90%: Decrease workers, simplify expression
# If high I/O wait: Reduce workers, copy locally
```

### Workflow 3: Encoding Issues

```bash
# Step 1: Detect encoding
file -bi /var/log/app.log
chardet /var/log/app.log  # pip install chardet

# Step 2: Try detected encoding
log-filter "ERROR" /var/log --encoding iso-8859-1

# Step 3: Use error handling
log-filter "ERROR" /var/log --errors replace
log-filter "ERROR" /var/log --errors ignore

# Step 4: Convert file if needed
iconv -f iso-8859-1 -t utf-8 /var/log/app.log > /tmp/app-utf8.log
log-filter "ERROR" /tmp/app-utf8.log

# Step 5: Find problematic line
python3 << 'EOF'
with open('/var/log/app.log', 'rb') as f:
    for i, line in enumerate(f, 1):
        try:
            line.decode('utf-8')
        except UnicodeDecodeError as e:
            print(f"Line {i}: {e}")
            print(f"Bytes: {line[:100]}")
            break
EOF
```

### Workflow 4: Configuration Debugging

```bash
# Step 1: Validate YAML syntax
python -c "import yaml; print(yaml.safe_load(open('config.yaml')))"

# Step 2: Check required fields
grep -E "^(search|files|output):" config.yaml

# Step 3: Test without config
log-filter "ERROR" /var/log  # Works?

# Step 4: Test with config
log-filter --config config.yaml --verbose

# Step 5: Override config values
log-filter --config config.yaml "CRITICAL"  # Different expression
log-filter --config config.yaml -o test.txt  # Different output

# Step 6: Generate valid config
log-filter --generate-config > valid-config.yaml
diff config.yaml valid-config.yaml
```

## Best Practices for Avoiding Issues

### Before Running

1. **Test with dry-run (if available)**
   ```bash
   log-filter "ERROR" /var/log --dry-run
   ```

2. **Start with small dataset**
   ```bash
   # Test on single file first
   log-filter "ERROR" /var/log/app.log
   
   # Then scale up
   log-filter "ERROR" /var/log
   ```

3. **Validate expression syntax**
   ```bash
   # Simple test
   echo "ERROR: test" | log-filter "ERROR" -
   ```

4. **Check file accessibility**
   ```bash
   ls -la /var/log/*.log
   head -1 /var/log/app.log  # Can you read it?
   ```

5. **Estimate resource requirements**
   ```bash
   # Check total size
   du -sh /var/log
   
   # Plan accordingly:
   # < 1 GB: default settings fine
   # 1-10 GB: 4-8 workers
   # > 10 GB: 8-16 workers, monitor resources
   ```

### During Development

1. **Use verbose mode initially**
   ```bash
   log-filter "ERROR" /var/log --verbose
   ```

2. **Start simple, add complexity gradually**
   ```bash
   log-filter "ERROR" /var/log           # Works?
   log-filter "ERROR AND database" /var/log  # Add AND
   log-filter "(ERROR OR CRITICAL) AND database" /var/log  # Add OR
   ```

3. **Always quote expressions**
   ```bash
   # Wrong
   log-filter ERROR AND database /var/log
   
   # Correct
   log-filter "ERROR AND database" /var/log
   ```

4. **Use absolute paths**
   ```bash
   # Avoid
   log-filter "ERROR" ./logs
   log-filter "ERROR" ../logs
   
   # Prefer
   log-filter "ERROR" /home/user/logs
   log-filter "ERROR" $(pwd)/logs
   ```

5. **Test configuration files**
   ```bash
   python -c "import yaml; yaml.safe_load(open('config.yaml'))"
   ```

### During Execution

1. **Monitor system resources**
   ```bash
   # Watch in another terminal
   watch 'ps aux | grep log-filter'
   ```

2. **Use appropriate worker count**
   ```bash
   # Start conservative
   log-filter "ERROR" /var/log -w 4
   
   # Increase if CPU < 50%
   log-filter "ERROR" /var/log -w 8
   ```

3. **Handle interrupts gracefully**
   ```bash
   # Save partial results
   log-filter "ERROR" /var/log -o results.txt
   # Press Ctrl+C if needed - partial results saved
   ```

### In Production

1. **Keep log-filter updated**
   ```bash
   pip install --upgrade log-filter
   ```

2. **Use configuration files**
   ```bash
   # Version control your configs
   log-filter --config production-errors.yaml
   ```

3. **Log processing activity**
   ```yaml
   # config.yaml
   logging:
     level: INFO
     file: /var/log/log-filter.log
   ```

4. **Set resource limits**
   ```bash
   # Use ulimit to prevent runaway processes
   ulimit -m 2048000  # 2 GB memory limit
   ulimit -t 3600     # 1 hour CPU time limit
   log-filter "ERROR" /var/log
   ```

5. **Rotate output files**
   ```bash
   # Use date in filename
   log-filter "ERROR" /var/log -o "errors-$(date +%Y-%m-%d).txt"
   
   # Or append with rotate
   log-filter "ERROR" /var/log -o errors.txt --append
   logrotate /etc/logrotate.d/log-filter
   ```

6. **Monitor and alert**
   ```bash
   # Example monitoring script
   #!/bin/bash
   log-filter "CRITICAL" /var/log --stats 2>&1 | \
     grep -q "Matches: [1-9]" && \
     echo "ALERT: Critical errors found!" | mail -s "Log Alert" ops@example.com
   ```

## Next Steps

- **[Configuration Guide](configuration.md)** - Configure for your environment
- **[Quick Start](quickstart.md)** - Learn basic usage
- **[API Documentation](api/index.rst)** - Programmatic usage
