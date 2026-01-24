# Concepts Fondamentaux

Ce guide explique les idées principales derrière fptk sans trop entrer dans la théorie. Nous nous concentrerons sur l'utilisation pratique avec des exemples concrets.

## Les Fonctions comme Blocs de Construction

fptk traite les fonctions comme des blocs de construction réutilisables que vous pouvez combiner de différentes manières.

### pipe() : Flux de Données Linéaire

`pipe()` fait passer les données à travers des fonctions en séquence :

```python
from fptk.core.func import pipe

def process_user_data(raw_data):
    return pipe(
        raw_data,
        parse_json,      # Step 1: parse
        validate_user,   # Step 2: validate
        save_to_db,      # Step 3: save
        send_welcome     # Step 4: notify
    )
```

**Avantages :**

- Facile à lire (de haut en bas)
- Facile d'ajouter/supprimer des étapes
- Facile de tester les étapes individuellement

### compose() : Construction de Fonctions

`compose()` combine des fonctions en nouvelles fonctions :

```python
from fptk.core.func import compose

# Create a new function from existing ones
process_and_save = compose(save_to_db, validate_user, parse_json)

# Use it
result = process_and_save(raw_data)
```

Note : `compose` applique les fonctions de droite à gauche : `compose(f, g)(x)` = `f(g(x))`.

### curry() : Appels de Fonctions Flexibles

`curry()` vous permet d'appeler des fonctions partiellement :

```python
from fptk.core.func import curry

def send_email(to, subject, body):
    # Send email logic
    pass

# Create specialized functions
send_support_email = curry(send_email)("support@company.com")
notify_user = send_support_email("Welcome!")

# Use them
notify_user("Welcome to our platform!")
```

## Gérer les Données Manquantes avec Option

Le `None` de Python est source d'erreurs. L'`Option` de fptk rend l'absence explicite.

### Utilisation Basique d'Option

```python
from fptk.adt.option import Some, NOTHING, from_nullable

# Convert potentially None values
name = from_nullable(user.get('name'))  # Some("Alice") or NOTHING

# Handle absence safely
display_name = name.map(lambda n: n.upper()).unwrap_or("Anonymous")
```

### Chaîner les Opérations Optionnelles

```python
def get_full_name(user):
    return (
        from_nullable(user.get('first_name'))
        .zip(from_nullable(user.get('last_name')))
        .map(lambda names: f"{names[0]} {names[1]}")
        .or_else(lambda: from_nullable(user.get('display_name')))
        .unwrap_or('Anonymous')
    )

get_full_name({'first_name': 'John', 'last_name': 'Doe'})  # "John Doe"
get_full_name({'display_name': 'Johnny'})                   # "Johnny"
get_full_name({})                                           # "Anonymous"
```

**Opérations Clés :**

| Méthode | Description |
|---------|-------------|
| `map(f)` | Transforme la valeur si présente |
| `bind(f)` | Chaîne des opérations qui retournent Option |
| `zip(other)` | Combine deux Options en tuple |
| `or_else(f)` | Fournit une Option de secours |
| `unwrap_or(default)` | Obtient la valeur ou la valeur par défaut |

## Gestion des Erreurs avec Result

Les exceptions sont excellentes pour les erreurs inattendues, mais pour les échecs attendus (validation, parsing, etc.), `Result` est plus clair.

### Utilisation Basique de Result

```python
from fptk.adt.result import Ok, Err, Result

def divide(a: int, b: int) -> Result[int, str]:
    if b == 0:
        return Err("Division by zero")
    return Ok(a // b)

result = divide(10, 2)  # Ok(5)
error = divide(10, 0)   # Err("Division by zero")
```

### Chaîner les Results

```python
def process_payment(amount, card_number):
    return (
        validate_amount(amount)
        .bind(lambda amt: validate_card(card_number))
        .bind(lambda card: charge_card(amount, card))
    )

# Either Ok(success_data) or Err(error_message)
result = process_payment(100, "4111111111111111")
```

**Opérations Clés :**

| Méthode | Description |
|---------|-------------|
| `map(f)` | Transforme la valeur de succès |
| `bind(f)` | Chaîne des opérations retournant Result |
| `map_err(f)` | Transforme l'erreur |
| `unwrap_or(default)` | Obtient la valeur ou la valeur par défaut |

## Travailler avec les Collections

fptk fournit des utilitaires paresseux pour traiter les collections efficacement.

### Traitement Paresseux

```python
from fptk.core.func import pipe
from fptk.iter.lazy import map_iter, filter_iter

# Process large datasets without loading everything
def process_logs(logs):
    return pipe(
        logs,
        lambda ls: filter_iter(lambda log: log['level'] == 'ERROR', ls),
        lambda ls: map_iter(lambda log: log['message'], ls),
        list
    )
```

### Groupement et Découpage

```python
from fptk.iter.lazy import group_by_key, chunk

# Group data by category (input must be sorted by key)
grouped = dict(group_by_key(users, lambda u: u['department']))

# Process in batches
for user_batch in chunk(users, 10):
    process_batch(user_batch)
```

## Opérations Asynchrones

Gérez les opérations concurrentes avec une gestion d'erreurs appropriée.

### Rassembler les Results

```python
from fptk.async_tools import gather_results

async def fetch_user_data(user_ids):
    tasks = [fetch_user_api(uid) for uid in user_ids]
    # Returns Ok([user_data]) or Err(first_error)
    return await gather_results(tasks)
```

### Pipelines Asynchrones

```python
from fptk.core.func import async_pipe

async def process_request(request):
    return await async_pipe(
        request,
        parse_async,
        validate_async,
        save_async,
        notify_async
    )
```

## Validation

Accumulez plusieurs erreurs de validation au lieu d'échouer à la première.

```python
from fptk.adt.result import Ok, Err
from fptk.validate import validate_all

def validate_user(user):
    return validate_all([
        lambda u: Ok(u) if u.get('email') else Err("Email required"),
        lambda u: Ok(u) if '@' in u.get('email', '') else Err("Invalid email"),
        lambda u: Ok(u) if len(u.get('password', '')) >= 8 else Err("Password too short")
    ], user)

validate_user({'email': 'invalid', 'password': 'short'})
# Err(NonEmptyList("Invalid email", "Password too short"))
```

## Assembler le Tout

Voici un exemple complet combinant plusieurs concepts :

```python
from fptk.core.func import pipe
from fptk.adt.result import Ok, Err
from fptk.validate import validate_all

def process_registration(data):
    return pipe(
        data,
        validate_registration,
        lambda valid: valid.bind(save_user),
        lambda saved: saved.bind(send_welcome_email),
        lambda result: result.map(lambda user: {
            'user_id': user['id'],
            'message': 'Registration successful'
        })
    )

def validate_registration(data):
    return validate_all([
        lambda d: Ok(d) if d.get('email') else Err("Email required"),
        lambda d: Ok(d) if d.get('password') else Err("Password required"),
    ], data)

# Usage
result = process_registration({
    'email': 'user@example.com',
    'password': 'secure123'
})
# Ok({'user_id': 123, 'message': 'Registration successful'})
```

Cet exemple montre comment les concepts de fptk fonctionnent ensemble pour créer un code robuste et lisible.
