# Design Data Contract
Core records: project, constraint, room, option, item, budgetLine, visualization.
constraint.confidence is confirmed, drawing, inferred, or verify. Immutable constraints never appear as removal recommendations.
Store canonical metric dimensions and convert for display. Preserve locale, currency, and unit system. Budgets are ranges derived from line items. Visualization versions reference option_id and never overwrite a source.
