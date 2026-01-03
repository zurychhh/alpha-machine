# 🧪 Universal E2E Testing Framework
## Playwright MCP + Claude Code Integration

**Version**: 1.0.0 | **Last Updated**: 2025-12-21  
**Purpose**: Zero-code E2E testing using AI + browser automation for any web project

---

## 📋 Table of Contents

1. [Why This Approach](#why-this-approach)
2. [Quick Start (5 minutes)](#quick-start)
3. [Core Concepts](#core-concepts)
4. [Testing Standards](#testing-standards)
5. [Universal Test Templates](#universal-test-templates)
6. [Project Type Examples](#project-type-examples)
7. [CI/CD Integration](#cicd-integration)
8. [Advanced Patterns](#advanced-patterns)
9. [Troubleshooting](#troubleshooting)

---

## Why This Approach

### Traditional E2E Testing Problems

| Problem | Impact |
|---------|--------|
| Writing test scripts manually | Hours of developer time |
| Maintaining selectors | Tests break with every UI change |
| Complex infrastructure | CI/CD setup, browser farms |
| Flaky tests | False negatives, lost trust |
| Learning curve | Cypress/Selenium/Playwright syntax |

### Playwright MCP + Claude Code Solution

```
┌─────────────────────────────────────────────────────────────┐
│  YOU: "Test login flow with invalid password"               │
│                          ↓                                   │
│  CLAUDE CODE: Understands intent, plans test                │
│                          ↓                                   │
│  PLAYWRIGHT MCP: Executes in real browser                   │
│                          ↓                                   │
│  RESULT: Detailed report with screenshots                   │
└─────────────────────────────────────────────────────────────┘
```

**Benefits:**
- ✅ **Zero code** - describe tests in natural language
- ✅ **Self-healing** - AI adapts to UI changes
- ✅ **Free** - no SaaS subscriptions needed
- ✅ **Fast** - tests run in seconds, not minutes
- ✅ **Debuggable** - AI explains what it sees and does

---

## Quick Start

### Step 1: Install Playwright MCP (2 min)

```bash
# Global installation
npm install -g @playwright/mcp@latest

# Verify
npx @playwright/mcp --version
```

### Step 2: Configure Claude Code (1 min)

**For Claude Code CLI:**
```bash
claude mcp add --transport stdio playwright npx @playwright/mcp@latest
```

**For Claude Desktop (macOS):**
```bash
# Edit config file
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Add:
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

**For Claude Desktop (Windows):**
```
%APPDATA%\Claude\claude_desktop_config.json
```

### Step 3: Restart & Test (2 min)

Restart Claude Code/Desktop, then say:

```
Use Playwright to navigate to https://example.com 
and tell me the page title.
```

✅ If you see "Example Domain" - you're ready!

### Step 4: Create Project Config (optional)

Create `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "playwright": {
      "type": "stdio",
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

**Useful flags:**
| Flag | Purpose |
|------|---------|
| `--headless` | Run without visible browser (CI) |
| `--browser chromium\|firefox\|webkit` | Specific browser |
| `--viewport 1280x720` | Custom viewport size |
| `--save-trace` | Save trace for debugging |
| `--save-video 800x600` | Record video |

---

## Core Concepts

### How Playwright MCP Works

```
┌──────────────┐     MCP Protocol      ┌──────────────┐
│              │ ──────────────────────▶│              │
│  Claude Code │                        │  Playwright  │
│    (LLM)     │ ◀──────────────────────│  MCP Server  │
│              │   Accessibility Tree   │              │
└──────────────┘                        └──────────────┘
                                               │
                                               ▼
                                        ┌──────────────┐
                                        │   Browser    │
                                        │  (Chromium)  │
                                        └──────────────┘
```

**Key insight:** Playwright MCP uses the **accessibility tree**, not screenshots. This means:
- Faster than vision-based approaches
- More reliable element identification
- Works with any accessible web UI
- No need for visual AI models

### Natural Language → Browser Actions

| You Say | Claude Does |
|---------|-------------|
| "Go to example.com" | `page.goto('https://example.com')` |
| "Click the login button" | Finds button by text/role, clicks |
| "Type 'hello' in the search box" | Locates input, types text |
| "Wait for the results to load" | Waits for network idle + DOM |
| "Take a screenshot" | Captures and returns image |
| "Check for console errors" | Monitors browser console |

### Accessibility Tree Navigation

Claude sees your page like this:
```
- document
  - heading "Welcome"
  - form
    - textbox "Email" [focused]
    - textbox "Password"
    - button "Sign In"
  - link "Forgot password?"
```

This is why you should describe elements by their **role and text**, not CSS selectors:
```
✅ "Click the Sign In button"
✅ "Type in the Email field"
❌ "Click element with class .btn-primary"
❌ "Click the third div inside the form"
```

---

## Testing Standards

### Test Categories

#### 🔴 Critical Path (CP) - MUST PASS
Core user journeys that generate revenue or are essential for app function.

| ID | Test | Example |
|----|------|---------|
| CP-01 | Authentication | Login, logout, password reset |
| CP-02 | Core Feature | Main value proposition works |
| CP-03 | Payment Flow | Checkout, subscription, billing |
| CP-04 | Data Persistence | Save, load, delete operations |
| CP-05 | Error Handling | Graceful failures, error messages |

#### 🟡 Regression (RG) - SHOULD PASS
Ensure existing features still work after changes.

| ID | Test | Example |
|----|------|---------|
| RG-01 | Navigation | All menu items, links work |
| RG-02 | Forms | Validation, submission, feedback |
| RG-03 | UI Components | Modals, dropdowns, tooltips |
| RG-04 | Filters/Search | Sorting, filtering, pagination |
| RG-05 | Responsive | Mobile, tablet, desktop layouts |

#### 🟢 Edge Cases (EC) - NICE TO HAVE
Uncommon scenarios that should still work.

| ID | Test | Example |
|----|------|---------|
| EC-01 | Empty States | No data, first-time user |
| EC-02 | Large Data | 1000+ items, long text |
| EC-03 | Slow Network | Loading states, timeouts |
| EC-04 | Concurrent Actions | Race conditions |
| EC-05 | Browser Edge Cases | Back button, refresh, tabs |

### Test Naming Convention

```
[PROJECT]-[CATEGORY]-[NUMBER]: [Description]

Examples:
MYAPP-CP-01: User Login Flow
MYAPP-RG-03: Product Filter Dropdown
MYAPP-EC-02: Dashboard with 10,000 Items
```

### Test Documentation Template

Create `tests/E2E_TESTS.md` in your project:

```markdown
# E2E Test Suite - [PROJECT NAME]

## Environment
- **Local**: http://localhost:3000
- **Staging**: https://staging.myapp.com
- **Production**: https://myapp.com
- **Test Credentials**: See `.env.test`

## Critical Path Tests

### [PROJECT]-CP-01: User Login

**Priority**: Critical  
**Duration**: ~30 seconds  
**Last Run**: [DATE]  
**Status**: ✅ PASSING | ❌ FAILING

#### Prerequisites
- Test user exists: test@example.com / TestPass123!
- App is running

#### Steps
1. Navigate to login page
2. Enter email
3. Enter password
4. Click submit
5. Verify redirect to dashboard

#### Expected Results
- Dashboard loads within 3 seconds
- User name displayed in header
- No console errors

#### Playwright MCP Prompt
```
Use Playwright to test login:
1. Go to [APP_URL]/login
2. Type "test@example.com" in the email field
3. Type "TestPass123!" in the password field
4. Click the "Sign In" button
5. Wait for navigation to complete
6. Verify text "Welcome" appears on page
7. Check for console errors
8. Take screenshot as "login-success.png"
Report: PASS/FAIL with details
```

---

[Continue for each test...]
```

---

## Universal Test Templates

### Template 1: Authentication Flow

```markdown
## Authentication Test

Use Playwright to test [APP_NAME] authentication:

### Login (Happy Path)
1. Navigate to [LOGIN_URL]
2. Enter valid email: [TEST_EMAIL]
3. Enter valid password: [TEST_PASSWORD]
4. Click sign in button
5. Verify redirect to [DASHBOARD_URL]
6. Verify user indicator shows logged in state
7. Take screenshot

### Login (Invalid Credentials)
1. Navigate to [LOGIN_URL]
2. Enter invalid email: wrong@example.com
3. Enter any password
4. Click sign in button
5. Verify error message appears
6. Verify still on login page

### Logout
1. From authenticated state, find logout option
2. Click logout
3. Verify redirect to [LOGIN_URL] or [HOME_URL]
4. Verify user indicator shows logged out state

### Password Reset
1. Navigate to [LOGIN_URL]
2. Click "Forgot password" link
3. Enter email: [TEST_EMAIL]
4. Submit form
5. Verify confirmation message

Report: PASS/FAIL for each section
```

### Template 2: CRUD Operations

```markdown
## CRUD Test for [ENTITY_NAME]

Use Playwright to test [ENTITY_NAME] management:

### Create
1. Navigate to [ENTITY_LIST_URL]
2. Click "Add New" / "Create" button
3. Fill required fields:
   - [FIELD_1]: [VALUE_1]
   - [FIELD_2]: [VALUE_2]
4. Click save/submit
5. Verify success message
6. Verify new item appears in list

### Read
1. Navigate to [ENTITY_LIST_URL]
2. Verify list displays items
3. Click on an item
4. Verify detail view shows correct data

### Update
1. Navigate to existing item
2. Click edit button
3. Modify [FIELD_1] to new value
4. Save changes
5. Verify update reflected in UI

### Delete
1. Navigate to existing item
2. Click delete button
3. Confirm deletion in modal
4. Verify item removed from list
5. Verify cannot access deleted item URL

Report: PASS/FAIL for each operation
```

### Template 3: Form Validation

```markdown
## Form Validation Test

Use Playwright to test [FORM_NAME] validation:

### Required Fields
1. Navigate to [FORM_URL]
2. Submit empty form
3. Verify error messages for each required field:
   - [FIELD_1]: "[REQUIRED_MESSAGE]"
   - [FIELD_2]: "[REQUIRED_MESSAGE]"

### Field Format Validation
1. Enter invalid email format in email field
2. Verify email format error
3. Enter invalid phone format in phone field
4. Verify phone format error
5. Enter too-short password
6. Verify password requirements error

### Successful Submission
1. Fill all fields with valid data:
   - [FIELD_1]: [VALID_VALUE_1]
   - [FIELD_2]: [VALID_VALUE_2]
2. Submit form
3. Verify success state (message, redirect, or UI change)

Report: PASS/FAIL with specific validation messages
```

### Template 4: Navigation & Routing

```markdown
## Navigation Test

Use Playwright to test [APP_NAME] navigation:

### Main Navigation
For each menu item:
1. Click [MENU_ITEM]
2. Verify URL changes to [EXPECTED_URL]
3. Verify page content loads
4. Verify no console errors

Menu items to test:
- Home → /
- Dashboard → /dashboard
- Settings → /settings
- Profile → /profile
- [ADD MORE]

### Deep Linking
1. Navigate directly to [DEEP_URL]
2. Verify correct page loads
3. Verify all components render

### Back/Forward Navigation
1. Navigate: Home → Dashboard → Settings
2. Click browser back
3. Verify on Dashboard
4. Click browser back
5. Verify on Home
6. Click browser forward
7. Verify on Dashboard

### 404 Handling
1. Navigate to /nonexistent-page-xyz
2. Verify 404 page displays
3. Verify navigation still works from 404 page

Report: PASS/FAIL for each navigation test
```

### Template 5: API Integration

```markdown
## API Integration Test

Use Playwright to verify [APP_NAME] API integration:

### Data Loading
1. Navigate to [PAGE_WITH_API_DATA]
2. Wait for data to load (loading indicator disappears)
3. Verify data displays correctly:
   - [DATA_POINT_1] is visible
   - [DATA_POINT_2] is visible
4. Measure load time (should be < [X] seconds)

### Real-time Updates
1. Navigate to [REALTIME_PAGE]
2. Trigger external data change (if possible)
3. Verify UI updates without refresh

### Error States
1. [Simulate API failure if possible]
2. Verify error message displays
3. Verify retry option available
4. Verify app doesn't crash

### Pagination/Infinite Scroll
1. Navigate to [PAGINATED_LIST]
2. Scroll to bottom / click "Load More"
3. Verify additional items load
4. Verify no duplicates

Report: PASS/FAIL with timing metrics
```

### Template 6: Responsive Design

```markdown
## Responsive Design Test

Use Playwright to test [APP_NAME] on different viewports:

### Desktop (1920x1080)
1. Set viewport to 1920x1080
2. Navigate to [KEY_PAGES]
3. Verify layout is correct
4. Take screenshots

### Laptop (1366x768)
1. Set viewport to 1366x768
2. Navigate to [KEY_PAGES]
3. Verify layout adapts
4. Take screenshots

### Tablet (768x1024)
1. Set viewport to 768x1024
2. Navigate to [KEY_PAGES]
3. Verify mobile menu appears (if applicable)
4. Verify touch-friendly spacing
5. Take screenshots

### Mobile (375x667)
1. Set viewport to 375x667
2. Navigate to [KEY_PAGES]
3. Verify hamburger menu works
4. Verify forms are usable
5. Verify no horizontal scroll
6. Take screenshots

Report: PASS/FAIL with screenshots for each viewport
```

### Template 7: Performance Baseline

```markdown
## Performance Test

Use Playwright to measure [APP_NAME] performance:

### Page Load Times
For each critical page:
1. Clear cache
2. Navigate to page
3. Measure time to:
   - First Contentful Paint
   - DOM Content Loaded
   - Full Load
4. Compare to targets:
   - FCP: < 1.5s
   - DCL: < 2.5s
   - Full: < 4s

Pages to test:
- Home: [URL]
- Dashboard: [URL]
- [OTHER_CRITICAL_PAGES]

### Interaction Response
1. Navigate to interactive page
2. Click button/trigger action
3. Measure time to visual feedback
4. Target: < 100ms for feedback, < 1s for completion

### Memory Leaks (Long Session)
1. Navigate around app for 20 actions
2. Return to starting page
3. Check for degraded performance
4. Note any memory warnings in console

Report: All timing metrics vs targets
```

---

## Project Type Examples

### SaaS Application

```markdown
# SaaS E2E Test Suite

## Critical Path
1. **Signup Flow**: New user can create account
2. **Subscription**: User can subscribe to paid plan
3. **Core Feature**: Main product feature works
4. **Team Invite**: Can invite team members
5. **Billing**: Can update payment, view invoices

## Key Prompts

### Test Signup
Use Playwright:
1. Go to [APP]/signup
2. Fill name, email, password
3. Submit and verify email confirmation page
4. [If email confirmation required, note manual step]

### Test Subscription Upgrade
Use Playwright:
1. Login as free user
2. Navigate to billing/upgrade
3. Select Pro plan
4. Enter test card: 4242424242424242, any future date, any CVC
5. Submit payment
6. Verify Pro badge/features unlocked
```

### E-commerce Store

```markdown
# E-commerce E2E Test Suite

## Critical Path
1. **Product Browse**: Can view products, filter, search
2. **Add to Cart**: Products add to cart correctly
3. **Checkout**: Complete purchase flow
4. **Account**: Login, view orders, manage addresses
5. **Inventory**: Out-of-stock handling

## Key Prompts

### Test Add to Cart
Use Playwright:
1. Go to [STORE]/products
2. Click on first product
3. Select size/variant if applicable
4. Click "Add to Cart"
5. Verify cart count increases
6. Navigate to cart
7. Verify product in cart with correct details

### Test Checkout
Use Playwright:
1. With item in cart, go to checkout
2. Fill shipping: [TEST_ADDRESS]
3. Select shipping method
4. Fill payment: test card 4242...
5. Place order
6. Verify confirmation page with order number
```

### Content/Blog Platform

```markdown
# Content Platform E2E Test Suite

## Critical Path
1. **Content Display**: Articles render correctly
2. **Search**: Can find content
3. **Comments**: Can post and view comments
4. **Author Pages**: Author profiles work
5. **Sharing**: Social sharing works

## Key Prompts

### Test Article View
Use Playwright:
1. Go to [SITE]/articles
2. Click on first article
3. Verify: title, author, date, body content visible
4. Scroll to bottom
5. Verify related articles section
6. Test any embedded media loads
```

### Admin Dashboard

```markdown
# Admin Dashboard E2E Test Suite

## Critical Path
1. **Login Security**: Only admins can access
2. **Data Tables**: CRUD on all entities
3. **Reports**: Reports generate correctly
4. **User Management**: Can manage users
5. **Settings**: System settings persist

## Key Prompts

### Test Admin Access Control
Use Playwright:
1. Go to [APP]/admin (not logged in)
2. Verify redirect to login
3. Login as regular user
4. Try to access /admin
5. Verify access denied
6. Login as admin
7. Verify admin dashboard accessible

### Test Data Export
Use Playwright:
1. Login as admin
2. Navigate to reports section
3. Select date range
4. Click export
5. Verify download initiates (or verify export complete message)
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'  # Weekly Monday 6am

jobs:
  e2e:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          
      - name: Install dependencies
        run: npm ci
        
      - name: Install Playwright
        run: npx playwright install --with-deps chromium
        
      - name: Start app
        run: npm start &
        env:
          NODE_ENV: test
          
      - name: Wait for app
        run: npx wait-on http://localhost:3000 --timeout 60000
        
      - name: Run Playwright tests
        run: npx playwright test
        env:
          BASE_URL: http://localhost:3000
          TEST_USER: ${{ secrets.TEST_USER }}
          TEST_PASS: ${{ secrets.TEST_PASS }}
          
      - name: Upload results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 14
```

### GitLab CI

```yaml
# .gitlab-ci.yml
e2e-tests:
  stage: test
  image: mcr.microsoft.com/playwright:v1.40.0-focal
  script:
    - npm ci
    - npm start &
    - npx wait-on http://localhost:3000
    - npx playwright test
  artifacts:
    when: always
    paths:
      - playwright-report/
    expire_in: 1 week
  only:
    - main
    - merge_requests
```

### Notifications

#### Slack

```typescript
// notify-slack.ts
interface TestResults {
  passed: boolean;
  total: number;
  failed: number;
  duration: number;
  project: string;
  environment: string;
}

async function notifySlack(results: TestResults) {
  const webhook = process.env.SLACK_WEBHOOK_URL;
  
  await fetch(webhook, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: results.passed 
        ? `✅ E2E Tests Passed (${results.total} tests)`
        : `❌ E2E Tests Failed (${results.failed}/${results.total})`,
      attachments: [{
        color: results.passed ? 'good' : 'danger',
        fields: [
          { title: 'Project', value: results.project, short: true },
          { title: 'Duration', value: `${results.duration}s`, short: true },
          { title: 'Environment', value: results.environment, short: true },
        ]
      }]
    })
  });
}
```

#### Discord

```typescript
// notify-discord.ts
async function notifyDiscord(results: TestResults) {
  const webhook = process.env.DISCORD_WEBHOOK_URL;
  
  await fetch(webhook, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      embeds: [{
        title: results.passed ? '✅ Tests Passed' : '❌ Tests Failed',
        color: results.passed ? 0x00ff00 : 0xff0000,
        fields: [
          { name: 'Total', value: results.total.toString(), inline: true },
          { name: 'Failed', value: results.failed.toString(), inline: true },
          { name: 'Duration', value: `${results.duration}s`, inline: true },
        ]
      }]
    })
  });
}
```

---

## Advanced Patterns

### Visual Regression Testing

```markdown
Use Playwright for visual regression:

1. Navigate to [PAGE]
2. Take screenshot as "baseline-[PAGE_NAME].png"
3. [After code changes]
4. Take new screenshot as "current-[PAGE_NAME].png"
5. Compare with baseline
6. Report any pixel differences > 0.1%

Note: Store baselines in version control
```

### Multi-User Scenarios

```markdown
Use Playwright to test multi-user interaction:

### Browser 1 (User A):
1. Login as User A
2. Create shared item
3. Wait for User B confirmation

### Browser 2 (User B):
1. Login as User B
2. Navigate to shared items
3. Verify User A's item visible
4. Interact with item

### Verify:
- Real-time updates work
- Permissions respected
- No data conflicts
```

### State Persistence Testing

```markdown
Use Playwright to test state persistence:

### Session 1:
1. Login
2. Create data: [SPECIFIC_DATA]
3. Modify settings: [SPECIFIC_SETTINGS]
4. Close browser (end session)

### Session 2:
1. Open new browser
2. Login as same user
3. Verify data persists: [SPECIFIC_DATA]
4. Verify settings persist: [SPECIFIC_SETTINGS]

Report: Data integrity across sessions
```

### Accessibility Testing

```markdown
Use Playwright for accessibility checks:

1. Navigate to [PAGE]
2. Check for:
   - All images have alt text
   - All form fields have labels
   - Heading hierarchy is correct (h1 → h2 → h3)
   - Interactive elements are keyboard accessible
   - Color contrast is sufficient
3. Tab through entire page
4. Verify focus indicators visible
5. Test with screen reader simulation

Report: Accessibility violations found
```

---

## Troubleshooting

### Common Issues

#### "MCP server not found"
```bash
# Reinstall
npm uninstall -g @playwright/mcp
npm install -g @playwright/mcp@latest

# Restart Claude
```

#### "Cannot find element"
```
# Bad: CSS selectors
"Click .btn-primary"

# Good: Natural language
"Click the Submit button"
"Click the button that says 'Submit'"
```

#### "Timeout waiting for X"
```
# Add explicit waits
"Wait up to 30 seconds for the loading spinner to disappear"
"Wait for the text 'Success' to appear, timeout 60 seconds"
```

#### "Element not interactable"
```
# Scroll into view first
"Scroll down until you see the 'Continue' button, then click it"

# Or wait for animations
"Wait for any animations to complete, then click Submit"
```

#### OAuth/Login Loops
```
# Clear cookies first
"Clear all cookies, then navigate to [URL]"

# Or use fresh context
"Open a new browser context, then test login"
```

### Debug Mode

```
Use Playwright in debug mode:

For every action:
1. Describe what you see on the page
2. State what you're about to do
3. Do the action
4. Report the result
5. If error, take screenshot and describe DOM state

This helps me understand what's happening.
```

### Getting Help

1. **Playwright MCP Issues**: https://github.com/microsoft/playwright-mcp/issues
2. **Playwright Docs**: https://playwright.dev/docs/intro
3. **Claude Code**: https://docs.anthropic.com/claude-code

---

## Quick Reference

### Playwright MCP Prompts

| Action | Prompt |
|--------|--------|
| Navigate | "Go to [URL]" |
| Click | "Click the [DESCRIPTION] button/link" |
| Type | "Type '[TEXT]' in the [FIELD] field" |
| Select | "Select '[OPTION]' from the [DROPDOWN] dropdown" |
| Check | "Check the [CHECKBOX] checkbox" |
| Wait | "Wait for [ELEMENT/TEXT] to appear" |
| Wait (timed) | "Wait up to [X] seconds for [CONDITION]" |
| Screenshot | "Take a screenshot" |
| Viewport | "Set viewport to [WIDTH]x[HEIGHT]" |
| Scroll | "Scroll to [ELEMENT/bottom/top]" |
| Hover | "Hover over the [ELEMENT]" |
| Console | "Check for console errors" |
| Network | "Wait for network to be idle" |
| Clear | "Clear the [FIELD] field" |
| Press | "Press Enter/Tab/Escape" |
| Upload | "Upload [FILE] to the file input" |

### Pre-Deploy Checklist

```markdown
- [ ] CP-01: Authentication works
- [ ] CP-02: Core feature works
- [ ] CP-03: Payment/billing works (if applicable)
- [ ] CP-04: Data saves correctly
- [ ] CP-05: Errors handled gracefully
- [ ] No console errors on any page
- [ ] Page load < 3 seconds
- [ ] Mobile viewport tested
- [ ] Screenshots captured
- [ ] Results documented
```

### Test Results Template

```markdown
# Test Results - [DATE]

## Summary
- **Project**: [NAME]
- **Environment**: [local/staging/production]
- **Tester**: Claude Code + Playwright MCP
- **Duration**: [X] minutes
- **Result**: ✅ [X]/[Y] PASSED | ❌ [Z] FAILED

## Results

| Test ID | Test Name | Result | Duration | Notes |
|---------|-----------|--------|----------|-------|
| CP-01 | Login | ✅ | 5s | |
| CP-02 | Core Feature | ✅ | 12s | |
| CP-03 | Checkout | ❌ | 8s | Payment button unresponsive |

## Issues Found
1. [ISSUE]: [DESCRIPTION] - [SCREENSHOT]

## Next Steps
- [ ] Fix [ISSUE]
- [ ] Re-run failed tests
- [ ] Run full regression
```

---

## Document Maintenance

**Created**: 2025-12-21  
**Author**: [Your Name/Team]  
**License**: MIT (or your preference)

**Update this document when:**
- New test patterns emerge
- Playwright MCP updates significantly
- Team adopts new testing standards

---

*Remember: The goal isn't perfect tests—it's catching bugs before users do. Start with Critical Path tests, then expand coverage as your project matures.*
