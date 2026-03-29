# npm SDK Publishing Guide

Guide for publishing and managing the `@deckforge/sdk` TypeScript package on npm.

## Package Overview

- **Name:** `@deckforge/sdk`
- **Location:** `sdk/` directory in the repo
- **Current Version:** 0.1.0
- **Registry:** [npmjs.com](https://www.npmjs.com/package/@deckforge/sdk)
- **Outputs:** `dist/index.js` (ESM), `dist/index.cjs` (CJS), `dist/index.d.ts` (types)

## Prerequisites

1. npm account with access to the `@deckforge` scope
2. `NPM_TOKEN` configured as a GitHub repository secret (for automated publishing)
3. Node.js 20+ installed locally (for manual publishing)

### Getting npm Access

```bash
# Login to npm
npm login

# If @deckforge scope doesn't exist yet, the first publish creates it
# Ensure your account has publish access to the org/scope
```

## Automated Publishing (Recommended)

The repository includes `.github/workflows/publish-sdk.yml` which handles testing, building, and publishing automatically.

### Steps

```bash
cd sdk

# 1. Bump the version (choose: patch, minor, or major)
npm version patch   # 0.1.0 -> 0.1.1
npm version minor   # 0.1.0 -> 0.2.0
npm version major   # 0.1.0 -> 1.0.0

# 2. Create a git tag matching the sdk-v* pattern
git tag sdk-v$(node -p "require('./package.json').version")

# 3. Push the commit and tag
git push origin main --tags
```

The workflow triggers on `sdk-v*` tags and:
1. Runs `npm test` (vitest)
2. Runs `npm run typecheck` (tsc --noEmit)
3. Runs `npm run build` (tsup)
4. Publishes with `npm publish --provenance --access public`

The `--provenance` flag creates a verifiable link between the published package and the source commit (npm supply chain security).

### Workflow Triggers

| Trigger | Action |
|---------|--------|
| Push `sdk-v*` tag | Full test + build + publish to npm |
| PR modifying `sdk/**` | Test + build only (no publish) |

## Manual Publishing

For emergency releases or when CI is unavailable:

```bash
cd sdk

# 1. Install dependencies
npm ci

# 2. Run tests
npm test

# 3. Type check
npm run typecheck

# 4. Build
npm run build

# 5. Publish (requires npm login)
npm publish --provenance --access public
```

## Verify Published Package

```bash
# Check package info on npm
npm info @deckforge/sdk

# Verify the latest version
npm view @deckforge/sdk version

# Test installation in a fresh project
mkdir /tmp/test-sdk && cd /tmp/test-sdk
npm init -y
npm install @deckforge/sdk
node -e "const { DeckForge } = require('@deckforge/sdk'); console.log('OK')"
```

## Version Strategy

Follow [semantic versioning](https://semver.org/):

| Change Type | Version Bump | Example |
|------------|-------------|---------|
| Bug fixes, typos | `patch` | 0.1.0 -> 0.1.1 |
| New features (backward-compatible) | `minor` | 0.1.0 -> 0.2.0 |
| Breaking API changes | `major` | 0.1.0 -> 1.0.0 |

**Current strategy:**
- Pre-1.0: Breaking changes allowed in minor versions (0.x.0)
- 1.0.0 release: When the API is stable and battle-tested in production
- Post-1.0: Strict semver compliance

## Package Contents

The published package includes only the `dist/` directory (configured in `package.json` `files` field):

```
@deckforge/sdk/
  dist/
    index.js      # ESM module
    index.cjs     # CommonJS module
    index.d.ts    # TypeScript declarations
  package.json
  README.md
```

## GitHub Secret Setup

For the automated workflow, add `NPM_TOKEN` to your GitHub repository:

1. Generate an npm access token:
   - Go to [npmjs.com](https://www.npmjs.com) > Access Tokens > Generate New Token
   - Select **Automation** type (bypass 2FA for CI)
2. In GitHub repo settings:
   - Go to **Settings** > **Secrets and variables** > **Actions**
   - Add `NPM_TOKEN` with the generated token value

## Troubleshooting

**"You must be logged in to publish"**
- Verify `NPM_TOKEN` is set in GitHub secrets
- For manual publish: run `npm login` first

**"Cannot publish over existing version"**
- Bump the version with `npm version patch/minor/major` before publishing
- npm does not allow re-publishing the same version

**"Package name not available"**
- The `@deckforge` scope must be created first (happens on first publish)
- Ensure your npm account owns or has access to the scope

**Build fails in CI**
- Check that `sdk/package.json` has all required devDependencies
- Verify `tsup` config produces all three outputs (ESM, CJS, types)
