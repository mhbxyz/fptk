# Concepts fondamentaux

Ce guide explore les concepts fondamentaux de fptk, en privilégiant l'aspect pratique par des exemples concrets plutôt qu'une plongée théorique approfondie.

## Les fonctions comme briques de construction

fptk considère les fonctions comme des briques de construction réutilisables, modulables de diverses manières.

### pipe() : Flux de données linéaire

`pipe()` orchestre le passage de données à travers une séquence de fonctions :

```python
from fptk.core.func import pipe

def process_user_data(raw_data):
    return pipe(
        raw_data,
        parse_json,      # Étape 1 : analyse
        validate_user,   # Étape 2 : validation
        save_to_db,      # Étape 3 : sauvegarde
        send_welcome     # Étape 4 : notification
    )
```

**Avantages :**

-   Lecture intuitive (de haut en bas)
-   Ajout/suppression d'étapes simplifiée
-   Test unitaire aisé de chaque étape

### compose() : Construction de fonctions

`compose()` assemble des fonctions pour en créer de nouvelles :

```python
from fptk.core.func import compose

# Crée une nouvelle fonction à partir de fonctions existantes
process_and_save = compose(save_to_db, validate_user, parse_json)

# Utilisation
result = process_and_save(raw_data)
```

Note : `compose` applique les fonctions de droite à gauche, soit `compose(f, g)(x)` équivalent à `f(g(x))`.

### curry() : Appels de fonctions flexibles

`curry()` permet d'appeler des fonctions de manière partielle :

```python
from fptk.core.func import curry

def send_email(to, subject, body):
    # Logique d'envoi d'e-mail
    pass

# Crée des fonctions spécialisées
send_support_email = curry(send_email)("support@company.com")
notify_user = send_support_email("Bienvenue !")

# Utilisation
notify_user("Bienvenue sur notre plateforme !")
```

## Gérer les données manquantes avec Option

La valeur `None` en Python est souvent source d'erreurs. L'`Option` de fptk rend l'absence d'une valeur explicite.

### Utilisation basique d'Option

```python
from fptk.adt.option import Some, NOTHING, from_nullable

# Convertit les valeurs potentiellement None
name = from_nullable(user.get('name'))  # Some("Alice") ou NOTHING

# Gère l'absence en toute sécurité
display_name = name.map(lambda n: n.upper()).unwrap_or("Anonyme")
```

### Chaîner les opérations Optionnelles

```python
def get_full_name(user):
    return (
        from_nullable(user.get('first_name'))
        .zip(from_nullable(user.get('last_name')))
        .map(lambda names: f"{names[0]} {names[1]}")
        .or_else(lambda: from_nullable(user.get('display_name')))
        .unwrap_or('Anonyme')
    )

get_full_name({'first_name': 'John', 'last_name': 'Doe'})  # "John Doe"
get_full_name({'display_name': 'Johnny'})                   # "Johnny"
get_full_name({})                                           # "Anonyme"
```

**Opérations clés :**

| Méthode | Description |
|---------|-------------|
| `map(f)` | Transforme la valeur si elle est présente. |
| `bind(f)` | Enchaîne des opérations qui renvoient une `Option`. |
| `zip(other)` | Combine deux `Option` en un tuple. |
| `or_else(fallback)` | Propose une `Option` de repli en cas d'absence. |
| `unwrap_or(default)` | Récupère la valeur ou une valeur par défaut. |

## Gestion des erreurs avec Result

Les exceptions sont pertinentes pour les erreurs inattendues, mais `Result` apporte plus de clarté pour les échecs prévisibles (validation, analyse, etc.).

### Utilisation basique de Result

```python
from fptk.adt.result import Ok, Err, Result

def divide(a: int, b: int) -> Result[int, str]:
    if b == 0:
        return Err("Division par zéro")
    return Ok(a // b)

result = divide(10, 2)  # Ok(5)
error = divide(10, 0)   # Err("Division par zéro")
```

### Chaîner les Results

```python
def process_payment(amount, card_number):
    return (
        validate_amount(amount)
        .bind(lambda amt: validate_card(card_number))
        .bind(lambda card: charge_card(amount, card))
    )

# Renvoie soit Ok(success_data) soit Err(error_message)
result = process_payment(100, "4111111111111111")
```

**Opérations clés :**

| Méthode | Description |
|---------|-------------|
| `map(f)` | Transforme la valeur en cas de succès. |
| `bind(f)` | Enchaîne des opérations qui renvoient un `Result`. |
| `map_err(f)` | Modifie l'erreur en cas d'échec. |
| `unwrap_or(default)` | Récupère la valeur ou une valeur par défaut. |

## Travailler avec les collections

fptk propose des utilitaires d'itérateurs paresseux (lazy iterators) pour un traitement efficace des collections.

### Traitement paresseux

```python
from fptk.core.func import pipe
from fptk.iter.lazy import map_iter, filter_iter

# Traite les grands jeux de données sans tout charger en mémoire
def process_logs(logs):
    return pipe(
        logs,
        lambda ls: filter_iter(lambda log: log['level'] == 'ERROR', ls),
        lambda ls: map_iter(lambda log: log['message'], ls),
        list
    )
```

### Groupement et découpage

```python
from fptk.iter.lazy import group_by_key, chunk

# Regroupe les données par catégorie (l'entrée doit être triée par clé)
grouped = dict(group_by_key(users, lambda u: u['department']))

# Traite les données par lots
for user_batch in chunk(users, 10):
    process_batch(user_batch)
```

## Opérations asynchrones

Gérez les opérations concurrentes avec une gestion des erreurs structurée.

### Rassembler les Results

```python
from fptk.async_tools import gather_results

async def fetch_user_data(user_ids):
    tasks = [fetch_user_api(uid) for uid in user_ids]
    # Retourne Ok([user_data]) ou Err(première_erreur)
    return await gather_results(tasks)
```

### Pipelines asynchrones

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

Accumulez toutes les erreurs de validation au lieu de vous arrêter à la première.

```python
from fptk.adt.result import Ok, Err
from fptk.validate import validate_all

def validate_user(user):
    return validate_all([
        lambda u: Ok(u) if u.get('email') else Err("Email requis"),
        lambda u: Ok(u) if '@' in u.get('email', '') else Err("Email invalide"),
        lambda u: Ok(u) if len(u.get('password', '')) >= 8 else Err("Mot de passe trop court")
    ], user)

validate_user({'email': 'invalide', 'password': 'court'})
# Err(NonEmptyList("Email invalide", "Mot de passe trop court"))
```

## Assembler le tout

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
            'message': 'Enregistrement réussi'
        })
    )

def validate_registration(data):
    return validate_all([
        lambda d: Ok(d) if d.get('email') else Err("Email requis"),
        lambda d: Ok(d) if d.get('password') else Err("Mot de passe requis"),
    ], data)

# Utilisation
result = process_registration({
    'email': 'utilisateur@example.com',
    'password': 'secure123'
})
# Ok({'user_id': 123, 'message': 'Enregistrement réussi'})
```

Cet exemple illustre comment les différents concepts de fptk s'articulent pour créer un code robuste et lisible.