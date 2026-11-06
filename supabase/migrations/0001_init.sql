-- Co zjeść? — schemat bazy danych (Supabase / Postgres)
--
-- Kluczowy podział:
--   ingredients  = składnik GENERYCZNY ("pierś z kurczaka"), na nim liczymy makro.
--   products     = konkretny produkt w konkretnej sieci ("Pierś z kurczaka 500 g, Lidl"),
--                  ma gramaturę opakowania i cenę. Wskazuje na składnik generyczny.
-- Przepisy używają składników generycznych, więc działają w każdej sieci.
-- Lista zakupów zamienia składniki na realne produkty i zaokrągla do opakowań.

create table stores (
  id    serial primary key,
  slug  text unique not null,          -- 'lidl', 'biedronka', 'dino', 'zabka', 'intermarche'
  name  text not null
);

insert into stores (slug, name) values
  ('lidl', 'Lidl'),
  ('biedronka', 'Biedronka'),
  ('dino', 'Dino'),
  ('zabka', 'Żabka'),
  ('intermarche', 'Intermarché');

create type ingredient_category as enum (
  'bialko', 'nabial', 'weglowodany', 'warzywa', 'owoce', 'tluszcze', 'dodatki', 'gotowe'
);

create table ingredients (
  id                 serial primary key,
  slug               text unique not null,
  name               text not null,
  category           ingredient_category not null,
  -- wartości na 100 g (węglowodany bez błonnika, jak na etykietach w UE)
  kcal               numeric(6,1) not null,
  protein_g          numeric(5,1) not null,
  fat_g              numeric(5,1) not null,
  carbs_g            numeric(5,1) not null,
  fiber_g            numeric(5,1) not null default 0,
  nutrient_tags      text[] not null default '{}',   -- np. {omega3, zelazo, wapn}
  unit_name          text,                           -- np. 'sztuka' dla jajka
  unit_g             numeric(6,1),                   -- ile waży jedna sztuka
  typical_package_g  numeric(7,1),                   -- typowe opakowanie w dyskoncie
  keeps_days_opened  int,                            -- ile dni wytrzyma po otwarciu
  is_pantry          boolean not null default false, -- produkty "zawsze w szafce" (olej, przyprawy)
  source             text not null default 'manual'  -- 'manual' | 'off' (Open Food Facts)
);

create table products (
  id                serial primary key,
  store_id          int not null references stores(id),
  ingredient_id     int references ingredients(id),   -- null = jeszcze nieprzypisany
  name              text not null,
  brand             text,
  barcode           text,
  package_g         numeric(7,1),
  price_pln         numeric(7,2),
  price_updated_at  timestamptz,
  is_core           boolean not null default true,   -- stały asortyment vs. akcja tygodnia
  is_ready_meal     boolean not null default false,  -- gotowe danie (np. sałatka, wrap)
  kcal              numeric(6,1),                    -- makro z etykiety, jeśli znane
  protein_g         numeric(5,1),
  fat_g             numeric(5,1),
  carbs_g           numeric(5,1),
  fiber_g           numeric(5,1),
  active            boolean not null default true,
  source            text not null default 'off',
  unique (store_id, barcode)
);

create table promotions (
  id          serial primary key,
  product_id  int references products(id),
  store_id    int not null references stores(id),
  title       text not null,            -- tekst z gazetki
  price_pln   numeric(7,2),
  old_price_pln numeric(7,2),
  conditions  text,                     -- np. 'przy zakupie 2 szt.', 'z aplikacją'
  valid_from  date not null,
  valid_to    date not null,
  source_url  text
);

create type meal_type as enum ('sniadanie', 'obiad', 'kolacja');

create table recipes (
  id             serial primary key,
  slug           text unique not null,
  name           text not null,
  meal_types     meal_type[] not null,
  active_min     int not null,           -- czas pracy w kuchni
  total_min      int not null,           -- łącznie z pieczeniem / gotowaniem
  base_servings  int not null default 2,
  lunchbox_ok    boolean not null default true,  -- da się zabrać do pracy
  keeps_days     int not null default 1,         -- ile dni można trzymać w lodówce
  cuisine        text,
  tags           text[] not null default '{}',
  steps          jsonb not null                  -- ["krok 1", "krok 2", ...]
);

-- Składniki przepisu. Wiersze z tym samym "slot" to WYMIENNE warianty
-- (np. slot 'bialko': kurczak ALBO tofu ALBO ciecierzyca).
-- Wiersz bez slotu to składnik stały.
create table recipe_ingredients (
  id             serial primary key,
  recipe_id      int not null references recipes(id) on delete cascade,
  ingredient_id  int not null references ingredients(id),
  amount_g       numeric(7,1) not null,   -- na jedną porcję bazową
  slot           text,
  optional       boolean not null default false
);

create type activity_level as enum ('siedzacy', 'lekki', 'umiarkowany', 'wysoki');
create type portion_size as enum ('mala', 'srednia', 'duza');

create table household_members (
  id           serial primary key,
  owner_id     uuid not null,             -- auth.users.id
  name         text not null,
  sex          text check (sex in ('m', 'k')),
  age          int,
  weight_kg    numeric(5,1),
  height_cm    numeric(5,1),
  activity     activity_level not null default 'lekki',
  portion      portion_size not null default 'srednia',
  excluded_ingredients int[] not null default '{}'
);

create table meal_plans (
  id          serial primary key,
  owner_id    uuid not null,
  week_start  date not null,
  settings    jsonb not null,             -- budżet, czas, posiłki, osoby
  created_at  timestamptz not null default now()
);

create table meal_plan_items (
  id          serial primary key,
  plan_id     int not null references meal_plans(id) on delete cascade,
  day         date not null,
  meal        meal_type not null,
  recipe_id   int references recipes(id),
  product_id  int references products(id),   -- gdy to gotowe danie
  variant     jsonb,                          -- wybrane warianty slotów
  servings    numeric(4,2) not null
);
