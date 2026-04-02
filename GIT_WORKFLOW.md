# KAIA – Git Workflow Cheatsheet

## Täglich arbeiten

```bash
# Immer auf develop starten
git checkout develop
git status                    # Was ist offen?

# Neue Arbeit: Feature-Branch
git checkout -b feature/assessment-engine

# Arbeit speichern
git add .
git commit -m "feat: assessment engine Grundstruktur"

# Fertig → zurück nach develop mergen
git checkout develop
git merge feature/assessment-engine
```

---

## Commit-Nachrichten (Konvention)

```
feat:     Neue Funktionalität
fix:      Bugfix
refactor: Umbau ohne neues Verhalten
docs:     Dokumentation, README
eval:     Evaluationsexperimente (Thesis)
test:     Tests hinzufügen
```

Beispiele:
```
feat: state detector neuroadaptive Klassifikation
eval: Claude vs Mistral Latenz-Vergleich Session 1
fix: profile store JSON-Encoding Sonderzeichen
```

---

## Branch-Übersicht

```
main          ← nur stabiler, fertiger Code
  └── develop ← tägliche Arbeit
        ├── feature/assessment-engine
        ├── feature/prompt-builder
        ├── feature/provider-claude
        ├── feature/provider-mistral
        ├── feature/provider-ollama
        └── eval/llm-comparison
```

---

## GitHub verbinden (einmalig)

```bash
# Auf GitHub: neues Repository "kaia" erstellen (leer, ohne README)
# Dann:
git remote add origin https://github.com/DEINNAME/kaia.git
git push -u origin main
git push origin develop

# Alle Branches pushen
git push origin feature/provider-claude
git push origin feature/provider-mistral
git push origin feature/provider-ollama
git push origin eval/llm-comparison
```

---

## Nützliche Befehle

```bash
git log --oneline --graph     # Übersicht aller Commits
git diff                      # Was hat sich geändert?
git stash                     # Änderungen kurz weglegen
git stash pop                 # Wieder holen
```
