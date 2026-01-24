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

La programmation fonctionnelle est une maniere d'ecrire du code ou vous construisez des programmes en composant des fonctions pures. Des fonctions qui retournent toujours la meme sortie pour la meme entree et ne modifient rien en dehors d'elles-memes.

Cela semble abstrait, mais cela resout des problemes reels :

- **Bugs lies a l'etat partage** : Quand plusieurs parties de votre code modifient les memes donnees, traquer les bugs devient un cauchemar. Les fonctions pures ne modifient rien, donc ce probleme disparait.
- **Code difficile a tester** : Les fonctions avec des effets de bord (appels base de donnees, requetes API, E/S fichiers) necessitent des mocks complexes pour etre testees. Les fonctions pures n'ont besoin que d'entrees et de sorties attendues.
- **Code difficile a comprendre** : Quand une fonction peut tout faire — modifier des globales, appeler des API, ecrire des fichiers — vous devez lire toute l'implementation pour savoir ce qu'elle fait. Les fonctions pures sont previsibles.

La programmation fonctionnelle ne consiste pas a utiliser des abstractions sophistiquees. Il s'agit d'ecrire du code plus facile a raisonner, tester et maintenir.

## Pourquoi fptk ?

Python est un excellent langage, mais il a quelques points sensibles que les patrons fonctionnels resolvent elegamment :

### Le probleme du `None`

```python
user = get_user(id)
name = user.get("profile").get("name").upper()  # AttributeError
```

Le `None` de Python se propage silencieusement jusqu'a l'explosion. Vous vous retrouvez avec du code defensif partout :

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

### Le probleme des exceptions

Les exceptions sont invisibles dans les signatures de fonctions. Vous appelez `parse_json(data)` et vous n'avez aucune idee qu'elle pourrait lever `JSONDecodeError`, `UnicodeDecodeError`, ou `MemoryError`. Vous enveloppez tout dans des try/except ou vous esperez que tout ira bien.

Le `Result` de fptk fait des erreurs une partie du type :

```python
def parse_json(data: str) -> Result[dict, str]:
    ...

# Le type de retour vous dit : cela peut echouer, gerez-le
```

### Le probleme des appels imbriques

Le code reel ressemble souvent a ceci :

```python
send_email(format_message(validate(parse(request))))
```

L'ordre de lecture est de l'interieur vers l'exterieur. Ajouter une etape signifie trouver le bon niveau d'imbrication. Le `pipe` de fptk rend le flux de donnees lineaire :

```python
pipe(request, parse, validate, format_message, send_email)
```

## L'etat d'esprit fonctionnel

La programmation fonctionnelle vous demande de penser differemment :

| Pensee imperative | Pensee fonctionnelle |
|-------------------|----------------------|
| "Fais ceci, puis fais cela" | "Transforme ceci en cela" |
| Modifier les variables sur place | Creer de nouvelles valeurs a partir des anciennes |
| Gerer les erreurs avec try/catch | Faire des erreurs une partie du type de retour |
| Verifier None partout | Rendre l'absence explicite avec Option |
| Les fonctions peuvent tout faire | Les fonctions calculent uniquement des sorties a partir des entrees |

Ce changement demande de la pratique, mais le benefice est un code plus previsible, testable et composable.

## Ce que fptk fournit

| Fonctionnalite | Ce qu'elle resout |
|----------------|-------------------|
| `pipe`, `compose` | Appels de fonctions imbriques, flux de donnees difficile a lire |
| `Option` | Erreurs de pointeur null, verifications defensives de None |
| `Result` | Exceptions invisibles, gestion des erreurs peu claire |
| `validate_all` | Validation fail-fast, messages d'erreur mediocres |
| `Reader` | Injection de dependances, passage de configuration |
| `State` | Etat mutable, code a etat difficile a tester |
| `Writer` | Journalisation melee a la logique, effets de bord |

## Installation

```bash
pip install fptk
```

## Prochaines etapes

- [Commencer](getting-started.fr.md) — Comprendre les concepts et commencer a utiliser fptk
- **Guide**
    - [Concepts fondamentaux](guide/core-concepts.md) — Plongee approfondie dans chaque patron
    - [Effets de bord](guide/side-effects.md) — Structurer le code avec des coeurs purs
    - [Migration](guide/migration.md) — Adopter progressivement les patrons fonctionnels
- **Recettes**
    - [Developpement API](recipes/api-development.md) — Construire des API web robustes
    - [Traitement de donnees](recipes/data-processing.md) — Pipelines ETL et transformations
- [Reference](reference/index.md) — Documentation API complete avec theorie et exemples
