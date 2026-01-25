# Writer

Le module `fptk.adt.writer` propose la monade `Writer`, conçue pour les calculs qui produisent un résultat accompagné d'un journal (log) accumulé. Elle permet de dissocier la logique de calcul de la préoccupation de journalisation.

## Concept : La Monade Writer

La monade Writer modélise des calculs qui renvoient à la fois une valeur et un journal de bord s'enrichissant au fil des opérations. Le journal peut être de n'importe quel type **Monoïde** — un type doté d'un élément neutre et d'une opération de combinaison associative.

Voyez-la comme : **un calcul qui tient son propre journal de bord.**

```python
Writer[W, A]  ≈  (A, W)  # où W est un Monoïde
```

Ainsi, un `Writer[list[str], int]` est un calcul produisant un entier (`int`) tout en collectant une liste de messages textuels.

### Le problème : la journalisation polluant la logique métier

```python
def traiter(donnees, logger):
    logger.info("Démarrage du traitement")
    validees = valider(donnees)
    logger.debug(f"Données validées : {validees}")
    transformees = transformer(validees)
    logger.debug(f"Données transformées : {transformees}")
    logger.info("Traitement terminé")
    return transformees

# Problèmes :
# - Le logger envahit les signatures de fonctions.
# - Les effets de bord (E/S) sont entremêlés à la logique pure.
# - Difficile à tester sans mocker le logger.
```

### La solution avec `Writer`

```python
from fptk.adt.writer import Writer, tell, monoid_list

def traiter(donnees) -> Writer[list[str], Result]:
    return (
        Writer.unit(donnees, monoid_list)
        .bind(lambda d: tell(["Démarrage du traitement"]).map(lambda _: d))
        .bind(lambda d:
            tell([f"Validé : {valider(d)}"]).map(lambda _: valider(d))
        )
        .bind(lambda v:
            tell([f"Transformé : {transformer(v)}"]).map(lambda _: transformer(v))
        )
        .bind(lambda t:
            tell(["Traitement terminé"]).map(lambda _: t)
        )
    )

# Pur : aucun effet de bord jusqu'à l'extraction finale
resultat, journaux = traiter(donnees).run()
# Vous écrivez ensuite les journaux comme bon vous semble
for message in journaux:
    print(message)
```

Le calcul demeure pur. Les journaux sont collectés mais pas encore écrits. Vous pouvez librement les inspecter, les filtrer ou les rediriger.

## Concept : Les Monoïdes

Un **Monoïde** est une structure algébrique possédant :

1.  Un **élément identité** (valeur vide) : `e`.
2.  Une **opération de combinaison associative** : `comb(a, comb(b, c)) == comb(comb(a, b), c)`.

Monoïdes courants supportés par fptk :

| Type | Identité | Combinaison | Utilité |
| :--- | :--- | :--- | :--- |
| `list` | `[]` | `+` (concaténation) | Liste de messages, métriques. |
| `str` | `""` | `+` (concaténation) | Journal textuel continu. |
| `int` (somme) | `0` | `+` (addition) | Compteurs, cumuls. |
| `int` (produit) | `1` | `*` (multiplication) | Probabilités, facteurs. |
| `bool` (all) | `True` | `and` | Vérification de conditions. |
| `bool` (any) | `False` | `or` | Détection d'événements. |
| `frozenset` | `frozenset()` | `\|` (union) | Collecte d'éléments uniques. |
| `float` (max) | `-inf` | `max` | Valeur maximale rencontrée. |
| `float` (min) | `+inf` | `min` | Valeur minimale rencontrée. |

### Monoïdes prédéfinis

fptk fournit des monoïdes prêts à l'emploi :

| Monoïde | Type | Identité | Description |
| :--- | :--- | :--- | :--- |
| `monoid_list` | `list[object]` | `[]` | Concaténation de listes |
| `monoid_str` | `str` | `""` | Concaténation de chaînes |
| `monoid_sum` | `int \| float` | `0` | Addition numérique |
| `monoid_product` | `int \| float` | `1` | Multiplication numérique |
| `monoid_all` | `bool` | `True` | ET logique (conjonction) |
| `monoid_any` | `bool` | `False` | OU logique (disjonction) |
| `monoid_set` | `frozenset[object]` | `frozenset()` | Union d'ensembles |
| `monoid_max` | `float` | `-inf` | Valeur maximale |
| `monoid_min` | `float` | `+inf` | Valeur minimale |

