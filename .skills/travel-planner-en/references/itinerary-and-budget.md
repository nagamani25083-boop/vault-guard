# Itinerary and Budget Guidelines

## Itinerary planning

- Group activities by geography and include travel, queues, meals, and rest buffers.
- Respect the user's relaxed, moderate, or packed pace without treating activity count as a hard target.
- Mark opening hours and reservation requirements as unresolved until verified.
- Use destination local time and show the timezone.
- Provide weather, transit-delay, and closure alternatives.
- Adapt for children, older travelers, mobility needs, allergies, and health constraints.
- Never turn template activities, restaurants, or prices into booking results.

## Budget fields

```json
{
  "total": 2500,
  "currency": "CNY",
  "travelers": 2,
  "includes_flights": false,
  "includes_accommodation": true,
  "includes_taxes": false,
  "includes_insurance": false,
  "exchange_rate_source": null,
  "exchange_rate_date": null,
  "assumptions": []
}
```

## Budget rules

- Default allocations are overridable templates, not current market facts.
- Add only same-currency amounts unless a dated exchange-rate source is provided.
- Show currency, traveler/unit basis, taxes, service fees, refund terms, and lookup date for estimates.
- State whether flights, accommodation, taxes, and insurance are included.
- Treat contingency as a reasoned suggestion, not a universal percentage.

## Delivery checklist

- [ ] Dates and timezones are explicit
- [ ] Travel and rest buffers are included
- [ ] Estimates include currency and assumptions
- [ ] Currencies are not combined without a source
- [ ] Facts, suggestions, estimates, and unresolved items are separated
- [ ] No automatic booking, payment, or lowest-price promise
