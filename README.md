# Co zjeść?

Planer śniadań i obiadów do pracy, zbudowany z produktów dostępnych w Lidlu, Biedronce, Dino, Żabce i Intermarché.
Aplikacja sama układa jadłospis na tydzień: różnorodny, z dobrze dobranymi porcjami, pod budżet i czas w kuchni.
Działa w przeglądarce i jako aplikacja na telefonie (PWA).

## Jak to działa

- **Składniki** (`data/ingredients.json`): generyczne produkty z wartościami odżywczymi na 100 g.
- **Produkty sklepowe** (`data/off/*.json`): konkretne produkty z sieci, pobierane z Open Food Facts.
- **Przepisy**: szablony z wymiennymi składnikami (np. kurczak / tofu / ciecierzyca).
- **Planer**: algorytm (bez AI) wybiera dania na tydzień tak, by dieta była zbilansowana,
  różnorodna, mieściła się w budżecie i nie marnowała otwartych opakowań.

## Struktura

| Ścieżka | Co tam jest |
|---|---|
| `src/app` | Aplikacja (Next.js) |
| `src/lib` | Typy i logika |
| `data` | Baza składników i produktów |
| `scripts` | Import danych z Open Food Facts |
| `supabase/migrations` | Schemat bazy danych |
| `.github/workflows` | Automat cotygodniowego importu produktów |

## Uruchomienie lokalne

```bash
npm install
npm run dev
```

Aplikacja będzie pod http://localhost:3000.

## Dane

Dane o produktach pochodzą z [Open Food Facts](https://world.openfoodfacts.org) (licencja ODbL).
