<p align="center">
  <img src="assets/fptk-logo.svg" alt="fptk — Functional Programming Toolkit" width="450">
</p>

<p align="center">
  <strong>Programmation fonctionnelle pragmatique pour Python 3.13+</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/fptk/">PyPI</a> ·
  <a href="https://github.com/mhbxyz/fptk">GitHub</a> ·
  <a href="getting-started.fr.md">Commencer</a>
</p>

---

## Qu'est-ce que la programmation fonctionnelle ?

La programmation fonctionnelle est une manière d'écrire du code où vous construisez des programmes en composant des fonctions pures. Des fonctions qui retournent toujours la même sortie pour la même entrée et ne modifient rien en dehors d'elles-mêmes.

Cela semble abstrait, mais cela résout des problèmes réels :

- **Bugs liés à l'état partagé** : Quand plusieurs parties de votre code modifient les mêmes données, traquer les bugs devient un cauchemar. Les fonctions pures ne modifient rien, donc ce problème disparaît.
- **Code difficile à tester** : Les fonctions avec des effets de bord (appels base de données, requêtes API, E/S fichiers) nécessitent des mocks complexes pour être testées. Les fonctions pures n'ont besoin que d'entrées et de sorties attendues.
- **Code difficile à comprendre** : Quand une fonction peut tout faire — modifier des globales, appeler des API, écrire des fichiers — vous devez lire toute l'implémentation pour savoir ce qu'elle fait. Les fonctions pures sont prévisibles.

La programmation fonctionnelle ne consiste pas à utiliser des abstractions sophistiquées. Il s'agit d'écrire du code plus facile à raisonner, tester et maintenir.

## Pourquoi fptk ?

Python est un excellent langage, mais il a quelques points sensibles que les patrons fonctionnels résolvent élégamment :

### Le problème du `None`

```python
user = get_user(id)
name = user.get("profile").get("name").upper()  # AttributeError
```

Le `None` de Python se propage silencieusement jusqu'à l'explosion. Vous vous retrouvez avec du code défensif partout :

```python
user = get_user(id)
if user and user.get("profile") and user.get("profile").get("name"):
    name = user["profile"]["name"].upper()
else:
    name = "Anonymous"
```

L'`Option` de fptk rend l'absence explicite et composable :

```python
name = (
    from_nullable(get_user(id))
    .bind(lambda u: from_nullable(u.get("profile")))
    .bind(lambda p: from_nullable(p.get("name")))
    .map(str.upper)
    .unwrap_or("Anonymous")
)
```

### Le problème des exceptions

Les exceptions sont invisibles dans les signatures de fonctions. Vous appelez `parse_json(data)` et vous n'avez aucune idée qu'elle pourrait lever `JSONDecodeError`, `UnicodeDecodeError`, ou `MemoryError`. Vous enveloppez tout dans des try/except ou vous espérez que tout ira bien.

Le `Result` de fptk fait des erreurs une partie du type :

```python
def parse_json(data: str) -> Result[dict, str]:
    ...

# Le type de retour vous dit : cela peut échouer, gérez-le
```

### Le problème des appels imbriqués

Le code réel ressemble souvent à ceci :

```python
send_email(format_message(validate(parse(request))))
```

L'ordre de lecture est de l'intérieur vers l'extérieur. Ajouter une étape signifie trouver le bon niveau d'imbrication. Le `pipe` de fptk rend le flux de données linéaire :

```python
pipe(request, parse, validate, format_message, send_email)
```

## L'état d'esprit fonctionnel

La programmation fonctionnelle vous demande de penser différemment :

| Pensée impérative | Pensée fonctionnelle |
|-------------------|----------------------|
| "Fais ceci, puis fais cela" | "Transforme ceci en cela" |
| Modifier les variables sur place | Créer de nouvelles valeurs à partir des anciennes |
| Gérer les erreurs avec try/catch | Faire des erreurs une partie du type de retour |
| Vérifier None partout | Rendre l'absence explicite avec Option |
| Les fonctions peuvent tout faire | Les fonctions calculent uniquement des sorties à partir des entrées |

Ce changement demande de la pratique, mais le bénéfice est un code plus prévisible, testable et composable.

## Ce que fptk fournit

| Fonctionnalité | Ce qu'elle résout |
|----------------|-------------------|
| `pipe`, `compose` | Appels de fonctions imbriqués, flux de données difficile à lire |
| `Option` | Erreurs de pointeur null, vérifications défensives de None |
| `Result` | Exceptions invisibles, gestion des erreurs peu claire |
| `validate_all` | Validation fail-fast, messages d'erreur médiocres |
| `Reader` | Injection de dépendances, passage de configuration |
| `State` | État mutable, code à état difficile à tester |
| `Writer` | Journalisation mêlée à la logique, effets de bord |

## Installation

```bash
pip install fptk
```

## Prochaines étapes

- [Commencer](getting-started.fr.md) — Comprendre les concepts et commencer à utiliser fptk
- **Guide**
    - [Concepts fondamentaux](guide/core-concepts.md) — Plongée approfondie dans chaque patron
    - [Effets de bord](guide/side-effects.md) — Structurer le code avec des cœurs purs
    - [Migration](guide/migration.md) — Adopter progressivement les patrons fonctionnels
- **Recettes**
    - [Développement API](recipes/api-development.md) — Construire des API web robustes
    - [Traitement de données](recipes/data-processing.md) — Pipelines ETL et transformations
- [Référence](reference/index.md) — Documentation API complète avec théorie et exemples
