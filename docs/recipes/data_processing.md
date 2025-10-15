# Data Processing Recipes

This guide shows how to use fptk for common data processing tasks like ETL pipelines, validation, and transformation.

## ETL Pipeline Example

Let's build a complete ETL (Extract, Transform, Load) pipeline for processing user data from a CSV file.

```python
from fptk.core.func import pipe
from fptk.adt.result import Ok, Err
from fptk.validate import validate_all
from fptk.iter.lazy import map_iter, filter_iter
import csv

def process_user_csv(file_path: str):
    """Complete ETL pipeline for user data."""
    return pipe(
        file_path,
        read_csv_file,        # Extract
        lambda rows: map_iter(process_user_row, rows),  # Transform
        lambda results: filter_valid_results(results),  # Filter
        lambda valid_users: save_users_to_db(valid_users)  # Load
    )

def read_csv_file(path: str):
    """Extract: Read CSV file."""
    try:
        with open(path, 'r') as f:
            return Ok(list(csv.DictReader(f)))
    except FileNotFoundError:
        return Err(f"File not found: {path}")
    except Exception as e:
        return Err(f"Error reading file: {e}")

def process_user_row(row: dict):
    """Transform: Process individual user row."""
    return pipe(
        row,
        validate_user_data,
        lambda valid: valid.map(normalize_user_data),
        lambda normalized: normalized.map(enrich_user_data)
    )

def validate_user_data(user: dict):
    """Validate user data fields."""
    return validate_all([
        lambda u: Ok(u) if u.get('email') else Err("Email required"),
        lambda u: Ok(u) if '@' in u.get('email', '') else Err("Invalid email"),
        lambda u: Ok(u) if u.get('name') else Err("Name required"),
        lambda u: Ok(u) if u.get('age') and u['age'].isdigit() else Err("Valid age required"),
    ], user)

def normalize_user_data(user: dict):
    """Normalize data formats."""
    return {
        'email': user['email'].lower().strip(),
        'name': user['name'].strip(),
        'age': int(user['age']),
        'department': user.get('department', 'General').strip()
    }

def enrich_user_data(user: dict):
    """Add computed fields."""
    return {
        **user,
        'full_name': user['name'],
        'is_adult': user['age'] >= 18,
        'email_domain': user['email'].split('@')[1]
    }

def filter_valid_results(results):
    """Filter out errors, keep only valid users."""
    return [r.unwrap() for r in results if r.is_ok()]

def save_users_to_db(users):
    """Load: Save to database (simplified)."""
    # In real code, this would use your ORM/database library
    saved_count = len(users)
    return Ok(f"Saved {saved_count} users")

# Usage
result = process_user_csv('users.csv')
# Ok("Saved 95 users") or Err("File not found: users.csv")
```

## Data Validation Pipeline

For validating and processing form data or API inputs:

```python
from fptk.core.func import pipe
from fptk.adt.result import Ok, Err
from fptk.validate import validate_all

def validate_and_process_form(form_data: dict):
    """Validate form data and process if valid."""
    return pipe(
        form_data,
        validate_form,
        lambda valid: valid.bind(sanitize_data),
        lambda clean: clean.bind(save_form_data),
        lambda saved: saved.map(lambda _: {"status": "success", "id": saved.unwrap()})
    )

def validate_form(data: dict):
    """Comprehensive form validation."""
    return validate_all([
        # Required fields
        lambda d: Ok(d) if d.get('name') else Err("Name is required"),
        lambda d: Ok(d) if d.get('email') else Err("Email is required"),

        # Format validation
        lambda d: Ok(d) if '@' in d.get('email', '') else Err("Invalid email format"),
        lambda d: Ok(d) if len(d.get('name', '')) >= 2 else Err("Name too short"),

        # Business rules
        lambda d: Ok(d) if not d.get('age') or (isinstance(d['age'], int) and 13 <= d['age'] <= 120)
                   else Err("Age must be between 13 and 120"),
    ], data)

def sanitize_data(data: dict):
    """Clean and normalize data."""
    return Ok({
        'name': data['name'].strip(),
        'email': data['email'].lower().strip(),
        'age': data.get('age'),
        'newsletter': data.get('newsletter', False)
    })

def save_form_data(data: dict):
    """Save to database (simplified)."""
    # Simulate database save
    user_id = hash(data['email']) % 10000  # Fake ID generation
    return Ok(user_id)

# Usage
form_result = validate_and_process_form({
    'name': '  John Doe  ',
    'email': 'JOHN@EXAMPLE.COM',
    'age': 25,
    'newsletter': True
})
# Ok({"status": "success", "id": 1234})
```

