# Nutrition and Data Contract
Use runtime TypeScript, not local scripts.
- BMI = kg / m² and is screening context only.
- Show the energy formula, activity factor, goal adjustment, and range.
- Protein/carbohydrate use 4 kcal/g and fat uses 9 kcal/g.
- Totals derive from structured ingredient rows, not prose.
- Unsupported values carry estimated=true.
Store canonical grams, milliliters, kilograms, centimeters, and kilocalories; display metric or US customary units. Preserve locale, currency, and timezone. Validate nonnegative quantities and rescan all substitutions for allergens.
