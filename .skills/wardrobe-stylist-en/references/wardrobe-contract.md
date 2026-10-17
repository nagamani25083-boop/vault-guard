# Wardrobe Data Contract
Core records: profile, item, look, schedule, wearLog, trip, shoppingGap.
Every look references existing itemIds. Item fields include category, colors, material, seasons, formality, status, image, source, and confirmed. Image tags remain confirmed=false until reviewed.
Deleting an item marks dependent looks for repair. Deleting an image removes Storage and database references. Care states are clean, worn, laundry, and unavailable. Preserve locale-specific size systems and explicit conversions.
