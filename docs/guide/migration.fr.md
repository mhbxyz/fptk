# Guide de migration

Ce guide montre comment adopter progressivement les patrons fptk dans votre code Python existant. Chaque niveau s'appuie sur le précédent, vous pouvez donc commencer petit et ajouter des fonctionnalités selon vos besoins.

## Niveau 1 : Composition de fonctions

**Commencez ici** — Remplacez les appels de fonctions imbriqués par `pipe()`.

### Avant : Appels imbriqués

```python
def process_data(data):
    result = parse_json(data)
    if result:
        validated = validate_data(result)
        if validated:
            saved = save_to_db(validated)
            if saved:
                return format_response(saved)
    return None
```

### Après : Pipeline linéaire

```python
from fptk.core.func import pipe

def process_data(data):
    return pipe(
        data,
        parse_json,
        validate_data,
        save_to_db,
        format_response
    )
```

**Avantages :**

- Plus facile à lire (de haut en bas)
- Plus facile d'ajouter/supprimer des étapes
- Plus facile de tester les fonctions individuellement

## Niveau 2 : Gestion des erreurs avec Result

**Ajoutez une gestion d'erreurs appropriée** — Remplacez les exceptions et les vérifications de None par `Result`.

### Avant : Gestion des exceptions

```python
def create_user(email, password):
    try:
        if not validate_email(email):
            raise ValueError("Invalid email")
        hashed = hash_password(password)
        user_id = save_to_db(email, hashed)
        send_welcome_email(user_id)
        return user_id
    except Exception as e:
        log_error(e)
        return None
```

### Après : Flux basé sur Result

```python
from fptk.adt.result import Ok, Err
from fptk.core.func import pipe, try_catch

def create_user(email, password):
    return (
        validate_email_result(email)
        .bind(lambda _: hash_password_safe(password))
        .bind(lambda hashed: save_to_db_safe(email, hashed))
        .bind(send_welcome_email_safe)
    )

def validate_email_result(email):
    return Ok(email) if "@" in email else Err("Invalid email")

def hash_password_safe(password):
    return try_catch(lambda: bcrypt.hashpw(password.encode(), bcrypt.gensalt()))()

def save_to_db_safe(email, hashed):
    return try_catch(lambda: db.save(email, hashed))()
```

**Avantages :**

- Types d'erreurs explicites
- Gestion des erreurs composable
- Pas de propagation d'exceptions

## Niveau 3 : Valeurs optionnelles avec Option

**Gérez les données manquantes en toute sécurité** — Remplacez les vérifications de None par `Option`.

### Avant : Vérifications de None partout

```python
def get_display_name(user):
    if user.get('profile'):
        profile = user['profile']
        if profile.get('first_name') and profile.get('last_name'):
            return f"{profile['first_name']} {profile['last_name']}"
        elif profile.get('display_name'):
            return profile['display_name']
    return user.get('username', 'Anonymous')
```

### Après : Chaînage avec Option

```python
from fptk.adt.option import from_nullable

def get_display_name(user):
    return (
        from_nullable(user.get('profile'))
        .bind(lambda profile:
            from_nullable(profile.get('first_name'))
            .zip(from_nullable(profile.get('last_name')))
            .map(lambda names: f"{names[0]} {names[1]}")
            .or_else(lambda: from_nullable(profile.get('display_name')))
        )
        .or_else(lambda: from_nullable(user.get('username')))
        .unwrap_or('Anonymous')
    )
```

**Avantages :**

- Pas de bugs liés à None
- Gestion explicite de l'absence
- Opérations composables

## Niveau 4 : Accumulation de validation

**Collectez toutes les erreurs d'un coup** — Remplacez la validation fail-fast par l'accumulation d'erreurs.

### Avant : Validation fail-fast

```python
def validate_user(user):
    if not user.get('email'):
        return False, "Email required"
    if '@' not in user['email']:
        return False, "Invalid email"
    if len(user.get('password', '')) < 8:
        return False, "Password too short"
    return True, None
```

### Après : Accumuler les erreurs

```python
from fptk.adt.result import Ok, Err
from fptk.validate import validate_all

def validate_user(user):
    return validate_all([
        lambda u: Ok(u) if u.get('email') else Err("Email required"),
        lambda u: Ok(u) if '@' in u.get('email', '') else Err("Invalid email"),
        lambda u: Ok(u) if len(u.get('password', '')) >= 8 else Err("Password too short"),
    ], user)
```

**Avantages :**

- Toutes les erreurs affichées en une fois
- Meilleure expérience utilisateur
- API de validation cohérente

## Niveau 5 : Collections paresseuses

**Traitez les grands ensembles de données efficacement** — Remplacez les listes par des itérateurs paresseux.

### Avant : Tout charger en mémoire

```python
def process_logs(logs):
    errors = []
    for log in logs:
        if log['level'] == 'ERROR':
            parsed = parse_log_line(log['message'])
            if parsed:
                errors.append(parsed)
    return errors
```

### Après : Traitement paresseux

```python
from fptk.iter.lazy import map_iter, filter_iter

def process_logs(logs):
    return list(
        map_iter(parse_log_line,
            filter_iter(lambda log: log['level'] == 'ERROR', logs)
        )
    )
```

**Avantages :**

- Efficace en mémoire pour les grands ensembles de données
- Étapes de traitement composables
- Ne traite que ce dont vous avez besoin

## Niveau 6 : Opérations asynchrones

**Gérez la concurrence en toute sécurité** — Utilisez `gather_results` pour les opérations asynchrones.

### Avant : Coordination asynchrone manuelle

```python
async def fetch_user_data(user_ids):
    tasks = [fetch_user_api(uid) for uid in user_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    data = []
    for result in results:
        if isinstance(result, Exception):
            log_error(result)
        else:
            data.append(result)
    return data
```

### Après : Concurrence basée sur Result

```python
from fptk.async_tools import gather_results

async def fetch_user_data(user_ids):
    tasks = [fetch_user_api(uid) for uid in user_ids]
    return await gather_results(tasks)
```

**Avantages :**

- Gestion structurée des erreurs
- Code asynchrone propre
- Types d'erreurs cohérents

## Patrons de migration courants

### Conversion du code basé sur les exceptions

```python
# Before
def risky_operation(x):
    if x < 0:
        raise ValueError("Negative value")
    return x * 2

# After
def risky_operation(x):
    return Ok(x * 2) if x >= 0 else Err("Negative value")
```

### Conversion des fonctions retournant None

```python
# Before
def find_user(user_id):
    return users_db.get(user_id)

# After
from fptk.adt.option import from_nullable

def find_user(user_id):
    return from_nullable(users_db.get(user_id))
```

### Conversion des fonctions de validation

```python
# Before
def is_valid_email(email):
    return '@' in email

# After
def validate_email(email):
    return Ok(email) if '@' in email else Err("Invalid email")
```

## Stratégie de migration

1. **Commencez petit** : Commencez avec `pipe()` dans une seule fonction
2. **Ajoutez la gestion d'erreurs** : Convertissez progressivement les fonctions basées sur les exceptions vers `Result`
3. **Gérez les optionnels** : Remplacez les vérifications de None par `Option`
4. **Montez en puissance** : Ajoutez la validation, l'asynchrone et les patrons avancés selon vos besoins

**Rappelez-vous :**

- Vous n'avez pas besoin de tout convertir d'un coup
- Chaque niveau améliore votre code
- L'adoption partielle est précieuse
- Commencez par les points douloureux de votre base de code
