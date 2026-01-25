# Result

Le module `fptk.adt.result` propose le type `Result`, conçu pour modéliser les opérations susceptibles de réussir ou d'échouer. Plutôt que de lever des exceptions, `Result` rend les erreurs explicites, robustes et parfaitement composables.

## Concept : La Monade Result (ou Either)

En programmation fonctionnelle, `Result` (souvent appelée `Either` dans d'autres langages comme Haskell) représente l'issue d'un calcul faillible. Elle se décline en deux cas :

-   **`Ok(value)`** : le calcul a réussi et contient une valeur.
-   **`Err(error)`** : le calcul a échoué et contient une erreur.

Cette approche apporte des avantages majeurs :

-   **Gestion explicite des erreurs** : la signature de la fonction vous avertit qu'un échec est possible.
-   **Chemins d'erreur composables** : enchaînez vos opérations et gérez l'ensemble des erreurs potentielles à la fin de la chaîne.
-   **Flux de contrôle limpide** : fini les exceptions invisibles qui traversent votre pile d'appels.
-   **Programmation orientée chemin de fer (Railway Oriented Programming)** : les succès et les échecs circulent sur des pistes parallèles et clairement définies.

### Le problème avec les exceptions

```python
def traiter(donnees):
    # Quelles exceptions ces fonctions peuvent-elles lever ?
    analysees = json.loads(donnees)
    validees = valider(analysees)
    resultat = transformer(validees)
    return resultat

# L'appelant ignore tout des risques potentiels :
try:
    res = traiter(donnees)
except json.JSONDecodeError:
    # Gère l'erreur d'analyse
except ValidationError:
    # Gère l'erreur de validation
# ...
```

### La solution avec `Result`

```python
from fptk.adt.result import Ok, Err
from fptk.core.func import pipe

def traiter(donnees: str) -> Result[Sortie, str]:
    return pipe(
        donnees,
        analyser_json,        # Renvoie Result[dict, str]
        lambda r: r.bind(valider),     # Renvoie Result[Valide, str]
        lambda r: r.bind(transformer), # Renvoie Result[Sortie, str]
    )

# L'appelant voit le type Result et sait qu'il doit le gérer :
resultat = traiter(donnees)
resultat.match(
    ok=lambda s: sauvegarder(s),
    err=lambda e: loguer_erreur(e)
)
```

Le type d'erreur est désormais visible et fait partie intégrante de la chaîne de traitement.

## API

### Types

| Type | Description |
| :--- | :--- |
| `Result[T, E]` | Type de base : un succès de type `T` ou une erreur de type `E`. |
| `Ok[T, E]` | Variante représentant un succès. |
| `Err[T, E]` | Variante représentant un échec. |

### Constructeurs

```python
from fptk.adt.result import Ok, Err

succes = Ok(42)
echec = Err("un problème est survenu")
```

### Méthodes principales

| Méthode | Signature | Description |
| :--- | :--- | :--- |
| `is_ok()` | `() -> bool` | Renvoie `True` s'il s'agit d'un `Ok`. |
| `is_err()` | `() -> bool` | Renvoie `True` s'il s'agit d'un `Err`. |
| `map(f)` | `(T -> U) -> Result[U, E]` | Transforme la valeur de succès. |
| `bind(f)` | `(T -> Result[U, E]) -> Result[U, E]` | Enchaîne une fonction retournant elle-même un `Result`. |
| `flatten()` | `Result[Result[T, E], E] -> Result[T, E]` | Déplie un `Result` imbriqué. |
| `zip(other)` | `(Result[U, E]) -> Result[tuple[T, U], E]` | Combine deux `Result` en un tuple de valeurs. |
| `map_err(f)` | `(E -> F) -> Result[T, F]` | Transforme la valeur d'erreur. |
| `recover(f)` | `(E -> T) -> Result[T, E]` | Convertit `Err` en `Ok` via une fonction. |
| `recover_with(f)` | `(E -> Result[T, E]) -> Result[T, E]` | Convertit `Err` en un autre `Result`. |
| `unwrap_or(default)` | `(U) -> T | U` | Récupère la valeur ou une valeur par défaut. |
| `unwrap_or_else(f)` | `(E -> U) -> T | U` | Récupère la valeur ou la calcule depuis l'erreur. |
| `match(ok, err)` | `(T -> U, E -> U) -> U` | Effectue un pattern matching sur les deux cas. |
| `unwrap()` | `() -> T` | Récupère la valeur ou lève une `ValueError`. |

## Fonctionnement technique

### Structure de données

`Result` est implémentée comme un type scellé avec deux variantes distinctes :

```python
class Result[T, E]:
    """Classe de base - non instanciable directement."""
    pass

@dataclass(frozen=True, slots=True)
class Ok[T, E](Result[T, E]):
    value: T

@dataclass(frozen=True, slots=True)
class Err[T, E](Result[T, E]):
    error: E
```

### Le Bifuncteur : `map_err`

Contrairement au type `Option`, `Result` permet de transformer non seulement la valeur de succès (`map`), mais aussi la valeur d'erreur :

```python
def map_err(self, f):
    if isinstance(self, Err):
        return Err(f(self.error))
    return self  # Les instances Ok passent sans modification
```

### Programmation orientée chemin de fer

Voyez `Result` comme une voie ferrée à deux rails :

```
     Piste Ok  ─────┬─────┬─────┬─────> Succès
                    │     │     │
     Piste Err ─────┴─────┴─────┴─────> Échec
                analyse  valide  transfo
```

Chaque étape décide soit de rester sur le rail `Ok`, soit de bifurquer sur le rail `Err`. Une fois sur le rail `Err`, on y reste jusqu'au bout.

## Exemples d'utilisation

### Encapsuler les exceptions existantes

```python
from fptk.core.func import try_catch
from fptk.adt.result import Ok, Err

# Encapsulation automatique
safe_parse = try_catch(json.loads)
safe_parse('{"a": 1}')  # Ok({"a": 1})
safe_parse('invalide')   # Err(JSONDecodeError(...))

# Encapsulation manuelle
def analyser_entier(s: str) -> Result[int, str]:
    try:
        return Ok(int(s))
    except ValueError:
        return Err(f"'{s}' n'est pas un entier valide")
```

### Chaînage de validations

```python
def valider_age(data: dict) -> Result[dict, str]:
    age = data.get("age")
    if age is None or age < 0:
        return Err("Âge invalide")
    return Ok(data)

def traiter_utilisateur(entree: str) -> Result[User, str]:
    return (
        try_catch(json.loads)(entree)
        .map_err(lambda e: f"JSON invalide : {e}")
        .bind(valider_age)
        .map(lambda d: User(**d))
    )
```

### Valeurs de repli intelligentes

```python
# Repli simple
valeur = analyser_entier(saisie).unwrap_or(0)

# Repli calculé (ne s'exécute qu'en cas d'erreur)
valeur = analyser_entier(saisie).unwrap_or_else(
    lambda err: loguer_et_renvoyer_defaut(err)
)
```

### Récupération d'erreurs

Utilisez `recover` pour convertir un `Err` en `Ok` avec une valeur de repli :

```python
from fptk.adt.result import Ok, Err

# Fournir une valeur par défaut en cas d'erreur
Err("introuvable").recover(lambda e: "defaut")  # Ok("defaut")
Ok(5).recover(lambda e: 0)  # Ok(5) - inchangé

# Exemple pratique : configuration avec repli
def obtenir_config(cle: str) -> Result[str, str]:
    return lire_fichier_config(cle).recover(lambda e: config_defaut[cle])
```

Utilisez `recover_with` pour une récupération conditionnelle où certaines erreurs peuvent être gérées :

```python
from fptk.adt.result import Ok, Err

def telecharger_avec_retry(url: str) -> Result[Response, str]:
    return telecharger(url).recover_with(lambda e:
        telecharger(url) if e == "timeout" else Err(e)  # Réessayer uniquement les timeouts
    )

# Enchaîner plusieurs stratégies de récupération
resultat = (
    telecharger_depuis_primaire()
    .recover_with(lambda e: telecharger_depuis_secondaire())  # Essayer le backup
    .recover(lambda e: reponse_en_cache)                      # Dernier recours : cache
)
```

### Aplatissement de Results imbriqués

Utilisez `flatten` lorsque vous avez un `Result[Result[T, E], E]` et souhaitez obtenir un `Result[T, E]` :

```python
from fptk.adt.result import Ok, Err

# Usage direct
Ok(Ok(42)).flatten()       # Ok(42)
Ok(Err("interne")).flatten() # Err("interne")
Err("externe").flatten()     # Err("externe")

# Scénario courant : map avec une fonction qui retourne Result
def recuperer_utilisateur(id: int) -> Result[User, str]: ...
def recuperer_permissions(user: User) -> Result[Permissions, str]: ...

# Sans flatten : Result[Result[Permissions, str], str]
imbrique = recuperer_utilisateur(1).map(recuperer_permissions)

# Avec flatten : Result[Permissions, str]
permissions = recuperer_utilisateur(1).map(recuperer_permissions).flatten()

# Note : ceci est équivalent à utiliser bind directement
permissions = recuperer_utilisateur(1).bind(recuperer_permissions)
```

## Quand utiliser Result ?

**Privilégiez Result lorsque :**

-   Une opération peut échouer et que l'échec doit être traité.
-   Vous souhaitez des erreurs typées et riches plutôt que de simples exceptions textuelles.
-   Vous construisez des pipelines où les erreurs doivent se propager naturellement.
-   Vous voulez forcer l'appelant à prendre en compte la possibilité d'un échec.

**Évitez Result lorsque :**

-   L'échec est véritablement exceptionnel (bug logiciel critique, mémoire saturée).
-   Vous êtes dans une boucle de calcul intensive où la performance est la priorité absolue.
-   L'échec ne comporte aucune information utile → considérez alors [`Option`](option.md).

## Comparaison avec Option

| Aspect | Option | Result |
| :--- | :--- | :--- |
| **Cas possibles** | `Some(T)`, `Nothing` | `Ok(T)`, `Err(E)` |
| **Info d'échec** | Aucune. | Oui (via le type d'erreur). |
| **Usage type** | Valeur potentiellement absente. | Opération potentiellement en échec. |

## Voir aussi

-   [`Option`](option.md) — Lorsque l'absence de valeur ne nécessite pas d'explication.
-   [`try_catch`](core.md#try_catch) — Pour convertir les exceptions en objets `Result`.
-   [`validate_all`](validate.md) — Pour accumuler plusieurs erreurs au lieu de s'arrêter à la première.
-   [`traverse_result`](traverse.md) — Pour collecter plusieurs `Result` en un seul.