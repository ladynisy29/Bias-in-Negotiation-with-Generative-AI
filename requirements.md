# Requirements Document: AI Negotiation Research Platform

## Feature Overview

A full-stack research platform enabling controlled human-AI price negotiation experiments. Users negotiate with an AI agent over factory purchase price across exactly 5 turns, with comprehensive behavioral data collection for analysis.

---

## Acceptance Criteria

### 1. User Authentication & Session Management

#### 1.1 User Registration
- **Given** a new user visits the platform
- **When** they complete registration with username, password, and demographics (age, gender, education, negotiation experience)
- **Then** a UserProfile is created and they can log in
- **And** demographics are stored for later analysis

#### 1.2 Session-Based Authentication
- **Given** a user is logged in
- **When** they navigate the platform
- **Then** their session token is validated on each request
- **And** expired sessions (>24 hours) are rejected with redirect to login

#### 1.3 Session Isolation
- **Given** multiple users are negotiating simultaneously
- **When** each user sends messages
- **Then** their sessions remain completely isolated
- **And** no cross-session data leakage occurs

---

### 2. Negotiation Session Initialization

#### 2.1 Session Creation
- **Given** an authenticated user clicks "Start Negotiation"
- **When** they enter an initial offer amount
- **Then** a NegotiationSession is created with:
  - Unique session_id
  - AI reservation price randomly assigned (850,000-1,150,000)
  - turn_count initialized to 0
  - started_at timestamp recorded

#### 2.2 Initial Offer Validation
- **Given** a user enters an initial offer
- **When** they submit it
- **Then** the system validates it's a positive number
- **And** rejects non-numeric or negative values with error message

#### 2.3 AI Reservation Price Randomization
- **Given** a new session is created
- **When** the AI reservation price is assigned
- **Then** it's randomly selected from range [850,000, 1,150,000]
- **And** it's stored in the session (hidden from user)

---

### 3. Real-Time Chat Interface

#### 3.1 Message Display
- **Given** a negotiation is in progress
- **When** messages are exchanged
- **Then** human messages appear right-aligned in one color
- **And** AI messages appear left-aligned in a different color
- **And** messages are displayed in chronological order

#### 3.2 Turn Counter Display
- **Given** a user is in a negotiation
- **When** they view the chat interface
- **Then** a turn counter displays "X/5" (current/max)
- **And** it updates after each AI response

#### 3.3 Message Input Validation
- **Given** a user types a message
- **When** they attempt to submit
- **Then** the system validates message is non-empty
- **And** rejects empty messages with error
- **And** enforces max 2000 character limit

#### 3.4 Typing Indicator
- **Given** the user sends a message
- **When** waiting for AI response
- **Then** a "typing..." indicator appears
- **And** it disappears when AI response arrives

---

### 4. AI Negotiation Agent

#### 4.1 AI Response Generation
- **Given** a user sends a message and offer
- **When** the backend processes it
- **Then** the system calls OpenAI API with:
  - System prompt defining "firm but reasonable negotiator" behavior
  - Full conversation history
  - Current turn number
- **And** receives JSON response with: message, reasoning, offer

