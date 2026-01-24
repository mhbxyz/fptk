# Liste non vide (NonEmptyList)

Le module `fptk.adt.nelist` définit le type `NonEmptyList`, une structure de liste garantissant, par construction, la présence d'au moins un élément.

## Concept : Des collections jamais vides

De nombreuses opérations sur les listes classiques échouent ou produisent des résultats incohérents lorsqu'elles sont appliquées à une séquence vide :

```python
max([])    # ValueError: max() arg is an empty sequence
min([])    # ValueError
premier = xs[0]  # IndexError si la liste est vide
moyenne = sum(xs) / len(xs)  # ZeroDivisionError si la liste est vide
```

`NonEmptyList` transforme cette exigence de « non-vacuité » en une garantie au niveau du type. Posséder une `NonEmptyList` vous assure qu'elle contient au moins un élément, éliminant ainsi le besoin de vérifications manuelles lors de l'exécution.

### Le problème : les tests de vacuité répétitifs

```python
def calculer_moyenne(xs: list[float]) -> float:
    if not xs:
        raise ValueError("Impossible de calculer la moyenne d'une liste vide")
    return sum(xs) / len(xs)

def obtenir_premier(xs: list[T]) -> T:
    if not xs:
        raise ValueError("La liste est vide")
    return xs[0]

# Chaque fonction doit valider la donnée, et chaque appelant doit gérer l'exception potentielle.
```

### La solution : `NonEmptyList`

```python
from fptk.adt.nelist import NonEmptyList

def calculer_moyenne(xs: NonEmptyList[float]) -> float:
    # Aucun test requis : xs contient forcément au moins un élément.
    return sum(xs) / len(list(xs))

def obtenir_premier(xs: NonEmptyList[T]) -> T:
    return xs.head  # Toujours sûr

# Construction sécurisée aux frontières du code
resultat = NonEmptyList.from_iter(donnees)  # Renvoie Option[NonEmptyList]
if resultat:
    moyenne = calculer_moyenne(resultat)
else:
    # On gère le cas vide une seule fois, ici même.
```

## API

### Types

| Type | Description |
| :--- | :--- |
| `NonEmptyList[E]` | Liste comportant obligatoirement au moins un élément. |

### Constructeurs

```python
from fptk.adt.nelist import NonEmptyList

# Construction directe (toujours non vide)
nel = NonEmptyList(1)                    # [1]
nel = NonEmptyList(1, (2, 3, 4))         # [1, 2, 3, 4]

# À partir d'un itérable (peut être vide)
resultat = NonEmptyList.from_iter([1, 2])  # Renvoie une NonEmptyList ou None
resultat = NonEmptyList.from_iter([])      # Renvoie None
```

### Propriétés

