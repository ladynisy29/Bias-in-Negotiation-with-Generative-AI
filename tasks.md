# Tasks: AI Negotiation Research Platform

## Phase 1: Backend Setup & Database

- [x] 1.1 Initialize Django project and app structure
- [ ] 1.2 Configure PostgreSQL database connection
- [x] 1.3 Create UserProfile model with demographics fields
- [x] 1.4 Create NegotiationSession model with all required fields
- [x] 1.5 Create DialogueTurn model for conversation history
- [x] 1.6 Create OfferHistory model for offer tracking
- [x] 1.7 Run migrations and verify database schema
- [x] 1.8 Create database indexes for performance optimization

## Phase 2: Authentication & User Management

- [ ] 2.1 Implement user registration endpoint (POST /register)
- [ ] 2.2 Implement user login endpoint (POST /login)
- [ ] 2.3 Implement session token generation and validation
- [ ] 2.4 Implement session token expiration (24 hours)
- [ ] 2.5 Create authentication middleware for request validation
- [x] 2.6 Implement logout endpoint (POST /logout)
- [x] 2.7 Add password hashing using bcrypt
- [ ] 2.8 Write unit tests for authentication (target: 100% coverage)

## Phase 3: Negotiation Session Management

- [x] 3.1 Implement POST /start-session endpoint
- [x] 3.2 Implement AI reservation price randomization (850k-1.15M)
- [x] 3.3 Implement turn counter initialization and tracking
- [x] 3.4 Implement session state validation
- [x] 3.5 Implement GET /session/<id> endpoint
- [x] 3.6 Add session isolation verification
- [x] 3.7 Write unit tests for session management (target: 100% coverage)

## Phase 4: AI Integration & OpenAI API

- [x] 4.1 Set up OpenAI API client with environment variables
- [x] 4.2 Create system prompt for "firm but reasonable negotiator" behavior
- [x] 4.3 Implement POST /send-message endpoint
- [x] 4.4 Implement conversation history building for API context
- [x] 4.5 Implement JSON response parsing and validation
- [x] 4.6 Implement offer extraction from AI messages (regex patterns)
- [x] 4.7 Implement error handling for API failures and timeouts
- [x] 4.8 Implement retry logic with exponential backoff
- [x] 4.9 Write unit tests for AI integration (target: 90% coverage)

## Phase 5: Dialogue & Offer Tracking

- [x] 5.1 Implement DialogueTurn creation for human messages
- [x] 5.2 Implement DialogueTurn creation for AI messages
- [x] 5.3 Implement OfferHistory creation with concession calculation
- [x] 5.4 Implement concession_amount calculation logic
- [x] 5.5 Implement concession_percentage calculation logic
- [x] 5.6 Implement dialogue history retrieval endpoint
- [x] 5.7 Write unit tests for dialogue tracking (target: 95% coverage)

## Phase 6: Turn Management & Enforcement

- [x] 6.1 Implement turn counter validation (max 5 turns)
- [x] 6.2 Implement turn increment logic after each exchange
- [x] 6.3 Implement turn-based message rejection (after turn 5)
- [x] 6.4 Implement turn number assignment to DialogueTurn records
- [x] 6.5 Write unit tests for turn management (target: 100% coverage)

## Phase 7: Final Offer & Acceptance Logic

- [x] 7.1 Implement POST /submit-final-offer endpoint
- [x] 7.2 Implement acceptance threshold calculation (RP * 0.95)
- [x] 7.3 Implement acceptance decision logic
- [x] 7.4 Implement rejection decision logic
- [x] 7.5 Implement profit calculation for accepted deals
- [x] 7.6 Implement profit calculation for rejected deals
- [x] 7.7 Implement session finalization (ended_at, outcome)
- [x] 7.8 Write unit tests for acceptance logic (target: 100% coverage)

## Phase 8: Data Collection & Export

- [x] 8.1 Implement concession pattern calculation
- [x] 8.2 Implement offer progression data aggregation
- [x] 8.3 Implement session summary statistics calculation
- [x] 8.4 Implement CSV export endpoint (GET /export/sessions)
- [x] 8.5 Implement conversation transcript export
- [x] 8.6 Implement profit analysis data export
- [x] 8.7 Write unit tests for data collection (target: 90% coverage)

## Phase 9: Error Handling & Validation

