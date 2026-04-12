const { test, expect } = require("@playwright/test");

test("human message receives AI response", async ({ page }) => {
  const sessionId = "11111111-1111-1111-1111-111111111111";
  let dialogueTurns = [
    {
      turn_id: "greeting-turn",
      turn_number: 0,
      speaker: "AI",
      message: "Welcome! I am the factory seller.",
      offer_made: false,
      is_counter_offer: false,
      offer_amount: null,
      concession_amount: null,
      response_time_seconds: null,
      message_length: 33,
      sentiment: "neutral",
      strategy_tag: "neutral",
      extracted_offer: null,
      reasoning: null,
      timestamp: new Date().toISOString(),
      created_at: new Date().toISOString(),
    },
  ];
  let offerProgression = [];

  await page.addInitScript((sid) => {
    localStorage.setItem("access_token", "test-token");
    localStorage.setItem("session_id", sid);
  }, sessionId);

  await page.route(/\/api\/session\/[^/]+\/send-message$/, async (route) => {
    const payload = route.request().postDataJSON();
    const now = new Date().toISOString();

    dialogueTurns = [
      ...dialogueTurns,
      {
        turn_id: "human-turn-1",
        turn_number: 1,
        speaker: "Human",
        message: payload.message,
        offer_made: true,
        is_counter_offer: false,
        offer_amount: Number(payload.offer),
        concession_amount: null,
        response_time_seconds: null,
        message_length: String(payload.message || "").length,
        sentiment: "neutral",
        strategy_tag: "neutral",
        extracted_offer: Number(payload.offer),
        reasoning: null,
        timestamp: now,
        created_at: now,
      },
      {
        turn_id: "ai-turn-1",
        turn_number: 1,
        speaker: "AI",
        message: "I can move to $920,000 this round.",
        offer_made: true,
        is_counter_offer: true,
        offer_amount: 920000,
        concession_amount: null,
        response_time_seconds: null,
        message_length: 31,
        sentiment: "neutral",
        strategy_tag: "neutral",
        extracted_offer: 920000,
        reasoning: "Controlled concession",
        timestamp: now,
        created_at: now,
      },
    ];

    offerProgression = [
      {
        turn_number: 1,
        speaker: "Human",
        offer_amount: Number(payload.offer),
        concession_amount: null,
        concession_percentage: null,
        is_counter_offer: false,
        timestamp: now,
        created_at: now,
      },
      {
        turn_number: 1,
        speaker: "AI",
        offer_amount: 920000,
        concession_amount: -20000,
        concession_percentage: -2.13,
        is_counter_offer: true,
        timestamp: now,
        created_at: now,
      },
    ];

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        ai_message: "I can move to $920,000 this round.",
        ai_reasoning: "Controlled concession",
        ai_offer: 920000,
        turn_count: 1,
        outcome: null,
      }),
    });
  });

  await page.route(/\/api\/session\/[^/]+\/dialogue$/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        session_id: sessionId,
        dialogue: dialogueTurns,
        offers: offerProgression,
      }),
    });
  });

  await page.route(/\/api\/session\/[^/]+$/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        session_id: sessionId,
        turn_count: 1,
        turns_remaining: 4,
        initial_offer: 900000,
        final_offer: null,
        outcome: null,
        session_status: "in_progress",
        dropoff_stage: "mid_negotiation",
        dialogue_turns: dialogueTurns,
        offer_progression: offerProgression,
      }),
    });
  });

  await page.goto(`/src/pages/Chat.html?session_id=${sessionId}`);
  await expect(page.locator("#message-form")).toBeVisible();

  await page.fill("#message-input", "I can offer 900000");
  await page.fill("#offer-input", "900000");
  await page.click("#send-button");

  await expect(page.locator("#messages .bubble.ai").last()).toContainText("$920,000", { timeout: 20000 });
});