| Propriété | Type | Description |
| :--- | :--- | :--- |
| `head` | `E` | Le premier élément (dont l'existence est garantie). |
| `tail` | `tuple[E, ...]` | Les éléments restants (peut être un tuple vide). |

### Méthodes

| Méthode | Signature | Description |
| :--- | :--- | :--- |
| `append(e)` | `(E) -> NonEmptyList[E]` | Ajoute un élément à la fin. |
| `to_list()` | `() -> list[E]` | Convertit en une liste standard de Python. |
| `from_iter(it)` | `staticmethod (Iterable[E]) -> NonEmptyList[E] | None` | Tente de créer une `NonEmptyList` depuis un itérable. |
| `__iter__()` | `() -> Iterator[E]` | Permet de parcourir l'ensemble des éléments. |

## Fonctionnement technique

### Structure de données

`NonEmptyList` s'appuie sur un `head` obligatoire et un `tail` facultatif :

```python
@dataclass(frozen=True, slots=True)
class NonEmptyList[E]:
    head: E                      # Premier élément (requis)
    tail: tuple[E, ...] = ()     # Éléments suivants (tuple pour garantir l'immuabilité)
```

L'immuabilité est assurée par le décorateur `@dataclass(frozen=True)`.

### Construction sécurisée

```python
@staticmethod
def from_iter(it: Iterable[E]) -> NonEmptyList[E] | None:
    iterator = iter(it)
    try:
        h = next(iterator)
    except StopIteration:
        return None  # L'itérable était vide
    return NonEmptyList(h, tuple(iterator))
```

La méthode `from_iter` renvoie `None` si l'itérable fourni est vide. C'est le seul moyen d'obtenir une instance de `NonEmptyList` à partir de données dynamiques.

## Exemples d'utilisation

### Accès sécurisé au premier élément

```python
from fptk.adt.nelist import NonEmptyList

# Avec une liste classique : risque d'erreur
def premier_element_dangereux(xs: list[int]) -> int:
    return xs[0]  # IndexError si vide !

# Avec NonEmptyList : sécurité totale
def premier_element_sur(xs: NonEmptyList[int]) -> int:
    return xs.head  # Garanti d'exister

# Validation aux limites
donnees_brutes = recuperer_donnees()  # list[int]
nel = NonEmptyList.from_iter(donnees_brutes)
if nel:
    print(premier_element_sur(nel))
else:
    print("Aucune donnée disponible")
```

### Calcul de statistiques sans crainte

```python
from fptk.adt.nelist import NonEmptyList

def statistiques(xs: NonEmptyList[float]) -> dict:
    """Calcule des statistiques sans avoir à vérifier la vacuité de la liste."""
    valeurs = list(xs)
    return {
        "nombre": len(valeurs),
        "somme": sum(valeurs),
        "moyenne": sum(valeurs) / len(valeurs), # Sûr (pas de division par zéro possible)
        "min": min(valeurs),  # Sûr
        "max": max(valeurs),  # Sûr
        "premier": xs.head,   # Sûr
    }
```

### Usage avec `validate_all`

```python
from fptk.validate import validate_all
from fptk.adt.nelist import NonEmptyList

# validate_all renvoie Result[T, NonEmptyList[E]]
# En cas d'échec, vous avez la garantie d'obtenir au moins une erreur.

resultat = validate_all([test1, test2, test3], donnees)
resultat.match(
    ok=lambda d: traiter(d),
    err=lambda erreurs: print(f"Validation échouée : {erreurs.head}")
    # erreurs est une NonEmptyList[str], donc .head est parfaitement sûr.
)
```

## Quand utiliser `NonEmptyList` ?

**Privilégiez `NonEmptyList` lorsque :**

-   Votre logique métier exige impérativement la présence d'au moins un élément.
-   Vous voulez supprimer les tests de vacuité redondants dans vos fonctions.
-   Vous accumulez des erreurs (comme dans un processus de validation).
-   Vous effectuez des agrégations nécessitant une entrée non vide (moyenne, extremums, etc.).

**Évitez `NonEmptyList` lorsque :**

-   Une collection vide est une donnée tout à fait valide dans votre contexte.
-   Vous avez besoin d'accès aléatoires très fréquents (préférez `list`).
-   Vous effectuez de nombreux ajouts d'éléments (la concaténation de tuples est en O(n)).

## NonEmptyList vs Option[list]

| Type | Signification |
| :--- | :--- |
| `list[T]` | Zéro, un ou plusieurs éléments. |
| `Option[list[T]]` | Une liste facultative (qui pourrait tout de même être vide). |
| `NonEmptyList[T]` | Un ou plusieurs éléments (garanti). |
| `Option[NonEmptyList[T]]` | Une liste facultative qui, si elle existe, contient forcément au moins un élément. |

## Voir aussi

-   [`validate_all`](validate.md) — Utilise `NonEmptyList` pour collecter les erreurs.
-   [`Option`](option.md) — Pour les valeurs potentiellement absentes.
-   [`Result`](result.md) — Pour les calculs susceptibles d'échouer.