## Batch Processing with Error Handling

Process large datasets in batches while handling errors gracefully:

```python
from fptk.core.func import pipe
from fptk.adt.result import Ok, Err
from fptk.iter.lazy import chunk
from fptk.async_tools import gather_results_accumulate
import asyncio

async def process_large_dataset(items, batch_size=100):
    """Process items in batches with error accumulation."""
    return pipe(
        items,
        lambda xs: chunk(xs, batch_size),  # Split into batches
        lambda batches: map(lambda batch: process_batch_async(batch), batches),
        lambda tasks: asyncio.gather(*tasks),  # Run all batches concurrently
        lambda results: aggregate_batch_results(results)
    )

async def process_batch_async(batch):
    """Process a single batch asynchronously."""
    tasks = [process_item_async(item) for item in batch]
    return await gather_results_accumulate(tasks)

async def process_item_async(item):
    """Process individual item (simplified)."""
    # Simulate async processing with potential errors
    if item.get('status') == 'invalid':
        return Err(f"Invalid item: {item['id']}")
    # Simulate processing time
    await asyncio.sleep(0.01)
    return Ok(f"Processed {item['id']}")

def aggregate_batch_results(batch_results):
    """Combine results from all batches."""
    all_successes = []
    all_errors = []

    for batch_result in batch_results:
        if batch_result.is_ok():
            successes = batch_result.unwrap()
            all_successes.extend(successes)
        else:
            errors = batch_result.unwrap_err()
            all_errors.extend(errors)

    if all_errors:
        return Err({
            'processed': len(all_successes),
            'errors': all_errors
        })
    else:
        return Ok({
            'processed': len(all_successes),
            'message': 'All items processed successfully'
        })

# Usage
items = [{'id': i, 'status': 'valid' if i % 10 != 0 else 'invalid'}
         for i in range(1000)]

result = asyncio.run(process_large_dataset(items, batch_size=50))
# Ok({"processed": 900, "message": "All items processed successfully"})
# or Err({"processed": 900, "errors": ["Invalid item: 10", "Invalid item: 20", ...]})
```

## Data Transformation Chains

Build reusable transformation pipelines:

```python
from fptk.core.func import pipe, compose
from fptk.adt.result import Ok, Err

# Define reusable transformations
strip_strings = lambda data: {k: v.strip() if isinstance(v, str) else v
                             for k, v in data.items()}

lowercase_emails = lambda data: {**data, 'email': data['email'].lower()}

add_timestamps = lambda data: {**data, 'created_at': datetime.now()}

validate_required = lambda fields: lambda data: pipe(
    fields,
    lambda fs: all(data.get(f) for f in fs),
    lambda valid: Ok(data) if valid else Err(f"Missing required fields: {fields}")
)

# Compose transformation pipeline
process_user_input = compose(
    add_timestamps,
    lowercase_emails,
    strip_strings
)

# Use in validation pipeline
def save_user_form(form_data):
    return pipe(
        form_data,
        process_user_input,
        lambda processed: validate_required(['name', 'email'])(processed),
        lambda valid: valid.bind(save_to_database)
    )

# Usage
result = save_user_form({
    'name': '  Alice Smith  ',
    'email': 'ALICE@EXAMPLE.COM'
})
```

These recipes show how fptk helps build robust, maintainable data processing pipelines with clear error handling and composable transformations.