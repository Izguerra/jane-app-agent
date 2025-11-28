# UI/UX Design Document
# Jane AI Voice & Chat Agent SaaS

**Version:** 1.0  
**Date:** November 22, 2025  
**Designer:** TBD  
**Status:** Draft

---

## Table of Contents

1. [Design Principles](#design-principles)
2. [Brand & Visual Identity](#brand--visual-identity)
3. [User Flows](#user-flows)
4. [Component Library](#component-library)
5. [Page Designs](#page-designs)
6. [Chat Widget](#chat-widget)
7. [Responsive Design](#responsive-design)
8. [Accessibility](#accessibility)

---

## Design Principles

### 1. Healthcare-Appropriate
- Professional, trustworthy aesthetic
- Calming colors (avoid aggressive reds/oranges)
- Clear hierarchy and readability
- HIPAA-compliant indicators visible

### 2. Practice-Owner Friendly
- Simple, not cluttered
- Clear call-to-actions
- Progress indicators for multi-step processes
- Help text and tooltips throughout

### 3. Fast & Responsive
- Skeleton loaders for async content
- Optimistic UI updates
- Real-time feedback
- <200ms perceived interaction time

### 4. Accessible
- WCAG 2.1 AA compliant
- Keyboard navigation
- Screen reader friendly
- Color contrast ratios met

### 5. Mobile-First
- Responsive across devices
- Touch-friendly targets (44x44px minimum)
- Works offline where appropriate

---

## Brand & Visual Identity

### Color Palette

**Primary Colors:**
```
Primary Blue: #2563EB (Trust, healthcare)
Primary Dark: #1E40AF
Primary Light: #60A5FA
```

**Secondary Colors:**
```
Success Green: #10B981 (Bookings, confirmations)
Warning Amber: #F59E0B (Alerts, attention)
Error Red: #EF4444 (Errors, critical actions)
```

**Neutral Colors:**
```
Gray 900: #111827 (Headlines)
Gray 700: #374151 (Body text)
Gray 500: #6B7280 (Secondary text)
Gray 300: #D1D5DB (Borders)
Gray 100: #F3F4F6 (Backgrounds)
White: #FFFFFF
```

### Typography

**Font Family:**
```css
--font-sans: 'Inter', system-ui, -apple-system, sans-serif;
--font-mono: 'JetBrains Mono', monospace;
```

**Font Sizes:**
```css
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 1.875rem;  /* 30px */
--text-4xl: 2.25rem;   /* 36px */
```

**Font Weights:**
```css
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### Spacing System

```css
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
```

### Border Radius

```css
--radius-sm: 0.25rem;   /* 4px - subtle */
--radius-md: 0.5rem;    /* 8px - standard */
--radius-lg: 0.75rem;   /* 12px - cards */
--radius-xl: 1rem;      /* 16px - modals */
--radius-full: 9999px;  /* Pills, avatars */
```

### Shadows

```css
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
```

---

## User Flows

### 1. New Customer Onboarding Flow

```
Landing Page
    ↓
Sign Up (Email + Password)
    ↓
Email Verification
    ↓
Welcome Screen (Practice Name)
    ↓
Connect Jane App (OAuth)
    ↓
Loading... (Syncing Jane Data)
    ↓
Knowledge Base Setup
    - Auto-populated from Jane
    - Add practice details
    - Upload documents (optional)
    - Build FAQ
    ↓
Configure Agent
    - Review/edit greeting
    - Set business hours
    - Enable features
    ↓
Phone Number Setup
    - Area code selection
    - Number provisioned
    - Setup instructions
    ↓
Test Your Agent
    - Test chat interface
    - Test call (optional)
    ↓
Dashboard (Onboarding Complete)
```

**Expected Time:** 10 minutes

**Key Interactions:**
- Progress bar showing 6/7 steps
- "Skip for now" option on optional steps
- "Need help?" button always visible
- Auto-save on each step

### 2. Patient Booking via Chat Flow

```
Patient visits practice website
    ↓
Sees chat widget (bottom right)
    ↓
Clicks to open
    ↓
Agent greets: "Hi! How can I help you today?"
    ↓
Patient types: "I need to book an appointment"
    ↓
Agent: "I'd be happy to help! What type of service?"
    ↓
Patient: "Massage therapy"
    ↓
Agent: "Great! When works best for you?"
    ↓
Patient: "Next Tuesday afternoon"
    ↓
Agent: "I have these times available: 2pm, 3:30pm, 4pm"
    ↓
Patient: "2pm works"
    ↓
Agent: "Perfect! May I have your name and phone?"
    ↓
Patient provides details
    ↓
Agent: "Confirmed! See you Tuesday at 2pm. Confirmation sent via SMS."
    ↓
Widget shows booking summary
```

**Key Interactions:**
- Typing indicators
- Quick reply buttons for common responses
- Date picker for selecting dates
- Time slot buttons (visual selection)
- Confirmation animation

### 3. Patient Booking via Voice Flow

```
Patient calls practice number
    ↓
Forwarded to AI agent
    ↓
Agent: "Thank you for calling [Practice Name]. I'm your AI assistant. How can I help?"
    ↓
Patient: "I need to book an appointment"
    ↓
Agent: "I'd be happy to help. What type of service are you looking for?"
    ↓
[Natural conversation continues...]
    ↓
Agent books appointment
    ↓
Agent: "All set! You'll receive a confirmation via text message shortly."
    ↓
SMS sent
    ↓
Call ends
```

**Key Interactions:**
- Natural voice conversation
- Agent handles interruptions
- Clarifying questions when needed
- Verbal confirmation before booking

---

## Component Library

### Navigation

**Top Navigation Bar**
```
┌────────────────────────────────────────────────┐
│ [Logo]  Dashboard  Analytics  Settings  [User]│
└────────────────────────────────────────────────┘
```

**Specifications:**
- Height: 64px
- Background: White with bottom border
- Logo: 32px height
- Active state: Blue underline
- User avatar: 40px circle, dropdown on click

**Sidebar Navigation (Alternative)**
```
┌─────────────┬──────────────────────────────────┐
│  [Logo]     │                                  │
│             │                                  │
│  Dashboard  │                                  │
│  Calls      │         Main Content             │
│  Chats      │                                  │
│  Knowledge  │                                  │
│  Settings   │                                  │
│             │                                  │
│  [User]     │                                  │
└─────────────┴──────────────────────────────────┘
```

**Specifications:**
- Width: 240px
- Collapsible to 64px (icons only)
- Active: Blue background, white text
- Hover: Gray background

### Cards

**Standard Card**
```
┌────────────────────────────────────┐
│  [Icon]  Title                     │
│                                    │
│  Description text here             │
│  More details                      │
│                                    │
│  [Action Button]                   │
└────────────────────────────────────┘
```

**Specifications:**
- Border radius: 12px
- Padding: 24px
- Shadow: shadow-md
- Hover: shadow-lg + slight lift

**Stat Card**
```
┌────────────────────────────────────┐
│  Total Calls                       │
│  1,234          +12% ↑            │
│  ───────────────────────────       │
│  [Mini chart/sparkline]            │
└────────────────────────────────────┘
```

**Specifications:**
- Large number: text-3xl, bold
- Trend: Green (+) or Red (-)
- Sparkline: 80px width

### Buttons

**Primary Button**
```css
.btn-primary {
  background: #2563EB;
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  hover: background: #1E40AF;
  active: scale(0.98);
}
```

**Secondary Button**
```css
.btn-secondary {
  background: white;
  border: 1px solid #D1D5DB;
  color: #374151;
  padding: 12px 24px;
  border-radius: 8px;
  hover: background: #F3F4F6;
}
```

**Danger Button**
```css
.btn-danger {
  background: #EF4444;
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  hover: background: #DC2626;
}
```

**Sizes:**
- Small: padding 8px 16px, text-sm
- Medium: padding 12px 24px, text-base (default)
- Large: padding 16px 32px, text-lg

### Forms

**Input Field**
```
┌────────────────────────────────────┐
│  Label                  (Optional) │
│  ┌──────────────────────────────┐  │
│  │ Placeholder text             │  │
│  └──────────────────────────────┘  │
│  Helper text or error message      │
└────────────────────────────────────┘
```

**Specifications:**
- Height: 44px (touch-friendly)
- Border: 1px solid gray-300
- Focus: Blue border, ring
- Error: Red border
- Success: Green border

**Select Dropdown**
```
┌────────────────────────────────────┐
│  Select option              ▼     │
└────────────────────────────────────┘
```

**Textarea**
```
┌────────────────────────────────────┐
│                                    │
│  Multiple lines of text            │
│                                    │
└────────────────────────────────────┘
```
- Min height: 100px
- Resize: vertical only

**Toggle Switch**
```
Enable feature    ( OFF )
                  ─────
```

**Radio Buttons / Checkboxes**
- 20px size
- Blue when selected
- Aligned with label baseline

### Modals

**Standard Modal**
```
        ┌──────────────────────────────┐
        │  Title                    ✕  │
        ├──────────────────────────────┤
        │                              │
        │  Modal content here          │
        │                              │
        │                              │
        ├──────────────────────────────┤
        │         [Cancel] [Confirm]   │
        └──────────────────────────────┘
```

**Specifications:**
- Max width: 600px
- Centered on screen
- Backdrop: black 50% opacity
- Border radius: 16px
- Close on backdrop click
- ESC key to close

### Tables

**Data Table**
```
┌──────────────┬──────────────┬──────────────┬─────────┐
│ Name ↑       │ Date         │ Duration     │ Actions │
├──────────────┼──────────────┼──────────────┼─────────┤
│ John Doe     │ Nov 22, 2025 │ 5:32         │ [View]  │
│ Jane Smith   │ Nov 21, 2025 │ 3:15         │ [View]  │
│ ...          │ ...          │ ...          │ ...     │
└──────────────┴──────────────┴──────────────┴─────────┘
```

**Features:**
- Sortable columns (click header)
- Hover row highlight
- Sticky header on scroll
- Pagination at bottom
- Striped rows (optional)

### Status Badges

```
[Active]   - Green background
[Pending]  - Yellow background
[Failed]   - Red background
[Inactive] - Gray background
```

**Specifications:**
- Padding: 4px 12px
- Border radius: full
- Font: text-sm, semibold
- Uppercase text

### Loading States

**Spinner**
- Circular spinner, blue color
- 24px or 32px size
- Animated rotation

**Skeleton Loader**
```
┌────────────────────────────────────┐
│  ████████          ████████        │
│  ████               ████           │
│  ██████████████     ██████████     │
└────────────────────────────────────┘
```
- Gray animated pulse
- Matches layout of actual content

**Progress Bar**
```
[███████████──────────────] 45%
```
- Blue fill
- Percentage label

---

## Page Designs

### 1. Landing Page (Public)

**Hero Section:**
```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│      24/7 AI Receptionist for Your Practice            │
│      Handle appointments, payments, and support         │
│      automatically with voice and chat                  │
│                                                         │
│      [Start Free Trial]  [Watch Demo]                  │
│                                                         │
│      ┌──────────────────────────────────────┐          │
│      │                                      │          │
│      │    [Product Screenshot/Demo]         │          │
│      │                                      │          │
│      └──────────────────────────────────────┘          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Features Section:**
```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  [Icon] Voice Calls    [Icon] Text Chat   [Icon] Jane  │
│  Natural phone         Website widget      Native       │
│  conversations         for patients        integration  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Pricing Section:**
```
┌────────────┬────────────┬────────────┐
│  Starter   │Professional│ Enterprise │
│  $99/mo    │  $199/mo   │  $399/mo   │
│            │            │            │
│  Features  │  Features  │  Features  │
│  listed    │  listed    │  listed    │
│            │            │            │
│ [Start]    │ [Start]    │ [Contact]  │
└────────────┴────────────┴────────────┘
```

### 2. Dashboard (Main View)

**Layout:**
```
┌──────────────────────────────────────────────────────┐
│  Welcome back, [Practice Name]!                      │
└──────────────────────────────────────────────────────┘

┌──────────┬──────────┬──────────┬──────────┐
│  Calls   │  Chats   │ Bookings │  Usage   │
│  147     │  223     │  92      │  156 min │
│  +12% ↑  │  +8% ↑   │  +15% ↑  │  of 200  │
└──────────┴──────────┴──────────┴──────────┘

┌────────────────────────────┬─────────────────────────┐
│  Recent Activity           │  Quick Actions          │
│  ┌──────────────────────┐  │  ┌───────────────────┐  │
│  │ Call - John Doe      │  │  │ Test Agent        │  │
│  │ 5 min ago • Booked   │  │  └───────────────────┘  │
│  └──────────────────────┘  │  ┌───────────────────┐  │
│  ┌──────────────────────┐  │  │ View Knowledge    │  │
│  │ Chat - Jane Smith    │  │  └───────────────────┘  │
│  │ 12 min ago • Inquiry │  │  ┌───────────────────┐  │
│  └──────────────────────┘  │  │ Agent Settings    │  │
│  ...                       │  └───────────────────┘  │
└────────────────────────────┴─────────────────────────┘
```

**Key Elements:**
- Personalized greeting
- Overview stats (4 cards)
- Activity feed (left 2/3)
- Quick actions (right 1/3)
- Mobile: Stacked vertically

### 3. Call/Chat Logs Page

**Layout:**
```
┌──────────────────────────────────────────────────────┐
│  Calls & Chats                    [Search] [Filter]  │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌─────┬─────────────┬──────────┬──────────┬──────┐ │
│  │Type │ Contact     │ Date     │ Duration │Action│ │
│  ├─────┼─────────────┼──────────┼──────────┼──────┤ │
│  │ 📞  │ John Doe    │ Nov 22   │ 5:32     │[View]│ │
│  │ 💬  │ Jane Smith  │ Nov 22   │ -        │[View]│ │
│  │ 📞  │ (555)123... │ Nov 21   │ 3:15     │[View]│ │
│  │ ... │ ...         │ ...      │ ...      │ ...  │ │
│  └─────┴─────────────┴──────────┴──────────┴──────┘ │
│                                                      │
│  [Previous]  Page 1 of 10  [Next]                   │
└──────────────────────────────────────────────────────┘
```

**Filter Options:**
- Date range
- Type (call/chat)
- Outcome (booked/inquiry/error)
- Duration

**Detail View (Modal):**
```
┌──────────────────────────────────────────┐
│  Call Details                         ✕  │
├──────────────────────────────────────────┤
│  Contact: John Doe                       │
│  Phone: (555) 123-4567                   │
│  Date: Nov 22, 2025 at 2:30 PM           │
│  Duration: 5:32                          │
│  Outcome: Appointment Booked             │
│                                          │
│  Transcript:                             │
│  ┌────────────────────────────────────┐  │
│  │ Agent: Thank you for calling...    │  │
│  │ John: I need an appointment...     │  │
│  │ Agent: I'd be happy to help...     │  │
│  │ ...                                │  │
│  └────────────────────────────────────┘  │
│                                          │
│  [Download] [Play Recording]             │
└──────────────────────────────────────────┘
```

### 4. Knowledge Base Management

**Layout:**
```
┌──────────────────────────────────────────────────────┐
│  Knowledge Base            [Sync Jane] [Add Document]│
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌─────────────────────┐  ┌─────────────────────┐   │
│  │ Synced from Jane    │  │ Uploaded Documents  │   │
│  │                     │  │                     │   │
│  │ ✓ 3 Practitioners   │  │ • Welcome Guide.pdf │   │
│  │ ✓ 12 Services       │  │ • Policies.docx     │   │
│  │ ✓ 2 Locations       │  │ • FAQ.txt           │   │
│  │                     │  │                     │   │
│  │ Last sync: 5m ago   │  │ [Upload More]       │   │
│  └─────────────────────┘  └─────────────────────┘   │
│                                                      │
│  Practice Information                                │
│  ┌────────────────────────────────────────────────┐  │
│  │ About Your Practice                            │  │
│  │ [Text editor with formatting]                  │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  Frequently Asked Questions                          │
│  ┌────────────────────────────────────────────────┐  │
│  │ Q: Do you accept insurance?                    │  │
│  │ A: [Answer...]                                 │  │
│  │ [Edit] [Delete]                                │  │
│  └────────────────────────────────────────────────┘  │
│  [+ Add FAQ]                                         │
│                                                      │
│  [Test Search] - Preview what your agent knows      │
└──────────────────────────────────────────────────────┘
```

### 5. Agent Configuration

**Layout:**
```
┌──────────────────────────────────────────────────────┐
│  Agent Settings                                      │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Voice & Personality                                 │
│  ┌────────────────────────────────────────────────┐  │
│  │ Voice: [Female - Professional ▼]               │  │
│  │ Speed: [─────●────] Normal                     │  │
│  │ Greeting: "Thank you for calling..."           │  │
│  │ [Preview Voice]                                │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  Business Hours                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │ Monday    9:00 AM - 5:00 PM  [Toggle]          │  │
│  │ Tuesday   9:00 AM - 5:00 PM  [Toggle]          │  │
│  │ ...                                            │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  Enabled Features                                    │
│  ┌────────────────────────────────────────────────┐  │
│  │ [✓] Appointment Booking                        │  │
│  │ [✓] Answer Questions                           │  │
│  │ [ ] Payment Handling                           │  │
│  │ [✓] Send SMS Confirmations                     │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  [Save Changes]                                      │
└──────────────────────────────────────────────────────┘
```

### 6. Analytics Dashboard

**Layout:**
```
┌──────────────────────────────────────────────────────┐
│  Analytics                     [Last 30 Days ▼]      │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │         Calls & Chats Over Time                │  │
│  │  [Line chart showing volume trends]            │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌────────────────┬────────────────┬──────────────┐  │
│  │ Booking Rate   │ Avg Duration   │ Success Rate │  │
│  │ 87%            │ 4:23           │ 94%          │  │
│  └────────────────┴────────────────┴──────────────┘  │
│                                                      │
│  ┌─────────────────────┐  ┌─────────────────────┐   │
│  │ Top Questions       │  │ Peak Hours          │   │
│  │ 1. Office hours     │  │ [Bar chart]         │   │
│  │ 2. Appointment      │  │                     │   │
│  │ 3. Insurance        │  │                     │   │
│  └─────────────────────┘  └─────────────────────┘   │
│                                                      │
│  [Export Report]                                     │
└──────────────────────────────────────────────────────┘
```

---

## Chat Widget

### Widget Closed State

```
                              ┌──────┐
                              │ 💬   │
                              │      │
                              └──────┘
```

**Specifications:**
- Position: Fixed bottom-right
- Size: 64px × 64px
- Background: Primary blue gradient
- Shadow: shadow-lg
- Pulse animation on page load
- Badge with unread count (if returning)

### Widget Open State

```
┌──────────────────────────────────────┐
│  [Practice Logo]  Practice Name   ✕  │
├──────────────────────────────────────┤
│                                      │
│  Agent: Hi! How can I help?          │
│  ┌────────────────────────────────┐  │
│  │ 2:30 PM                        │  │
│  └────────────────────────────────┘  │
│                                      │
│                  You: I need help    │
│                  ┌──────────────┐    │
│                  │ 2:31 PM      │    │
│                  └──────────────┘    │
│                                      │
│  Agent is typing...                  │
│                                      │
├──────────────────────────────────────┤
│  [Type a message...]        [Send]   │
└──────────────────────────────────────┘
```

**Specifications:**
- Size: 380px × 600px (desktop)
- Full screen on mobile
- Header: Practice branding
- Chat area: Scrollable message list
- Input: Sticky at bottom
- Timestamps on hover

### Message Bubbles

**User Message:**
```
                     ┌──────────────────┐
                     │ I need help      │
                     └──────────────────┘
                          2:31 PM
```
- Background: Primary blue
- Color: White text
- Align: Right
- Border radius: 16px (round on left, sharp on right)

**Agent Message:**
```
  ┌──────────────────┐
  │ I'd be happy to  │
  │ help you!        │
  └──────────────────┘
  2:31 PM
```
- Background: Gray 100
- Color: Gray 900 text
- Align: Left
- Border radius: 16px (round on right, sharp on left)

### Quick Reply Buttons

```
Agent: What type of service do you need?

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Chiropractic │  │ Massage      │  │ Physio       │
└──────────────┘  └──────────────┘  └──────────────┘
```

**Specifications:**
- Horizontal scroll if many options
- Pill-shaped buttons
- Blue border, white background
- Click to send as message

### Date/Time Picker

```
Agent: When would you like to come in?

┌────────────────────────────────┐
│      November 2025             │
│  Su Mo Tu We Th Fr Sa          │
│              1  2  3  4  5     │
│   6  7  8  9 10 11 12          │
│  13 14 15 16 17 18 19          │
│  20 21 22 [23] 24 25 26        │
│  27 28 29 30                   │
└────────────────────────────────┘

Available times on Nov 23:
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│ 9:00 │ │10:30 │ │ 2:00 │ │ 3:30 │
└──────┘ └──────┘ └──────┘ └──────┘
```

### Booking Confirmation

```
┌────────────────────────────────────┐
│  ✓ Booking Confirmed!              │
│                                    │
│  Service: Massage Therapy          │
│  When: Nov 23, 2025 at 2:00 PM     │
│  With: Dr. Sarah Johnson           │
│  Location: Main Office             │
│                                    │
│  A confirmation has been sent to:  │
│  (555) 123-4567                    │
│                                    │
│  [Add to Calendar] [Close]         │
└────────────────────────────────────┘
```

---

## Responsive Design

### Breakpoints

```css
/* Mobile First */
@media (min-width: 640px)  { /* sm */ }
@media (min-width: 768px)  { /* md */ }
@media (min-width: 1024px) { /* lg */ }
@media (min-width: 1280px) { /* xl */ }
@media (min-width: 1536px) { /* 2xl */ }
```

### Mobile Considerations

**Dashboard (Mobile):**
- Single column layout
- Stat cards stack vertically
- Hamburger menu for navigation
- Bottom tab bar for main sections

**Tables (Mobile):**
- Horizontal scroll
- Or card-based layout instead
- Most important columns only

**Forms (Mobile):**
- Full width inputs
- Larger touch targets (48px min)
- Native date/time pickers

**Chat Widget (Mobile):**
- Full screen takeover
- Native feel with header
- Slide-up animation

---

## Accessibility

### WCAG 2.1 AA Compliance

**Color Contrast:**
- Text on background: Minimum 4.5:1
- Large text: Minimum 3:1
- Interactive elements: 3:1

**Keyboard Navigation:**
- All interactive elements tabbable
- Visible focus indicators
- Logical tab order
- Skip to main content link

**Screen Readers:**
- Semantic HTML (header, nav, main, footer)
- ARIA labels where needed
- Alt text for images
- Form labels associated with inputs

**Focus Management:**
- Visible focus ring (blue, 2px)
- Focus trap in modals
- Focus restoration on modal close

### Accessibility Checklist

- [ ] All images have alt text
- [ ] Form inputs have labels
- [ ] Buttons have descriptive text (not just icons)
- [ ] Color is not sole means of conveying info
- [ ] Text is resizable to 200%
- [ ] Animations respect prefers-reduced-motion
- [ ] Error messages are descriptive
- [ ] Loading states announced to screen readers

---

## Design System Implementation

### shadcn/ui Components Used

**Core Components:**
- Button
- Card
- Input
- Label
- Select
- Textarea
- Dialog (Modal)
- Dropdown Menu
- Tabs
- Toast (Notifications)
- Badge
- Avatar
- Skeleton

**Form Components:**
- Form (React Hook Form wrapper)
- Checkbox
- Radio Group
- Switch
- Calendar (Date picker)

**Data Display:**
- Table
- Badge
- Tooltip
- Accordion

### Custom Components Needed

**Agent Chat Interface**
- Message bubble
- Typing indicator
- Quick reply buttons
- Date/time picker integration

**Voice Call UI**
- Call status indicator
- Audio waveform visualization
- Mute/unmute controls

**Knowledge Base Editor**
- Rich text editor
- Document upload with progress
- FAQ builder with drag-and-drop

**Analytics Charts**
- Line chart (time series)
- Bar chart (peak hours)
- Donut chart (outcome distribution)

---

## Animation Guidelines

### Timing Functions

```css
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
```

### Durations

```css
--duration-fast: 150ms;    /* Hover states */
--duration-normal: 250ms;  /* Most transitions */
--duration-slow: 350ms;    /* Complex animations */
```

### Common Animations

**Fade In:**
```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
```

**Slide Up:**
```css
@keyframes slideUp {
  from {
    transform: translateY(10px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
```

**Pulse (for new notifications):**
```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
```

### Motion Preferences

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Design Deliverables

### Phase 1: Wireframes
- [ ] Dashboard (desktop & mobile)
- [ ] Knowledge Base management
- [ ] Agent configuration
- [ ] Call/chat logs

### Phase 2: High-Fidelity Mockups
- [ ] Landing page
- [ ] All dashboard pages
- [ ] Chat widget (all states)
- [ ] Onboarding flow

### Phase 3: Prototype
- [ ] Interactive Figma prototype
- [ ] User flow demonstrations
- [ ] Micro-interactions

### Phase 4: Design System
- [ ] Component library in Figma
- [ ] Design tokens documented
- [ ] Icon set
- [ ] Illustration style guide

---

## Open Design Questions

1. Should we use illustrations or stick to icons?
2. Dark mode support from day one or later?
3. Custom voice avatar/persona for each practice?
4. Video onboarding walkthrough?
5. Gamification elements (badges, achievements)?
6. Multi-language support requirements?
7. White-label requirements (custom colors/logo)?

---

**Document Status:** Draft v1.0  
**Next Steps:** Create Figma designs  
**Designer:** TBD  
**Feedback:** Design review with team