#### 4.2 Strict JSON Output Format
- **Given** OpenAI returns a response
- **When** the backend processes it
- **Then** it validates the JSON structure contains:
  - `message`: string (AI's negotiation message)
  - `reasoning`: string (AI's internal reasoning)
  - `offer`: number (AI's counter-offer in dollars)
- **And** rejects malformed responses with error

#### 4.3 Offer Extraction from AI Message
- **Given** an AI message is received
- **When** the system processes it
- **Then** it automatically extracts the numeric offer using regex patterns:
  - "$950,000" → 950000
  - "950k" → 950000
  - "1.2 million" → 1200000
- **And** stores extracted offer in OfferHistory

#### 4.4 Gradual Concession Strategy
- **Given** the AI is negotiating
- **When** it generates responses across turns
- **Then** it generally makes concessions (lowers price) over time
- **And** each concession includes justification in reasoning field
- **And** concessions are reasonable (not jumping to acceptance immediately)

#### 4.5 AI Response Time
- **Given** a user sends a message
- **When** waiting for AI response
- **Then** response arrives within 5 seconds
- **And** timeout error is shown if exceeded

---

### 5. Turn Management

#### 5.1 Turn Counter Enforcement
- **Given** a negotiation is in progress
- **When** a user attempts to send a message
- **Then** the system checks turn_count < 5
- **And** allows message if true
- **And** rejects with "Maximum turns reached" if false

#### 5.2 Turn Increment Logic
- **Given** a user sends a message and AI responds
- **When** both are stored
- **Then** turn_count is incremented by 1
- **And** turn_count never exceeds 5

#### 5.3 Turn-Based Data Recording
- **Given** each turn completes
- **When** data is stored
- **Then** DialogueTurn records include turn_number (1-5)
- **And** OfferHistory records include turn_number
- **And** all records are linked to session_id

---

### 6. Offer Tracking & History

#### 6.1 Offer Recording
- **Given** a user or AI makes an offer
- **When** the turn is processed
- **Then** an OfferHistory record is created with:
  - offer_amount (numeric value)
  - speaker (Human or AI)
  - turn_number
  - session_id

#### 6.2 Concession Calculation
- **Given** an offer is recorded
- **When** it's not the first offer
- **Then** concession_amount is calculated: previous_offer - current_offer
- **And** concession_percentage is calculated: (concession_amount / previous_offer) * 100
- **And** both are stored in OfferHistory

#### 6.3 Offer Progression Visibility
- **Given** a user views the chat interface
- **When** they look at the offer history
- **Then** they see all previous offers in chronological order
- **And** concession amounts are displayed

---

### 7. Final Offer Submission

#### 7.1 Final Offer Input Availability
- **Given** a negotiation reaches turn 5
- **When** the AI responds to the 5th turn
- **Then** a "Submit Final Offer" button appears
- **And** it's disabled before turn 5

#### 7.2 Final Offer Validation
- **Given** a user enters a final offer
- **When** they click "Submit Final Offer"
- **Then** the system validates:
  - Value is numeric
  - Value is positive
  - turn_count = 5
- **And** rejects invalid entries with error message

#### 7.3 Final Offer Storage
- **Given** a valid final offer is submitted
- **When** it's processed
- **Then** session.final_offer is set
- **And** session.ended_at is set to current timestamp

---

### 8. Acceptance Logic & Outcome Determination

#### 8.1 Acceptance Threshold
- **Given** a final offer is submitted
- **When** the system evaluates it
- **Then** it calculates: acceptance_threshold = ai_reservation_price * 0.95
- **And** compares: final_offer >= acceptance_threshold

#### 8.2 Acceptance Decision
- **Given** final_offer >= acceptance_threshold
- **When** outcome is determined
- **Then** session.outcome is set to "Accepted"
- **And** session.final_price is set to final_offer

#### 8.3 Rejection Decision
- **Given** final_offer < acceptance_threshold
- **When** outcome is determined
- **Then** session.outcome is set to "Declined"
- **And** session.final_price remains null

#### 8.4 Acceptance Determinism
- **Given** the same final_offer and ai_reservation_price
- **When** outcome is evaluated multiple times
- **Then** the outcome is always identical
- **And** no randomness affects the decision

---

### 9. Profit Calculations

#### 9.1 Human Profit Calculation (Accepted Deal)
- **Given** a deal is accepted
- **When** profits are calculated
- **Then** human_profit = final_price - initial_offer
- **And** negative profit is possible (user paid more than initial offer)

#### 9.2 AI Profit Calculation (Accepted Deal)
- **Given** a deal is accepted
- **When** profits are calculated
- **Then** ai_profit = final_price - ai_reservation_price
- **And** ai_profit is always positive (final_price >= RP * 0.95)

#### 9.3 Profit Calculation (Rejected Deal)
- **Given** a deal is rejected
- **When** profits are calculated
- **Then** human_profit = 0
- **And** ai_profit = 0

#### 9.4 Profit Storage
- **Given** profits are calculated
- **When** the session is updated
- **Then** human_profit and ai_profit are stored in NegotiationSession
- **And** they're available for analysis export

---

### 10. Dialogue & Conversation History

#### 10.1 Dialogue Turn Recording
- **Given** a message is sent (human or AI)
- **When** it's processed
- **Then** a DialogueTurn record is created with:
  - session_id
  - turn_number
  - speaker (Human or AI)
  - message (full text)
  - extracted_offer (if present)
  - reasoning (AI only)

#### 10.2 Conversation Context Preservation
- **Given** a negotiation is in progress
- **When** the AI generates a response
- **Then** the full conversation history is sent to OpenAI
- **And** the AI can reference previous messages and offers

#### 10.3 Conversation Retrieval
- **Given** a session_id
- **When** dialogue history is requested
- **Then** all DialogueTurn records are returned in chronological order
- **And** they include all metadata (speaker, offer, reasoning)

---

### 11. Result Display & Summary

#### 11.1 Outcome Display
- **Given** a final offer is submitted and evaluated
- **When** the result page loads
- **Then** it displays:
  - "Deal Accepted" or "Deal Declined"
  - Final price (if accepted)
  - Human profit/loss
  - AI profit

#### 11.2 Concession Pattern Summary
- **Given** a negotiation completes
- **When** the result page displays
- **Then** it shows:
  - Offer progression (all offers in order)
  - Concession amounts per turn
  - Average concession per turn

#### 11.3 Session Summary Statistics
- **Given** a negotiation completes
- **When** the result page displays
- **Then** it shows:
  - Total turns completed (5)
  - Initial offer
  - Final offer
  - Total concession (initial - final)

---

### 12. Data Collection & Storage

#### 12.1 Complete Conversation Transcripts
- **Given** a negotiation completes
- **When** data is exported
- **Then** full conversation transcripts are available including:
  - All human messages
  - All AI messages
  - All reasoning from AI
  - Timestamps for each turn

#### 12.2 Offer Progression Data
- **Given** a negotiation completes
- **When** data is exported
- **Then** offer progression is available including:
  - All offers (human and AI)
  - Turn numbers
  - Concession amounts and percentages
  - Speaker for each offer

#### 12.3 Concession Pattern Data
- **Given** a negotiation completes
- **When** data is exported
- **Then** concession patterns are available including:
  - Concession amount per turn
  - Concession percentage per turn
  - Average concession rate
  - Concession direction (increase/decrease)

#### 12.4 Profit Calculation Data
- **Given** a negotiation completes
- **When** data is exported
- **Then** profit data is available including:
  - Initial offer
  - Final offer
  - Final price
  - Human profit/loss
  - AI profit
  - Joint profit (if accepted)

#### 12.5 User Demographics Data
- **Given** a negotiation completes
- **When** data is exported
- **Then** user demographics are linked including:
  - Age
  - Gender
  - Education level
  - Negotiation experience

#### 12.6 Session Metadata
- **Given** a negotiation completes
- **When** data is exported
- **Then** session metadata is available including:
  - session_id
  - user_id
  - started_at
  - ended_at
  - duration
  - ai_reservation_price
  - outcome

---

### 13. API Endpoints

#### 13.1 POST /start-session
- **Given** an authenticated user
- **When** they call POST /start-session with initial_offer
- **Then** a NegotiationSession is created
- **And** response includes: session_id, ai_reservation_price (hidden), turn_count=0

#### 13.2 POST /send-message
- **Given** an active session
- **When** they call POST /send-message with message and offer
- **Then** the message is stored
- **And** AI response is generated
- **And** response includes: ai_message, ai_reasoning, ai_offer, turn_count

#### 13.3 POST /submit-final-offer
- **Given** a session at turn 5
- **When** they call POST /submit-final-offer with final_offer
- **Then** outcome is evaluated
- **And** response includes: outcome, final_price, human_profit, ai_profit

#### 13.4 GET /session/<id>
- **Given** a session_id
- **When** they call GET /session/<id>
- **Then** session details are returned including:
  - All dialogue turns
  - All offers
  - Current turn_count
  - Outcome (if completed)

---

### 14. Error Handling

#### 14.1 Invalid Session Error
- **Given** a user sends a request with non-existent session_id
- **When** the backend processes it
- **Then** HTTP 404 is returned with message "Session not found"

#### 14.2 Turn Limit Error
- **Given** a user attempts to send a message after turn 5
- **When** the backend processes it
- **Then** HTTP 400 is returned with message "Maximum turns reached"

#### 14.3 Invalid Offer Error
- **Given** a user submits non-numeric or negative offer
- **When** the backend validates it
- **Then** HTTP 400 is returned with message "Invalid offer amount"

#### 14.4 AI Service Error
- **Given** OpenAI API fails or times out
- **When** the backend attempts to call it
- **Then** HTTP 503 is returned with message "AI service temporarily unavailable"
- **And** error is logged for debugging

#### 14.5 Premature Final Offer Error
- **Given** a user attempts to submit final offer before turn 5
- **When** the backend validates turn_count
- **Then** HTTP 400 is returned with message "Cannot submit final offer before turn 5"

---

### 15. Security & Privacy

#### 15.1 Password Security
- **Given** a user registers
- **When** their password is stored
- **Then** it's hashed using bcrypt or similar
- **And** plaintext passwords are never stored

#### 15.2 Session Token Security
- **Given** a user logs in
- **When** a session token is issued
- **Then** it expires after 24 hours
- **And** expired tokens are rejected

#### 15.3 API Key Security
- **Given** the system uses OpenAI API
- **When** the API key is stored
- **Then** it's stored in environment variables
- **And** it's never committed to version control

#### 15.4 Input Sanitization
- **Given** a user submits any input
- **When** it's processed
- **Then** it's sanitized to prevent injection attacks
- **And** special characters are escaped

#### 15.5 Data Privacy
- **Given** user demographics are stored
- **When** they're stored in database
- **Then** sensitive fields are encrypted
- **And** they're only accessible to authorized users

---

### 16. Performance Requirements

#### 16.1 AI Response Time
- **Given** a user sends a message
- **When** waiting for AI response
- **Then** response arrives within 5 seconds
- **And** timeout error is shown if exceeded

#### 16.2 Database Query Performance
- **Given** a session_id is queried
- **When** dialogue history is retrieved
- **Then** query completes within 500ms
- **And** database indexes are used for optimization

#### 16.3 Concurrent Session Support
- **Given** multiple users are negotiating
- **When** they send messages simultaneously
- **Then** system handles 100+ concurrent sessions
- **And** no performance degradation occurs

---

## Non-Functional Requirements

### Scalability
- System must support 100+ concurrent negotiations
- Database must handle 10,000+ completed sessions
- API must scale horizontally with load balancing

### Reliability
- System uptime target: 99.5%
- Failed AI API calls must be retried with exponential backoff
- Database backups must occur daily

### Maintainability
- Code must follow PEP 8 style guide (Python)
- All functions must have docstrings
- Unit test coverage must be ≥80%

### Usability
- Chat interface must be intuitive and responsive
- Error messages must be clear and actionable
- Mobile-friendly design (responsive CSS)

---

## Data Export & Analysis

### Export Format
- CSV export of all sessions with:
  - Session metadata
  - User demographics
  - Offer progression
  - Concession patterns
  - Profit calculations
  - Conversation transcripts

### Analysis Metrics
- Average human profit by demographic group
- Average AI profit across all sessions
- Concession patterns by turn
- Acceptance rate by initial offer range
- Negotiation duration statistics

