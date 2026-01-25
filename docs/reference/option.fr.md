# Option

Le module `fptk.adt.option` définit le type `Option`, conçu pour gérer élégamment les valeurs susceptibles d'être absentes. Plutôt que d'utiliser `None` et de multiplier les vérifications manuelles, `Option` rend l'absence de valeur explicite, robuste et parfaitement composable.

## Concept : La Monade Option (ou Maybe)

En programmation fonctionnelle, `Option` (souvent appelée `Maybe` dans d'autres langages comme Haskell) représente un conteneur pour une valeur qui peut, ou non, exister. Elle se décline en deux variantes :

-   **`Some(value)`** : la valeur est présente.
-   **`Nothing`** : la valeur est absente.

Cette approche est essentielle pour :

-   **Éliminer les exceptions de pointeur nul** : vous ne pouvez plus appeler accidentellement des méthodes sur une valeur `None`.
-   **Rendre l'absence explicite** : la signature de type vous avertit directement qu'une valeur peut manquer.
-   **Composer les transformations** : enchaînez vos opérations en laissant le type `Option` gérer gracieusement les cas d'absence.

### Le problème avec `None`

```python
utilisateur = get_user(id)
# Risque d'AttributeError à chaque étape si l'une des valeurs est None !
nom = utilisateur.get("profile").get("name").upper()

# On se retrouve à écrire du code défensif partout :
if utilisateur and utilisateur.get("profile") and utilisateur.get("profile").get("name"):
    nom = utilisateur["profile"]["name"].upper()
else:
    nom = "Anonyme"
```

### La solution avec `Option`

```python
from fptk.adt.option import from_nullable, Some, NOTHING

nom = (
    from_nullable(get_user(id))
    .bind(lambda u: from_nullable(u.get("profile")))
    .bind(lambda p: from_nullable(p.get("name")))
    .map(str.upper)
    .unwrap_or("Anonyme")
)
```

Chaque appel à `.bind()` court-circuite immédiatement vers `NOTHING` si l'étape précédente a échoué. Fini les exceptions et les blocs conditionnels imbriqués.

## API

### Types

| Type | Description |
| :--- | :--- |
| `Option[T]` | Type de base représentant une valeur optionnelle. |
| `Some[T]` | Variante contenant une valeur présente. |
| `Nothing` | Variante représentant l'absence (classe singleton). |
| `NOTHING` | L'instance unique (singleton) de `Nothing`. |

### Constructeurs

```python
from fptk.adt.option import Some, NOTHING, from_nullable

# Construction directe
present = Some(42)
absent = NOTHING

# Depuis une valeur potentiellement None
from_nullable(ma_valeur)  # Some(x) si x n'est pas None, sinon NOTHING
```

### Méthodes principales

| Méthode | Signature | Description |
| :--- | :--- | :--- |
| `is_some()` | `() -> bool` | Renvoie `True` s'il s'agit d'un `Some`. |
| `is_none()` | `() -> bool` | Renvoie `True` s'il s'agit d'un `Nothing`. |
| `map(f)` | `(T -> U) -> Option[U]` | Applique `f` à la valeur si elle est présente. |
| `bind(f)` | `(T -> Option[U]) -> Option[U]` | Enchaîne une fonction retournant elle-même une `Option`. |
| `filter(p)` | `(T -> bool) -> Option[T]` | Conserve `Some` uniquement si le prédicat est vrai. |
| `flatten()` | `Option[Option[T]] -> Option[T]` | Déplie une `Option` imbriquée. |
| `zip(other)` | `(Option[U]) -> Option[tuple[T, U]]` | Combine deux `Option` en un tuple de valeurs. |
| `ap(other)` | `Option[T -> U].ap(Option[T]) -> Option[U]` | Applique une fonction enveloppée à une valeur enveloppée. |
| `unwrap_or(default)` | `(U) -> T | U` | Récupère la valeur ou une valeur par défaut. |
| `or_else(alt)` | `(Option[T] \| () -> Option[T]) -> Option[T]` | Fournit une alternative si la valeur est absente. |
| `to_result(err)` | `(E) -> Result[T, E]` | Convertit l'`Option` en `Result`. |
| `match(some, none)` | `(T -> U, () -> U) -> U` | Effectue un pattern matching sur les deux cas. |
| `unwrap()` | `() -> T` | Récupère la valeur ou lève une `ValueError`. |

### `or_else` : Évaluation immédiate vs paresseuse

`or_else` accepte indifféremment une valeur `Option` directe ou un callable (fonction) renvoyant une `Option` :

```python
from fptk.adt.option import Some, NOTHING

# Immédiat : la valeur est toujours évaluée
res1 = NOTHING.or_else(Some(42))

# Paresseux : la fonction n'est appelée que si nécessaire
res2 = NOTHING.or_else(lambda: Some(calcul_couteux()))
```

**Quel usage privilégier ?**

| Style | Syntaxe | Quand l'utiliser ? |
| :--- | :--- | :--- |
| **Immédiat** | `.or_else(Some(x))` | La valeur de repli est simple ou déjà calculée. |
| **Paresseux** | `.or_else(lambda: ...)` | Le calcul du repli est coûteux ou déclenche des effets de bord. |

## Fonctionnement technique

### Structure de données

`Option` est implémentée comme un type scellé avec deux variantes distinctes :

```python
class Option[T]:
    """Classe de base - non instanciable directement."""
    pass

@dataclass(frozen=True, slots=True)
class Some[T](Option[T]):
    value: T

@dataclass(frozen=True, slots=True)
class Nothing(Option[None]):
    pass

NOTHING = Nothing()  # Instance unique
```

L'usage de `@dataclass(frozen=True)` garantit l'immuabilité et l'efficacité mémoire des instances.

### Le Functor : `map`

`map` applique une transformation à la valeur contenue dans un `Some`, mais ne fait rien dans le cas d'un `Nothing` :

```python
def map(self, f):
    if isinstance(self, Some):
        return Some(f(self.value))
    return NOTHING
```

### La Monade : `bind`

`bind` (parfois appelé `flatMap` ou `and_then`) permet d'enchaîner des opérations qui renvoient elles-mêmes des `Option`. Elle évite ainsi de se retrouver avec des structures imbriquées du type `Option[Option[T]]` :

```python
def bind(self, f):
    if isinstance(self, Some):
        return f(self.value)  # f doit renvoyer une Option[U]
    return NOTHING
```

## Exemples d'utilisation

### Accès sécurisé aux structures imbriquées

```python
from fptk.adt.option import from_nullable

config = {"database": {"host": "localhost", "port": 5432}}

# Parcours sécurisé de dictionnaires imbriqués
port = (
    from_nullable(config.get("database"))
    .bind(lambda db: from_nullable(db.get("port")))
    .map(str)
    .unwrap_or("5432")
)
```

### Première valeur disponible (chaîne de repli)

```python
from fptk.adt.option import from_nullable, NOTHING

def obtenir_config(cle: str) -> Option[str]:
    """Tente de lire dans l'environnement, puis dans un fichier, puis utilise une valeur par défaut."""
    return (
        from_nullable(os.getenv(cle))
        .or_else(lambda: from_nullable(config_fichier.get(cle)))
        .or_else(lambda: from_nullable(valeurs_defaut.get(cle)))
    )
```

### Conversion vers Result

```python
from fptk.adt.option import from_nullable

def chercher_utilisateur(id: int) -> Option[User]:
    return from_nullable(db.get(id))

# Conversion pour une gestion d'erreurs plus détaillée
resultat = chercher_utilisateur(42).to_result(f"Utilisateur {id} introuvable")
# Ok(user) ou Err("Utilisateur 42 introuvable")
```

### Filtrage de valeurs

Utilisez `filter` pour conserver un `Some` uniquement s'il satisfait un prédicat :

```python
from fptk.adt.option import Some, NOTHING

# Conserver uniquement les nombres positifs
Some(5).filter(lambda x: x > 0)   # Some(5)
Some(-3).filter(lambda x: x > 0)  # NOTHING
NOTHING.filter(lambda x: x > 0)   # NOTHING

# Exemple pratique : valider une saisie utilisateur
def obtenir_age_valide(saisie: str) -> Option[int]:
    return parser_entier(saisie).filter(lambda age: 0 <= age <= 150)

obtenir_age_valide("25")   # Some(25)
obtenir_age_valide("-5")   # NOTHING (âge invalide)
obtenir_age_valide("200")  # NOTHING (âge invalide)
obtenir_age_valide("abc")  # NOTHING (échec du parsing)
```

### Aplatissement d'Options imbriquées

Utilisez `flatten` lorsque vous avez une `Option[Option[T]]` et souhaitez obtenir une `Option[T]` :

```python
from fptk.adt.option import Some, NOTHING

# Usage direct
Some(Some(42)).flatten()  # Some(42)
Some(NOTHING).flatten()   # NOTHING
NOTHING.flatten()         # NOTHING

# Scénario courant : map avec une fonction qui retourne Option
def obtenir_utilisateur(id: int) -> Option[User]: ...
def obtenir_manager(user: User) -> Option[User]: ...

# Sans flatten : Option[Option[User]]
imbrique = obtenir_utilisateur(1).map(obtenir_manager)

# Avec flatten : Option[User]
manager = obtenir_utilisateur(1).map(obtenir_manager).flatten()

# Note : ceci est équivalent à utiliser bind directement
manager = obtenir_utilisateur(1).bind(obtenir_manager)
```

### Application applicative

Utilisez `ap` pour appliquer une fonction enveloppée à une valeur enveloppée :

```python
from fptk.adt.option import Some, NOTHING

# Usage de base
Some(lambda x: x + 1).ap(Some(5))  # Some(6)
Some(lambda x: x + 1).ap(NOTHING)  # NOTHING
NOTHING.ap(Some(5))                # NOTHING

# Fonctions curryfiées pour plusieurs arguments
def additionner(a: int):
    return lambda b: a + b

Some(additionner).ap(Some(1)).ap(Some(2))  # Some(3)

# Exemple pratique : combiner des valeurs optionnelles
def creer_utilisateur(nom: str):
    return lambda email: {"nom": nom, "email": email}

utilisateur = Some(creer_utilisateur).ap(from_nullable(nom)).ap(from_nullable(email))
# Some({"nom": ..., "email": ...}) si les deux sont présents, sinon NOTHING
```

## Quand utiliser Option ?

**Privilégiez Option lorsque :**

-   Une valeur peut être légitimement absente (ce n'est pas forcément une erreur).
-   Vous voulez enchaîner des opérations pouvant échouer à tout moment.
-   Vous effectuez des recherches ou des analyses de données incertaines.
-   Vous souhaitez éradiquer les tests sur `None` dispersés dans votre code.

**Évitez Option lorsque :**

-   L'absence de valeur constitue une erreur devant être signalée précisément → utilisez [`Result`](result.md).
-   Vous avez besoin de savoir *pourquoi* la donnée est absente → utilisez [`Result`](result.md).
-   La performance est critique au sein de boucles très serrées (Option induit un léger surcoût).

## Voir aussi

-   [`Result`](result.md) — Lorsque l'absence est un échec porteur d'information.
-   [`traverse_option`](traverse.md) — Pour regrouper plusieurs `Option` en une seule.