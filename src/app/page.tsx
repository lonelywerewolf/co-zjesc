import ingredientsData from "../../data/ingredients.json";
import { CATEGORY_LABELS, type Ingredient, type IngredientCategory } from "@/lib/types";

const ingredients = ingredientsData as Ingredient[];

export default function Home() {
  const groups = new Map<IngredientCategory, Ingredient[]>();
  for (const ing of ingredients) {
    const list = groups.get(ing.category) ?? [];
    list.push(ing);
    groups.set(ing.category, list);
  }

  return (
    <main className="mx-auto w-full max-w-2xl px-4 py-8">
      <header className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-wider text-[var(--accent)]">Wersja 0.1</p>
        <h1 className="mt-1 text-3xl font-bold">Co zjeść?</h1>
        <p className="mt-2 text-[var(--muted)]">
          Baza składników, z których powstaną przepisy. Planer tygodnia pojawi się w kolejnym kroku.
        </p>
      </header>

      {[...groups.entries()].map(([category, items]) => (
        <section key={category} className="mb-6">
          <h2 className="mb-2 text-lg font-semibold">
            {CATEGORY_LABELS[category]} <span className="text-[var(--muted)] font-normal">({items.length})</span>
          </h2>
          <ul className="divide-y divide-[var(--line)] rounded-xl border border-[var(--line)] bg-[var(--card)]">
            {items.map((ing) => (
              <li key={ing.slug} className="flex items-baseline justify-between gap-3 px-4 py-2.5">
                <span>{ing.name}</span>
                <span className="shrink-0 text-sm tabular-nums text-[var(--muted)]">
                  {ing.kcal} kcal · B {ing.protein_g} g
                </span>
              </li>
            ))}
          </ul>
        </section>
      ))}

      <p className="mt-8 text-xs text-[var(--muted)]">Wartości na 100 g. {ingredients.length} składników.</p>
    </main>
  );
}
