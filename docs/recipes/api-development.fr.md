# Développement d'API

Ce guide montre comment utiliser les patterns fptk pour construire des API web robustes. Nous couvrirons les pipelines de traitement des requêtes, la gestion des erreurs, les opérations de base de données, les endpoints asynchrones et les middleware.

## Pourquoi des patterns fonctionnels pour les API ?

Le code d'API est particulièrement sujet à certains problèmes :

- **Gestion des erreurs en spaghetti** : des blocs try/except partout, des réponses d'erreur inconsistantes
- **Échecs cachés** : des fonctions qui peuvent échouer mais ne le rendent pas évident
- **Difficile à tester** : des handlers qui font trop de choses, fortement couplés aux frameworks

Les patterns fonctionnels aident en :

- Rendant la gestion des erreurs explicite et composable
- Séparant les responsabilités en petites fonctions testables
- Créant un flux de données cohérent à travers des pipelines

## Pipeline de traitement des requêtes

Une requête API passe typiquement par plusieurs étapes : parse → validate → process → respond. C'est naturellement adapté à `pipe` :

```python
from fptk.core.func import pipe, try_catch
from fptk.adt.result import Ok, Err
from fptk.validate import validate_all
import json

def handle_user_creation(request_body: str):
    """Complete pipeline for creating a user via API."""
    return pipe(
        request_body,
        parse_json,
        lambda r: r.bind(validate_request),
        lambda r: r.bind(create_user),
        lambda r: r.bind(send_welcome_email),
        lambda r: r.map(format_response)
    )

def parse_json(body: str):
    """Parse JSON, returning Result instead of raising."""
    return try_catch(json.loads)(body)

def validate_request(data: dict):
    """Validate with all errors accumulated."""
    return validate_all([
        lambda d: Ok(d) if d.get('name') else Err("Name required"),
        lambda d: Ok(d) if '@' in d.get('email', '') else Err("Invalid email"),
    ], data)

def create_user(data: dict):
    """Create user in database."""
    user_id = hash(data['email']) % 10000
    return Ok({
        'id': user_id,
        'name': data['name'],
        'email': data['email']
    })

def send_welcome_email(user: dict):
    """Send email (side effect at the edge)."""
    # In real code: email_service.send(...)
    return Ok(user)

def format_response(user: dict):
    """Format successful response."""
    return {'status': 'success', 'data': {'user': user}}
```

Chaque fonction fait une seule chose. Le pipeline rend le flux évident. Les erreurs se propagent automatiquement.

## Réponses d'erreur cohérentes

Les API ont besoin d'un formatage d'erreur cohérent. Utilisez `map_err` pour transformer les erreurs en un format standard :

```python
from fptk.adt.result import Ok, Err

def handle_request(request):
    return pipe(
        request,
        authenticate,
        lambda r: r.bind(authorize),
        lambda r: r.bind(process),
        lambda r: r.match(
            ok=lambda data: {'status': 'success', 'data': data},
            err=format_error
        )
    )

def authenticate(request):
    token = request.get('headers', {}).get('Authorization')
    if not token:
        return Err({'type': 'auth', 'message': 'Missing token'})
    if token != 'valid-token':
        return Err({'type': 'auth', 'message': 'Invalid token'})
    return Ok(request)

def authorize(request):
    if request.get('method') == 'DELETE':
        return Err({'type': 'forbidden', 'message': 'Admin required'})
    return Ok(request)

def process(request):
    return Ok({'result': 'processed'})

def format_error(error):
    """Convert internal errors to API response format."""
    status_codes = {
        'auth': 401,
        'forbidden': 403,
        'validation': 400,
        'not_found': 404,
    }
    return {
        'status': 'error',
        'code': status_codes.get(error['type'], 500),
        'message': error['message']
    }
```

## Opérations de base de données

Le code de base de données est l'endroit où `try_catch` et `Result` brillent vraiment :