- [ ] 9.1 Implement input validation for all endpoints
- [x] 9.2 Implement error response formatting (HTTP status codes)
- [ ] 9.3 Implement error logging for debugging
- [x] 9.4 Implement validation for offer amounts (positive, numeric)
- [x] 9.5 Implement validation for message length (max 2000 chars)
- [x] 9.6 Implement validation for session state transitions
- [ ] 9.7 Write integration tests for error scenarios (target: 90% coverage)

## Phase 10: Frontend - HTML Structure

- [x] 10.1 Create base HTML template with navigation
- [ ] 10.2 Create login page (username, password fields)*
- [ ] 10.3 Create registration page (demographics form)*
- [ ] 10.4 Create session start page (initial offer input)*
- [x] 10.5 Create chat interface page (message display area)
- [x] 10.6 Create result page (outcome display)
- [x] 10.7 Add responsive CSS for mobile compatibility

## Phase 11: Frontend - Chat Interface

- [x] 11.1 Implement message display with left/right alignment
- [x] 11.2 Implement turn counter display (X/5)
- [x] 11.3 Implement message input field with validation
- [x] 11.4 Implement offer input field with validation
- [x] 11.5 Implement typing indicator during AI response
- [x] 11.6 Implement message send button with loading state
- [x] 11.7 Implement auto-scroll to latest message

## Phase 12: Frontend - Offer Tracking & Display

- [x] 12.1 Implement offer history display
- [x] 12.2 Implement concession amount display
- [x] 12.3 Implement offer progression visualization
- [x] 12.4 Implement final offer input form (appears after turn 5)
- [x] 12.5 Implement final offer submit button
- [x] 12.6 Implement form validation for final offer

## Phase 13: Frontend - Result Display

- [x] 13.1 Implement outcome display (Accepted/Declined)
- [x] 13.2 Implement final price display
- [x] 13.3 Implement profit calculation display
- [x] 13.4 Implement concession pattern summary
- [x] 13.5 Implement session summary statistics
- [x] 13.6 Implement "Start New Negotiation" button

## Phase 14: Frontend - API Integration

- [x] 14.1 Implement fetch calls for /start-session
- [x] 14.2 Implement fetch calls for /send-message
- [x] 14.3 Implement fetch calls for /submit-final-offer
- [x] 14.4 Implement fetch calls for /session/<id>
- [x] 14.5 Implement error handling for API failures
- [x] 14.6 Implement loading states and spinners
- [x] 14.7 Implement session token management in localStorage

## Phase 15: Frontend - Styling & UX

- [x] 15.1 Create CSS for chat message bubbles
- [x] 15.2 Create CSS for form inputs and buttons
- [x] 15.3 Create CSS for turn counter display
- [x] 15.4 Create CSS for offer history display
- [x] 15.5 Create CSS for result page layout
- [x] 15.6 Implement dark/light theme toggle (optional)
- [x] 15.7 Test responsive design on mobile devices

## Phase 16: Testing & Quality Assurance

- [ ] 16.1 Run full unit test suite (target: 90%+ coverage)
- [ ] 16.2 Run integration tests for complete negotiation flow
- [ ] 16.3 Test concurrent session handling
- [ ] 16.4 Test error scenarios and edge cases
- [ ] 16.5 Test API response times and performance
- [ ] 16.6 Test database query performance
- [ ] 16.7 Perform security testing (input validation, injection attacks)
- [ ] 16.8 Test data export functionality

## Phase 17: Deployment & Documentation

- [ ] 17.1 Create deployment guide (Docker, environment setup)
- [ ] 17.2 Create API documentation (endpoint specs, examples)
- [ ] 17.3 Create user guide (how to run negotiations)
- [ ] 17.4 Create data analysis guide (how to export and analyze data)
- [ ] 17.5 Set up production database backups
- [ ] 17.6 Configure logging and monitoring
- [ ] 17.7 Deploy to staging environment
- [ ] 17.8 Deploy to production environment

## Phase 18: Post-Launch & Optimization

- [ ] 18.1 Monitor system performance and uptime
- [ ] 18.2 Collect user feedback and bug reports
- [ ] 18.3 Optimize database queries based on performance metrics
- [ ] 18.4 Optimize AI API calls (caching, batching)
- [ ] 18.5 Implement rate limiting for API endpoints
- [ ] 18.6 Add analytics tracking for research insights
- [ ] 18.7 Plan future enhancements based on research findings

