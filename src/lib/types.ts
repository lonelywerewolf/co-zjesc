// Typy odpowiadające tabelom w supabase/migrations/0001_init.sql

export type IngredientCategory =
  | "bialko"
  | "nabial"
  | "weglowodany"
  | "warzywa"
  | "owoce"
  | "tluszcze"
  | "dodatki"
  | "gotowe";

export interface Ingredient {
  slug: string;
  name: string;
  category: IngredientCategory;
  /** wartości na 100 g; węglowodany bez błonnika (konwencja etykiet UE) */
  kcal: number;
  protein_g: number;
  fat_g: number;
  carbs_g: number;
  fiber_g: number;
  nutrient_tags?: string[];
  unit_name?: string;
  unit_g?: number;
  typical_package_g?: number;
  keeps_days_opened?: number;
  is_pantry?: boolean;
}

export type MealType = "sniadanie" | "obiad" | "kolacja";
export type ActivityLevel = "siedzacy" | "lekki" | "umiarkowany" | "wysoki";
export type PortionSize = "mala" | "srednia" | "duza";

export interface HouseholdMember {
  name: string;
  sex: "m" | "k";
  age: number;
  weight_kg: number;
  height_cm: number;
  activity: ActivityLevel;
  portion: PortionSize;
}

export const CATEGORY_LABELS: Record<IngredientCategory, string> = {
  bialko: "Mięso, ryby, strączki",
  nabial: "Nabiał i jajka",
  weglowodany: "Kasze, makarony, pieczywo",
  warzywa: "Warzywa",
  owoce: "Owoce",
  tluszcze: "Tłuszcze i orzechy",
  dodatki: "Sosy i dodatki",
  gotowe: "Gotowe dania",
};
