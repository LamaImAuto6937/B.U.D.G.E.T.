B.U.D.G.E.T. - Balanced Usage of Daily Gains Expenses & Tracking


Branching Konventionen:

main: stabiler Produktions‑Branch
develop: Integrations‑Branch für laufende Entwicklung
feat/<feature_name>: Feature‑Branches, werden von develop erstellt und nach Fertigstellung in develop gemergt
fix/<fix_name>: Bugfixes für noch nicht releaste Änderungen, von develop abgezweigt, zurück nach develop
hotfix/<hotfix_name>: dringende Fixes für Produktion, von main abgezweigt, nach main und develop gemergt

main
 └─ hotfix/<hotfix_name>
develop
 ├─ feat/<feature_name>
 └─ fix/<fix_name>
          
