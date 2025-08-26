# Recruiting Analyst

A Python tool for pulling data from the Greenhouse API to calculate recruiting metrics and generate datasets.

## Overview

Recruiting Analyst is designed to help HR and recruiting teams analyze their hiring data by:
- Fetching data from the Greenhouse API
- Calculating key recruiting metrics (time-to-fill, conversion rates, etc.)
- Generating comprehensive reports for pipeline analysis
- Tracking AI rollout status across engineering roles

## Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Install the package: `pip install -e .`

## Configuration

1. Copy `src/analyst/config/greenhouse.py` and add your Greenhouse API key
2. Update the `DEPARTMENT_MAP` and `RELEVANT_DEPARTMENTS` as needed
3. The config file is automatically ignored by Git for security

## Available Commands

### Greenhouse API Integration

#### `analyst check-greenhouse-integration`
Test your Greenhouse API connection and authentication.
```bash
analyst check-greenhouse-integration
```

#### `analyst get-jobs`
Fetch and display jobs from Greenhouse API.
```bash
# Get all jobs (first 5)
analyst get-jobs

# Get jobs from specific department
analyst get-jobs --department "R&D"

# Include closed jobs
analyst get-jobs --include-closed

# Limit number of results
analyst get-jobs --limit 10
```

### Job Cache Management

#### `analyst refresh-job-cache`
Refresh the job cache by fetching all jobs from relevant departments.
```bash
analyst refresh-job-cache

# Use custom cache path
analyst refresh-job-cache --cache-path "custom/path/jobs.yaml"
```

#### `analyst print-job-from-cache`
Display detailed information about a specific job from the cache.
```bash
analyst print-job-from-cache 123456789
```

### Application Analysis

#### `analyst get-application`
Fetch and display detailed information about a specific application.
```bash
analyst get-application 987654321
```

### Reporting

#### `analyst report-ai-rollout`
Generate a CSV report on AI rollout status across all engineering jobs.
```bash
analyst report-ai-rollout > ai_rollout_report.csv
```

**CSV Output Fields:**
- `job_name` - Name of the job
- `job_id` - Greenhouse job ID
- `ai_eligible` - Whether the job is eligible for AI features
- `ai_enabled` - Whether AI features are currently enabled
- `recruiter_name` - Primary recruiter assigned
- `location` - Job location
- `department` - Department name
- `level` - Seniority level (SWE1, SWE2, Senior, Staff)

#### `analyst report-job-pipeline`
Generate a comprehensive CSV report of all applications in a specific job's pipeline.
```bash
analyst report-job-pipeline 123456789 > pipeline_report.csv
```

**CSV Output Fields:**
- `application_id` - Greenhouse application ID
- `current_stage` - Current stage name
- `stage_type` - Type of stage (take home, interview, other)
- `stage_status` - Current status (pending, scheduled, complete, etc.)
- `moved_to_stage_at` - When candidate moved to current stage
- `availability_requested_at` - When availability was requested
- `availability_received_at` - When candidate submitted availability
- `interview_scheduled_at` - When interview was scheduled
- `interview_date` - Actual interview date/time
- `take_home_submitted_at` - When take-home was submitted
- `take_home_graded_at` - When take-home was graded
- `scheduled_interviews_count` - Number of scheduled interviews
- `completed_interviews_count` - Number of completed interviews
- `recruiter_name` - Primary recruiter
- `location` - Job location
- `department` - Department name

## Project Structure

```
recruiting_analyst/
├── src/analyst/
│   ├── __init__.py
│   ├── client/
│   │   └── greenhouse.py          # Greenhouse API client
│   ├── cli/
│   │   ├── main.py               # Main CLI entry point
│   │   ├── greenhouse.py         # Greenhouse-related commands
│   │   └── reports.py            # Reporting commands
│   ├── config/
│   │   └── greenhouse.py         # API configuration
│   ├── dataclasses.py            # Data models
│   └── job_manager.py            # Job cache management
├── tests/
│   ├── analyst/
│   │   ├── test_dataclasses.py
│   │   └── test_reports.py
│   └── client/
│       ├── test_data.py
│       └── test_greenhouse.py
├── requirements.txt
├── setup.py
└── README.md
```

## Development

### Running Tests
```bash
python -m pytest tests/ -v
```

### Adding New Commands
1. Create your command function in the appropriate CLI module
2. Register it in `src/analyst/cli/main.py`
3. Add tests in the corresponding test file

## Requirements

- Python 3.11+
- Greenhouse API access
- Required packages listed in `requirements.txt`

## License

MIT License