```python
from fptk.core.func import pipe, try_catch
from fptk.adt.result import Ok, Err

def get_user_profile(user_id: int):
    """Get user with posts, handling all possible failures."""
    return pipe(
        user_id,
        validate_id,
        lambda r: r.bind(fetch_user),
        lambda r: r.bind(fetch_posts),
        lambda r: r.map(combine_data)
    )

def validate_id(user_id):
    if not isinstance(user_id, int) or user_id <= 0:
        return Err({'type': 'validation', 'message': 'Invalid user ID'})
    return Ok(user_id)

def fetch_user(user_id: int):
    """Wrap database call in Result."""
    def query():
        user = db.users.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        return user

    return try_catch(query)().map_err(
        lambda e: {'type': 'not_found', 'message': str(e)}
    )

def fetch_posts(user):
    """Fetch related data."""
    def query():
        return db.posts.filter(user_id=user['id'])

    return try_catch(query)().map(
        lambda posts: {'user': user, 'posts': posts}
    ).map_err(
        lambda e: {'type': 'database', 'message': str(e)}
    )

def combine_data(data):
    return {
        'profile': data['user'],
        'posts': data['posts'],
        'post_count': len(data['posts'])
    }
```

## Endpoints asynchrones

Pour les opérations asynchrones, utilisez `gather_results` pour gérer plusieurs tâches concurrentes :

```python
from fptk.core.func import async_pipe
from fptk.adt.result import Ok, Err
from fptk.async_tools import gather_results

async def handle_batch_creation(requests: list):
    """Create multiple users concurrently."""
    return await async_pipe(
        requests,
        validate_batch,
        lambda r: gather_results([create_user_async(req) for req in r]),
        lambda r: r.map(format_batch_response)
    )

def validate_batch(requests):
    if not isinstance(requests, list):
        return Err("Request must be a list")
    if len(requests) > 100:
        return Err("Maximum 100 items per batch")
    return Ok(requests)

async def create_user_async(data):
    """Async user creation."""
    if not data.get('email'):
        return Err(f"Missing email: {data}")

    # Simulate async I/O
    await asyncio.sleep(0.01)

    return Ok({
        'id': hash(data['email']) % 10000,
        'email': data['email']
    })

def format_batch_response(users):
    return {'created': len(users), 'users': users}
```

## Pattern middleware

Les middleware se composent naturellement avec des fonctions d'ordre supérieur :

```python
def with_auth(handler):
    """Authentication middleware."""
    def wrapper(request):
        return authenticate(request).bind(handler)
    return wrapper

def with_logging(handler):
    """Logging middleware (side effect)."""
    def wrapper(request):
        print(f"→ {request['method']} {request['path']}")
        result = handler(request)
        print(f"← {result}")
        return result
    return wrapper

def with_error_handling(handler):
    """Ensure errors are formatted consistently."""
    def wrapper(request):
        return handler(request).match(
            ok=lambda data: {'status': 'success', 'data': data},
            err=lambda e: {'status': 'error', 'error': e}
        )
    return wrapper

# Compose middleware (applied bottom-to-top)
@with_error_handling
@with_logging
@with_auth
def get_user(request):
    user_id = request['params']['id']
    return fetch_user(int(user_id))
```

## Points clés à retenir

1. **Utilisez `pipe` pour le flux des requêtes** : Rend les étapes explicites et faciles à modifier
2. **Utilisez `Result` pour toutes les opérations qui peuvent échouer** : Pas d'exceptions cachées
3. **Utilisez `validate_all` pour la validation des entrées** : Affiche toutes les erreurs en une fois
4. **Utilisez `try_catch` pour encapsuler les appels externes** : Base de données, API, E/S fichier
5. **Gardez les effets de bord aux extrémités** : Logique pure au milieu, E/S aux frontières
6. **Composez les middleware avec des fonctions d'ordre supérieur** : Séparation claire des responsabilités
