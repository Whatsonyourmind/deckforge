# x402 USDC Payment Setup

Guide for configuring x402 machine-to-machine payments on DeckForge.

## What is x402?

[x402](https://x402.org) is a machine-to-machine payment protocol that enables AI agents to pay per API call using USDC stablecoin on Base L2. When enabled, agents that lack a subscription can pay per-call in USDC -- the HTTP 402 Payment Required response tells the agent exactly what to pay and how.

**Why x402?**
- AI agents can autonomously pay for API access without human-managed subscriptions
- Per-call pricing aligns cost with usage (no monthly commitments)
- USDC on Base L2 means low transaction fees (~$0.001 per tx)
- Standard protocol -- agents that support x402 work with any x402-enabled API

## 1. Wallet Setup

Create an Ethereum-compatible wallet to receive USDC payments.

### Using MetaMask

1. Install [MetaMask](https://metamask.io) browser extension
2. Create or import a wallet
3. Add the **Base** network:
   - Network Name: `Base`
   - RPC URL: `https://mainnet.base.org`
   - Chain ID: `8453`
   - Currency Symbol: `ETH`
   - Block Explorer: `https://basescan.org`
4. Copy your wallet address (format: `0x...`)

### Using Coinbase Wallet

1. Install [Coinbase Wallet](https://www.coinbase.com/wallet)
2. Create a wallet
3. Switch to the Base network
4. Copy your wallet address

### Other Wallets

Any EVM-compatible wallet works (Rabby, Rainbow, Frame, etc.). Just switch to the Base network (Chain ID 8453) and copy the address.

## 2. Configure DeckForge

### Production (Fly.io)

```bash
fly secrets set \
  DECKFORGE_X402_ENABLED=true \
  DECKFORGE_X402_WALLET_ADDRESS="0xYOUR_WALLET_ADDRESS" \
  --app deckforge-api
```

### Local Development (.env)

```bash
# Add to .env file
DECKFORGE_X402_ENABLED=true
DECKFORGE_X402_WALLET_ADDRESS=0xYOUR_WALLET_ADDRESS
```

## 3. Per-Call Pricing

When x402 is enabled, the following pricing applies (decision [09-02]):

| Endpoint | USDC Price | Description |
|----------|-----------|-------------|
| `POST /v1/render` | $0.05 | Render IR to PPTX/Google Slides |
| `POST /v1/generate` | $0.15 | Generate slides from natural language |
| `GET /v1/health` | Free | Health check |
| `GET /v1/themes` | Free | List themes |
| `GET /v1/slide-types` | Free | List slide types |
| `GET /v1/pricing` | Free | View pricing info |

Pricing is also available programmatically via `GET /v1/pricing`.

## 4. x402 Facilitator

DeckForge uses the default x402 facilitator at `https://x402.org/facilitator` for payment verification and settlement.

The facilitator:
1. Receives the payment proof from the agent
2. Verifies the USDC transfer on Base
3. Confirms payment to DeckForge
4. DeckForge processes the API request

### Custom Facilitator (Advanced)

To use a custom facilitator:

```bash
fly secrets set \
  DECKFORGE_X402_FACILITATOR_URL="https://your-facilitator.com" \
  --app deckforge-api
```

## 5. How It Works

When an AI agent calls a paid endpoint without a subscription API key:

1. **402 Response:** DeckForge returns HTTP `402 Payment Required` with headers:
   - `X-Payment-Address`: Your wallet address
   - `X-Payment-Amount`: Required USDC amount
   - `X-Payment-Network`: `eip155:8453` (Base Mainnet)
   - `X-Facilitator-URL`: The facilitator endpoint

2. **Agent Pays:** The agent sends USDC to the facilitator, which forwards it to your wallet.

3. **Retry with Proof:** The agent retries the original request with a `X-Payment-Proof` header containing the transaction proof.

4. **Request Processed:** DeckForge verifies the payment via the facilitator and processes the API request normally.

x402 payments bypass rate limiting -- per-call payment is inherently self-throttling.

## 6. Testing with Testnet

For development and testing, use Base Sepolia testnet:

### Get Test USDC

1. Get Base Sepolia ETH from a [faucet](https://www.alchemy.com/faucets/base-sepolia)
2. Get test USDC from the [Circle faucet](https://faucet.circle.com/) (select Base Sepolia)

### Configure for Testnet

```bash
# In .env or fly secrets
DECKFORGE_X402_NETWORK=eip155:84532  # Base Sepolia chain ID
DECKFORGE_X402_WALLET_ADDRESS=0xYOUR_TEST_WALLET
DECKFORGE_X402_ENABLED=true
```

### Verify

```bash
# This should return 402 with payment details (no API key, no payment proof)
curl -v https://localhost:8000/v1/render \
  -H "Content-Type: application/json" \
  -d '{"title":"test","slides":[]}'
```

## 7. Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DECKFORGE_X402_ENABLED` | No | `false` | Enable x402 payment protocol |
| `DECKFORGE_X402_WALLET_ADDRESS` | If enabled | `None` | USDC receiving wallet on Base |
| `DECKFORGE_X402_FACILITATOR_URL` | No | `https://x402.org/facilitator` | x402 facilitator endpoint |
| `DECKFORGE_X402_NETWORK` | No | `eip155:8453` | Base Mainnet (or `eip155:84532` for Sepolia testnet) |

## 8. Revenue Tracking

x402 payments are tracked separately from Stripe subscriptions in the analytics dashboard:

```bash
# View payment analytics (requires admin API key)
curl -H "Authorization: Bearer dk_live_ADMIN_KEY" \
  https://deckforge-api.fly.dev/v1/analytics/revenue
```

Revenue split between Stripe subscriptions and x402 per-call payments is visible on the analytics dashboard.
