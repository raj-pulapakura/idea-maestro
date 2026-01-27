## Monetization and Credits Model

### High-level Approach

Idea Maestro v1 uses a **pure credits-based model**:

- Users **buy credits** from Idea Maestro.
- Credits are consumed when agents work on ideas (chat + document edits).
- You pay LLM providers using your own API keys in the backend.
- Pricing is designed so:
  - You cover LLM + infra costs.
  - You earn a healthy margin per credit.

No BYOK in v1 – this keeps onboarding and architecture simple.

### Why Pure Credits?

**Upsides:**

- Simpler onboarding:
  - No need for users to manage API keys or providers.
  - “Sign up → buy credits (or get free ones) → start using.”
- Direct, usage-based revenue:
  - Clear mapping between app usage and revenue.
  - Easier financial modeling and forecasting.
- Better product control:
  - You choose providers and models.
  - You can optimize for cost/quality trade-offs behind the scenes.

**Tradeoffs:**

- Higher end-user cost vs BYOK (they pay your markup).
- You bear the underlying LLM cost and need to manage margins.
- Power users who want BYOK flexibility aren’t served in v1 (can be added later).

### Credits Design

#### Credit Packs (example numbers)

- **Starter:** 100 credits – $5
- **Builder:** 500 credits – $20 (20% bonus over Starter)
- **Pro:** 2,000 credits – $70 (30% bonus)

Exact numbers can be tuned, but the pattern is:

- Small pack to try the app.
- Mid pack for casual builders.
- Larger discounted pack for power users.

#### What Costs Credits?

Conceptual mapping (these are UX numbers, not raw token units):

- **Agent message (simple)**: 1 credit  
  - Short responses, small document tweaks.
- **Agent message (complex)**: 2–3 credits  
  - Long reasoning, multiple document edits.
- **Document generation/edit**: 2 credits per major document operation.
- **Full refinement session**: ~20–30 credits total  
  - From initial idea to well-structured docs.

Under the hood, credits should loosely map to token usage so margin stays consistent.

### Example Unit Economics

Assume:

- Your average token cost per full session ≈ $0.50.
- You price a full session at ≈ 25 credits.
- Pack pricing implies:
  - 100 credits = $5 → $0.05/credit.
  - 25 credits (1 session) ≈ $1.25 revenue.
  - Gross margin per session ≈ $0.75 (before infra + Stripe fees).

You can adjust costs/credit and credits/operation to target a specific margin.

### Free Credits and Onboarding

- On sign up, users get **e.g., 100 free credits**:
  - Enough for 2–3 smaller sessions or 1–2 full refinement passes.
  - Creates a strong “try before you buy” experience.
- These free credits can optionally **expire** (e.g., 30–90 days) to encourage early engagement.

### Credit Ledger & Enforcement

Key mechanics:

- **Balance**:
  - Stored per user (e.g., `user_tiers.credits_balance`).
- **Ledger**:
  - `credit_transactions` table:
    - `amount` (+ for purchases, – for usage).
    - `type` (`purchase`, `usage`, `bonus`, `refund`).
    - `session_id` for tying usage to sessions.
- **Spending rules**:
  - Before an agent takes an action, the backend:
    - Computes estimated credit cost.
    - Checks balance.
    - Throws a controlled error if insufficient credits.
  - Frontend handles this by:
    - Showing “Buy credits” modal.
    - Allowing user to cancel or top up.

### Payments (Stripe)

- Use Stripe for:
  - Selling credit packs.
  - (Optionally later) subscriptions that include monthly credits.
- Flow:
  1. User chooses pack (e.g., 500 credits for $20).
  2. Create a PaymentIntent / Checkout Session in Stripe.
  3. On successful payment (via webhook):
     - Add credits to user balance.
     - Record a `credit_transactions` row (`type = 'purchase'`).

### Future Extensions

- **Subscriptions**:
  - e.g., $29/month with 1,000 credits included.
  - Overages charged via one-off credit packs.
- **Team plans**:
  - Shared credit pool across a workspace.
  - Per-member usage stats.
- **BYOK (later)**:
  - “Advanced” users can opt-out of credit costs for core agent work.
  - Credits still used for premium features (e.g., exports, comparison mode).


