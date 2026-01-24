# Guide de migration

Ce guide détaille comment intégrer progressivement les patrons de fptk à votre code Python existant. Chaque étape s'appuie sur la précédente, vous permettant de commencer modestement et d'ajouter des fonctionnalités au fur et à mesure.

## Niveau 1 : Composition de fonctions

**Point de départ** — Remplacez les appels de fonctions imbriqués par `pipe()`.

### Avant : Des appels imbriqués

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

### Après : Un pipeline linéaire

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

-   ✅ Lecture plus intuitive (de haut en bas)
-   ✅ Ajout/suppression d'étapes simplifiée
-   ✅ Test unitaire de chaque fonction facilité

## Niveau 2 : Gestion des erreurs avec Result

**Intégrez une gestion des erreurs robuste** — Remplacez les exceptions et les vérifications de `None` par `Result`.

### Avant : Une gestion d'exceptions classique

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

### Après : Un flux basé sur Result

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
    return Ok(email) if "@" in email else Err("Email invalide")

def hash_password_safe(password):
    return try_catch(lambda: bcrypt.hashpw(password.encode(), bcrypt.gensalt()))()

def save_to_db_safe(email, hashed):
    return try_catch(lambda: db.save(email, hashed))()
```

**Avantages :**

-   ✅ Types d'erreurs explicites
-   ✅ Gestion des erreurs composable
-   ✅ Fin de la propagation d'exceptions

## Niveau 3 : Valeurs optionnelles avec Option

**Gérez les données manquantes en toute sécurité** — Remplacez les vérifications de `None` par `Option`.

### Avant : Des vérifications de None omniprésentes

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

### Après : Un chaînage avec Option

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
        .unwrap_or('Anonyme')
    )
```

**Avantages :**

-   ✅ Élimination des bugs liés à `None`
-   ✅ Gestion explicite de l'absence de valeur
-   ✅ Opérations composables

## Niveau 4 : Accumulation de validation

**Collectez toutes les erreurs en une fois** — Remplacez la validation qui s'arrête à la première erreur (fail-fast) par l'accumulation de toutes les erreurs.

### Avant : Une validation qui s'arrête à la première erreur

```python
def validate_user(user):
    if not user.get('email'):
        return False, "Email requis"
    if '@' not in user['email']:
        return False, "Email invalide"
    if len(user.get('password', '')) < 8:
        return False, "Mot de passe trop court"
    return True, None
```

### Après : L'accumulation des erreurs

```python
from fptk.adt.result import Ok, Err
from fptk.validate import validate_all

def validate_user(user):
    return validate_all([
        lambda u: Ok(u) if u.get('email') else Err("Email requis"),
        lambda u: Ok(u) if '@' in u.get('email', '') else Err("Email invalide"),
        lambda u: Ok(u) if len(u.get('password', '')) >= 8 else Err("Mot de passe trop court"),
    ], user)
```

**Avantages :**

-   ✅ Toutes les erreurs affichées simultanément
-   ✅ Meilleure expérience utilisateur
-   ✅ API de validation cohérente

<h2>Niveau 5 : Collections paresseuses</h2>

**Traitez efficacement les grands ensembles de données** — Remplacez les listes par des itérateurs paresseux (lazy iterators).

### Avant : Un chargement complet en mémoire

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

### Après : Un traitement paresseux

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

-   ✅ Efficace en mémoire pour les grands jeux de données
-   ✅ Étapes de traitement composables
-   ✅ Traitement uniquement des données nécessaires

<h2>Niveau 6 : Opérations asynchrones</h2>

**Gérez la concurrence en toute sécurité** — Utilisez `gather_results` pour vos opérations asynchrones.

### Avant : Une coordination asynchrone manuelle

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

### Après : Une concurrence basée sur Result

```python
from fptk.async_tools import gather_results

async def fetch_user_data(user_ids):
    tasks = [fetch_user_api(uid) for uid in user_ids]
    return await gather_results(tasks)
```

**Avantages :**

-   ✅ Gestion des erreurs structurée
-   ✅ Code asynchrone épuré
-   ✅ Types d'erreurs cohérents

<h2>Patrons de migration courants</h2>

<h3>Conversion du code gérant les exceptions</h3>

```python
# Avant
def risky_operation(x):
    if x < 0:
        raise ValueError("Negative value")
    return x * 2

# Après
def risky_operation(x):
    return Ok(x * 2) if x >= 0 else Err("Valeur négative")
```

<h3>Conversion des fonctions retournant None</h3>

```python
# Avant
def find_user(user_id):
    return users_db.get(user_id)

# Après
from fptk.adt.option import from_nullable

def find_user(user_id):
    return from_nullable(users_db.get(user_id))
```

<h3>Conversion des fonctions de validation</h3>

```python
# Avant
def is_valid_email(email):
    return '@' in email

# Après
def validate_email(email):
    return Ok(email) if '@' in email else Err("Email invalide")
```

<h2>Stratégie de migration</h2>

1.  **Commencez modestement** : Intégrez `pipe()` à une seule fonction.
2.  **Ajoutez la gestion des erreurs** : Convertissez progressivement les fonctions basées sur les exceptions en utilisant `Result`.
3.  **Gérez les valeurs optionnelles** : Remplacez les vérifications de `None` par `Option`.
4.  **Passez à la vitesse supérieure** : Intégrez la validation, les opérations asynchrones et les patrons avancés selon vos besoins.

**Points clés à retenir :**

-   Pas besoin de tout convertir en une seule fois.
-   Chaque niveau apporte une amélioration concrète à votre code.
-   Une adoption partielle est déjà bénéfique.
-   Concentrez-vous d'abord sur les points sensibles de votre codebase.