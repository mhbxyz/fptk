# Développement d'API

Ce guide illustre comment utiliser les patrons de fptk pour concevoir des API web robustes. Nous aborderons les pipelines de traitement des requêtes, la gestion des erreurs, les interactions avec les bases de données, les points d'entrée (endpoints) asynchrones et l'usage de middlewares.

## Pourquoi adopter des patrons fonctionnels pour les API ?

Le code d'une API est souvent sujet à des problèmes récurrents :

-   **Une gestion d'erreurs confuse (spaghetti)** : des blocs `try/except` omniprésents et des réponses d'erreur disparates.
-   **Des échecs silencieux** : des fonctions qui peuvent échouer sans que cela soit explicite.
-   **Une difficulté de test** : des gestionnaires (handlers) surchargés et trop étroitement liés aux frameworks.

Les patrons fonctionnels apportent des solutions concrètes en :

-   Rendant la gestion des erreurs explicite et composable.
-   Découpant les responsabilités en petites fonctions testables.
-   Créant un flux de données cohérent grâce aux pipelines.

## Pipeline de traitement des requêtes

Le parcours d'une requête API suit généralement plusieurs étapes : analyse (parse) → validation → traitement → réponse. Ce flux se prête naturellement à l'usage de `pipe` :

```python
from fptk.core.func import pipe, try_catch
from fptk.adt.result import Ok, Err
from fptk.validate import validate_all
import json

def handle_user_creation(request_body: str):
    """Pipeline complet de création d'utilisateur via API."""
    return pipe(
        request_body,
        parse_json,
        lambda r: r.bind(validate_request),
        lambda r: r.bind(create_user),
        lambda r: r.bind(send_welcome_email),
        lambda r: r.map(format_response)
    )

def parse_json(body: str):
    """Analyse le JSON et renvoie un Result au lieu de lever une exception."""
    return try_catch(json.loads)(body)

def validate_request(data: dict):
    """Valide les données en accumulant toutes les erreurs détectées."""
    return validate_all([
        lambda d: Ok(d) if d.get('name') else Err("Nom requis"),
        lambda d: Ok(d) if '@' in d.get('email', '') else Err("Email invalide"),
    ], data)

def create_user(data: dict):
    """Simule la création d'un utilisateur en base de données."""
    user_id = hash(data['email']) % 10000
    return Ok({
        'id': user_id,
        'name': data['name'],
        'email': data['email']
    })

def send_welcome_email(user: dict):
    """Envoie un e-mail (effet de bord géré à la périphérie)."""
    # Dans un cas réel : email_service.send(...)
    return Ok(user)

def format_response(user: dict):
    """Formate la réponse en cas de succès."""
    return {'status': 'success', 'data': {'user': user}}
```

Chaque fonction est dédiée à une tâche unique. Le pipeline rend le flux limpide et les erreurs se propagent d'elles-mêmes.

## Réponses d'erreur cohérentes

La cohérence du formatage des erreurs est cruciale pour une API. Utilisez `map_err` pour normaliser vos erreurs :

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
    if not token :
        return Err({'type': 'auth', 'message': 'Jeton manquant'})
    if token != 'valid-token':
        return Err({'type': 'auth', 'message': 'Jeton invalide'})
    return Ok(request)

def authorize(request):
    if request.get('method') == 'DELETE':
        return Err({'type': 'forbidden', 'message': 'Droits administrateur requis'})
    return Ok(request)

def process(request):
    return Ok({'result': 'traité'})

def format_error(error):
    """Convertit les erreurs internes au format de réponse de l'API."""
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

Le code d'interaction avec la base de données est le terrain de prédilection de `try_catch` et `Result` :

```python
from fptk.core.func import pipe, try_catch
from fptk.adt.result import Ok, Err

def get_user_profile(user_id: int):
    """Récupère un utilisateur et ses publications, en gérant tous les échecs possibles."""
    return pipe(
        user_id,
        validate_id,
        lambda r: r.bind(fetch_user),
        lambda r: r.bind(fetch_posts),
        lambda r: r.map(combine_data)
    )

def validate_id(user_id):
    if not isinstance(user_id, int) or user_id <= 0:
        return Err({'type': 'validation', 'message': 'ID utilisateur invalide'})
    return Ok(user_id)

def fetch_user(user_id: int):
    """Encapsule l'appel à la base de données dans un Result."""
    def query():
        user = db.users.get(user_id)
        if not user:
            raise ValueError(f"Utilisateur {user_id} introuvable")
        return user

    return try_catch(query)().map_err(
        lambda e: {'type': 'not_found', 'message': str(e)}
    )

def fetch_posts(user):
    """Récupère les données associées."""
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

## Points d'entrée (endpoints) asynchrones

Pour les opérations asynchrones, privilégiez `gather_results` afin de gérer plusieurs tâches concurrentes :

```python
from fptk.core.func import async_pipe
from fptk.adt.result import Ok, Err
from fptk.async_tools import gather_results

async def handle_batch_creation(requests: list):
    """Crée plusieurs utilisateurs de manière concurrente."""
    return await async_pipe(
        requests,
        validate_batch,
        lambda r: gather_results([create_user_async(req) for req in r]),
        lambda r: r.map(format_batch_response)
    )

def validate_batch(requests):
    if not isinstance(requests, list):
        return Err("La requête doit être une liste")
    if len(requests) > 100:
        return Err("Maximum 100 éléments par lot")
    return Ok(requests)

async def create_user_async(data):
    """Création asynchrone d'un utilisateur."""
    if not data.get('email'):
        return Err(f"Email manquant : {data}")

    # Simule des E/S asynchrones
    await asyncio.sleep(0.01)

    return Ok({
        'id': hash(data['email']) % 10000,
        'email': data['email']
    })

def format_batch_response(users):
    return {'created': len(users), 'users': users}
```

## Patron (pattern) Middleware

Les middlewares se composent tout naturellement à l'aide de fonctions d'ordre supérieur :

```python
def with_auth(handler):
    """Middleware d'authentification."""
    def wrapper(request):
        return authenticate(request).bind(handler)
    return wrapper

def with_logging(handler):
    """Middleware de journalisation (effet de bord)."""
    def wrapper(request):
        print(f"→ {request['method']} {request['path']}")
        result = handler(request)
        print(f"← {result}")
        return result
    return wrapper

def with_error_handling(handler):
    """Garantit une mise en forme cohérente des erreurs."""
    def wrapper(request):
        return handler(request).match(
            ok=lambda data: {'status': 'success', 'data': data},
            err=lambda e: {'status': 'error', 'error': e}
        )
    return wrapper

# Composition des middlewares (appliquée du bas vers le haut)
@with_error_handling
@with_logging
@with_auth
def get_user(request):
    user_id = request['params']['id']
    return fetch_user(int(user_id))
```

## Points clés à retenir

1.  **Utilisez `pipe` pour orchestrer le flux des requêtes** : cela rend les étapes explicites et facilite toute modification ultérieure.
2.  **Adoptez `Result` pour toute opération susceptible d'échouer** : pour en finir avec les exceptions cachées.
3.  **Privilégiez `validate_all` pour la validation des entrées** : afin d'afficher toutes les erreurs en une seule fois.
4.  **Encapsulez les appels externes avec `try_catch`** : qu'il s'agisse de base de données, d'API ou d'E/S de fichiers.
5.  **Maintenez les effets de bord à la périphérie** : gardez une logique pure au centre, et gérez les E/S aux frontières.
6.  **Composez vos middlewares via des fonctions d'ordre supérieur** : pour une séparation nette des responsabilités.