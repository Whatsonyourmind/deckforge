# DeckForge — Stripe Products (Live)

Created 2026-03-31 via Stripe API.

## Products

| Tier | Product ID | Price ID | Amount | Interval |
|------|-----------|----------|--------|----------|
| Starter | `prod_UFZZuga60AkfYg` | `price_1TH4QVCS2n1FZOzcfoNI2jPK` | $0 | /month |
| Pro | `prod_UFZZ311aRnrTOC` | `price_1TH4QfCS2n1FZOzcyV41Zej0` | $79 | /month |
| Enterprise | `prod_UFZZZtWqTKQErS` | *(custom pricing)* | Custom | Custom |

## Environment Variables

```env
DECKFORGE_STRIPE_STARTER_PRICE_ID=price_1TH4QVCS2n1FZOzcfoNI2jPK
DECKFORGE_STRIPE_PRO_PRICE_ID=price_1TH4QfCS2n1FZOzcyV41Zej0
DECKFORGE_STRIPE_STARTER_PRODUCT_ID=prod_UFZZuga60AkfYg
DECKFORGE_STRIPE_PRO_PRODUCT_ID=prod_UFZZ311aRnrTOC
DECKFORGE_STRIPE_ENTERPRISE_PRODUCT_ID=prod_UFZZZtWqTKQErS
```

## Tier Features

- **Starter (Free)**: 5 decks/month, 15 themes, community support
- **Pro ($79/mo)**: Unlimited decks, all 32 slide types, priority rendering, email support
- **Enterprise (Custom)**: Custom volume, SLA, dedicated support, brand kit management, SSO
