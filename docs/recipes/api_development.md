# API Development Recipes

This guide shows how to use fptk for building robust web APIs with proper error handling, validation, and data transformation.

## Request Processing Pipeline

Build a complete request processing pipeline for a REST API:

```python
from fptk.core.func import pipe
from fptk.adt.result import Ok, Err
from fptk.validate import validate_all
from fptk.core.func import try_catch
import json

def handle_user_creation(request_body: str):
    """Complete pipeline for creating a user via API."""
    return pipe(
        request_body,
        parse_request_json,      # Parse JSON
        lambda parsed: parsed.bind(validate_user_request),  # Validate
        lambda valid: valid.bind(create_user_in_db),        # Create user
        lambda user: user.bind(send_welcome_email),         # Send email
        lambda result: result.map(format_success_response)  # Format response
    )

def parse_request_json(body: str):
    """Parse JSON request body."""
    return try_catch(json.loads)(body)

def validate_user_request(data: dict):
    """Validate user creation request."""
    return validate_all([
        lambda d: Ok(d) if isinstance(d.get('name'), str) and d['name'].strip()
                   else Err("Name must be a non-empty string"),
        lambda d: Ok(d) if isinstance(d.get('email'), str) and '@' in d['email']
                   else Err("Valid email is required"),
        lambda d: Ok(d) if not d.get('age') or isinstance(d['age'], int)
                   else Err("Age must be an integer"),
    ], data)

def create_user_in_db(user_data: dict):
    """Create user in database (simplified)."""
    # In real code, this would use your database library
    user_id = hash(user_data['email']) % 10000
    return Ok({
        'id': user_id,
        'name': user_data['name'],
        'email': user_data['email'],
        'age': user_data.get('age'),
        'created_at': '2024-01-01T00:00:00Z'
    })

def send_welcome_email(user: dict):
    """Send welcome email (simplified)."""
    # In real code, this would use your email service
    print(f"Sending welcome email to {user['email']}")
    return Ok(user)

def format_success_response(user: dict):
    """Format successful response."""
    return {
        'status': 'success',
        'data': {
            'user': user,
            'message': 'User created successfully'
        }
    }

# Usage
request_body = json.dumps({
    'name': 'John Doe',
    'email': 'john@example.com',
    'age': 30
})

result = handle_user_creation(request_body)
# Ok({'status': 'success', 'data': {'user': {...}, 'message': '...'}})
```

## Error Response Handling

Create consistent error responses across your API:

```python
from fptk.core.func import pipe
from fptk.adt.result import Ok, Err

def handle_api_request(request):
    """Generic API request handler with consistent error formatting."""
    return pipe(
        request,
        authenticate_request,
        lambda auth: auth.bind(authorize_request),
        lambda auth: auth.bind(process_business_logic),
        lambda result: result.map(format_success_response),
        lambda response: response.or_else(format_error_response)
    )

def authenticate_request(request):
    """Authenticate the request."""
    token = request.headers.get('Authorization')
    if not token:
        return Err({'type': 'authentication', 'message': 'Missing token'})
    if not is_valid_token(token):
        return Err({'type': 'authentication', 'message': 'Invalid token'})
    return Ok(request)

def authorize_request(request):
    """Authorize the request."""
    user = get_user_from_request(request)
    if not user:
        return Err({'type': 'authorization', 'message': 'User not found'})

    if request.method == 'DELETE' and not user.get('is_admin'):
        return Err({'type': 'authorization', 'message': 'Admin access required'})

    return Ok(request)

def process_business_logic(request):
    """Process the actual business logic."""
    # This would vary based on the endpoint
    return Ok({'data': 'processed'})

def format_success_response(data):
    """Format successful API response."""
    return {
        'status': 'success',
        'data': data
    }

def format_error_response(error):
    """Format error response consistently."""
    error_type = error.get('type', 'unknown')
    status_codes = {
        'authentication': 401,
        'authorization': 403,
        'validation': 400,
        'not_found': 404,
        'unknown': 500
    }

    return {
        'status': 'error',
        'error': {
            'type': error_type,
            'message': error.get('message', 'An error occurred'),
            'code': status_codes.get(error_type, 500)
        }
    }

# Usage
request = {
    'method': 'GET',
    'path': '/users',
    'headers': {'Authorization': 'valid-token'}
}

response = handle_api_request(request)
# Either success or consistently formatted error response
```

## Database Operations with Error Handling

Handle database operations safely:

```python
from fptk.core.func import pipe
from fptk.adt.result import Ok, Err
from fptk.core.func import try_catch

def get_user_profile(user_id: int):
    """Get user profile with proper error handling."""
    return pipe(
        user_id,
        validate_user_id,
        lambda valid_id: valid_id.bind(fetch_user_from_db),
        lambda user: user.bind(fetch_user_posts),
        lambda data: data.map(combine_user_data)
    )

def validate_user_id(user_id):
    """Validate user ID."""
    if not isinstance(user_id, int) or user_id <= 0:
        return Err({'type': 'validation', 'message': 'Invalid user ID'})
    return Ok(user_id)

def fetch_user_from_db(user_id: int):
    """Fetch user from database."""
    def db_query():
        # Simulate database query
        users_db = {
            1: {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'},
            2: {'id': 2, 'name': 'Bob', 'email': 'bob@example.com'}
        }
        user = users_db.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        return user

    return try_catch(db_query)().map_err(lambda e: {
        'type': 'not_found',
        'message': str(e)
    })

def fetch_user_posts(user):
    """Fetch user's posts."""
    def posts_query():
        # Simulate posts query
        posts_db = {
            1: [{'id': 1, 'title': 'Hello World', 'content': '...'}],
            2: [{'id': 2, 'title': 'My Post', 'content': '...'}]
        }
        return posts_db.get(user['id'], [])

    return try_catch(posts_query)().map(lambda posts: {
        'user': user,
        'posts': posts
    }).map_err(lambda e: {
        'type': 'database',
        'message': f"Error fetching posts: {e}"
    })

def combine_user_data(data):
    """Combine user and posts data."""
    user = data['user']
    posts = data['posts']
    return {
        'profile': user,
        'posts': posts,
        'stats': {
            'post_count': len(posts)
        }
    }

# Usage
result = get_user_profile(1)
# Ok({'profile': {...}, 'posts': [...], 'stats': {'post_count': 1}})
```

## Async API Endpoints

Handle async operations in API endpoints:

```python
from fptk.core.func import async_pipe
from fptk.adt.result import Ok, Err
from fptk.async_tools import gather_results
import asyncio

async def handle_batch_user_creation(user_requests):
    """Create multiple users asynchronously."""
    return await async_pipe(
        user_requests,
        validate_batch_request,
        lambda valid: gather_results([
            create_single_user_async(req) for req in valid
        ]),
        lambda results: results.map(format_batch_response)
    )

def validate_batch_request(requests):
    """Validate batch request."""
    if not isinstance(requests, list):
        return Err("Request must be a list")
    if len(requests) > 100:
        return Err("Maximum 100 users per batch")
    return Ok(requests)

async def create_single_user_async(user_data):
    """Create a single user asynchronously."""
    # Simulate async database and email operations
    await asyncio.sleep(0.1)  # Simulate I/O

    # Validate user data
    if not user_data.get('email'):
        return Err(f"Missing email for user: {user_data}")

    # Simulate database save
    user_id = hash(user_data['email']) % 10000

    # Simulate email sending
    await asyncio.sleep(0.05)

    return Ok({
        'id': user_id,
        'name': user_data['name'],
        'email': user_data['email']
    })

def format_batch_response(results):
    """Format batch response."""
    return {
        'created': len(results),
        'users': results
    }

# Usage
user_requests = [
    {'name': 'Alice', 'email': 'alice@example.com'},
    {'name': 'Bob', 'email': 'bob@example.com'},
    {'name': 'Charlie', 'email': 'charlie@example.com'}
]

result = asyncio.run(handle_batch_user_creation(user_requests))
# Ok({'created': 3, 'users': [{'id': 123, 'name': 'Alice', ...}, ...]})
```

## Middleware Pattern

Create reusable middleware for authentication, logging, etc.:

```python
from fptk.core.func import pipe
from fptk.adt.result import Ok, Err

def with_authentication(handler):
    """Authentication middleware."""
    def authenticated_handler(request):
        return pipe(
            request,
            authenticate_request,
            lambda auth_req: auth_req.bind(handler)
        )
    return authenticated_handler

def with_logging(handler):
    """Logging middleware."""
    def logged_handler(request):
        print(f"Request: {request['method']} {request['path']}")
        result = handler(request)
        print(f"Response: {result}")
        return result
    return logged_handler

def with_error_handling(handler):
    """Error handling middleware."""
    def error_handled_handler(request):
        return pipe(
            request,
            handler,
            lambda response: response.or_else(lambda error: {
                'status': 'error',
                'error': error
            })
        )
    return error_handled_handler

# Compose middleware
@with_error_handling
@with_logging
@with_authentication
def get_user_handler(request):
    """Actual handler with middleware applied."""
    user_id = request['params']['id']
    return pipe(
        user_id,
        lambda uid: int(uid) if uid.isdigit() else None,
        lambda uid: Ok(uid) if uid else Err('Invalid user ID'),
        lambda valid_id: valid_id.bind(fetch_user)
    )

# Usage
request = {
    'method': 'GET',
    'path': '/users/123',
    'headers': {'Authorization': 'valid-token'},
    'params': {'id': '123'}
}

response = get_user_handler(request)
```

These patterns help you build robust, maintainable APIs with clear error handling and composable request processing pipelines.