```python
from fptk.adt.writer import (
    monoid_list, monoid_str, monoid_sum, monoid_product,
    monoid_all, monoid_any, monoid_set, monoid_max, monoid_min,
)

# Accumuler des compteurs
monoid_sum.combine(5, 3)  # 8

# Suivre des conditions booléennes
monoid_all.combine(True, False)  # False
monoid_any.combine(True, False)  # True

# Collecter des éléments uniques
monoid_set.combine(frozenset({1, 2}), frozenset({2, 3}))  # frozenset({1, 2, 3})

# Suivre les valeurs extrêmes
monoid_max.combine(5.0, 10.0)  # 10.0
monoid_min.combine(5.0, 10.0)  # 5.0
```

## API

### Types

| Type | Description |
| :--- | :--- |
| `Writer[W, A]` | Un calcul produisant un résultat `A` et un journal `W`. |
| `Monoid[W]` | Protocole définissant `identity` et `combine`. |

### Constructeurs

```python
from fptk.adt.writer import Writer, monoid_list

# Création avec un journal vide
w = Writer.unit(42, monoid_list)

# Création avec une valeur et un journal initial
w = Writer(42, ["démarrage"], monoid_list)
```

### Méthodes principales

| Méthode | Signature | Description |
| :--- | :--- | :--- |
| `unit(val, monoid)` | `classmethod` | Initialise un Writer avec un journal vide. |
| `map(f)` | `(A -> B) -> Writer[W, B]` | Transforme la valeur produite. |
| `bind(f)` | `(A -> Writer[W, B]) -> Writer[W, B]` | Enchaîne les calculs en combinant leurs journaux. |
| `run()` | `() -> (A, W)` | Extrait le couple (valeur, journal). |

### Fonctions utilitaires

| Fonction | Signature | Description |
| :--- | :--- | :--- |
| `tell(log, monoid)` | `(W, Monoid[W]) -> Writer[W, None]` | Ajoute une entrée au journal de bord. |
| `listen(writer)` | `Writer[W, A] -> Writer[W, (A, W)]` | Récupère le journal courant au sein du calcul. |
| `censor(f, writer)` | `(W -> W, Writer[W, A]) -> Writer[W, A]` | Modifie ou filtre le journal accumulé. |

## Fonctionnement technique

### La Monade : `bind`

La méthode `bind` assure la transition des valeurs tout en orchestrant la fusion des journaux à l'aide du monoïde :

```python
def bind(self, f):
    wb = f(self.value)
    return Writer(
        wb.value,
        self.monoid.combine(self.log, wb.log),  # Fusion des logs !
        self.monoid
    )
```

## Exemples d'utilisation

### Collecte de métriques de performance

```python
@dataclass
class Metrics:
    nb_requetes: int = 0
    cache_hits: int = 0

    def __add__(self, other):
        return Metrics(
            self.nb_requetes + other.nb_requetes,
            self.cache_hits + other.cache_hits
        )

monoid_metrics = Monoid(identity=Metrics(), combine=lambda a, b: a + b)

def tracer_requete() -> Writer[Metrics, None]:
    return tell(Metrics(nb_requetes=1), monoid_metrics)
```

### Utilisation de `censor` pour le filtrage

```python
def filtrer_info(journaux):
    return [m for message in journaux if message.startswith("INFO")]

# On ne garde que les messages INFO du calcul verbeux
resultat_purge = censor(filtrer_info, calcul_tres_verbeux())
```

## Quand utiliser Writer ?

**Privilégiez Writer lorsque :**

-   Vous voulez accumuler des logs ou des métriques sans polluer votre logique métier.
-   Vous avez besoin de construire une piste d'audit (audit trail).
-   Vous souhaitez différer l'écriture effective des logs (E/S) à la fin du processus.
-   Vous visez une journalisation pure, déterministe et facile à tester.

**Évitez Writer lorsque :**

-   Les logs doivent impérativement être écrits en temps réel (en cas de crash, par exemple).
-   Le journal risque de devenir trop volumineux pour tenir en mémoire.
-   Une journalisation simple et directe via un logger classique suffit amplement.

## Voir aussi

-   [`Reader`](reader.md) — Pour accéder à un environnement en lecture seule.
-   [`State`](state.md) — Lorsque vous devez à la fois lire et modifier une donnée au cours du temps.
-   [Effets de bord](../guide/side-effects.md) — Pour comprendre comment isoler la pureté des calculs.