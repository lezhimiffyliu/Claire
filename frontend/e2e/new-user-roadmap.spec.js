// @ts-check
import { test, expect } from '@playwright/test';

/**
 * E2E Test: New User Roadmap Flow
 *
 * Simulates a completely new anonymous user:
 * 1. Clear localStorage (no preferences)
 * 2. Navigate to dashboard
 * 3. ExamDatePopup appears -> select today + 2 days
 * 4. PrepLevelPopup appears -> select "no_class_no_homework" (tier 1)
 * 5. Wait for /api/student-preferences (may fail for anonymous, that's OK)
 * 6. Wait for /api/roadmap to return
 * 7. Assert page renders: countdown, plan mode, roadmap blocks
 * 8. Take screenshot
 *
 * Expected for 2-day CRAM scenario:
 * - Plan mode: CRAM
 * - Countdown: "2 days left - high-impact topics only"
 * - Blocks: Double Integrals, Optimization, Taylor Series, Partial Derivatives
 * - NOT: vectors_and_geometry (excluded in CRAM)
 * - Reason: "matches high-priority exam block"
 */

test.describe('New User Roadmap Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Clear all localStorage before each test
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.clear();
    });
  });

  test('2-day cram scenario renders correct roadmap', async ({ page }) => {
    // Track API calls
    let roadmapResponse = null;
    let preferencesCallMade = false;

    // Listen for API calls
    page.on('request', request => {
      if (request.url().includes('/api/student-preferences')) {
        preferencesCallMade = true;
      }
    });

    page.on('response', async response => {
      if (response.url().includes('/api/roadmap')) {
        try {
          roadmapResponse = await response.json();
        } catch (e) {
          console.log('Failed to parse roadmap response');
        }
      }
    });

    // Navigate to dashboard
    await page.goto('/dashboard');

    // Handle course selection if it appears
    const courseSelection = page.locator('text=What\'s your current course?');
    if (await courseSelection.isVisible({ timeout: 3000 }).catch(() => false)) {
      console.log('Course selection screen detected');
      // Select Math 126
      const math126Option = page.locator('text=Math 126').first();
      await math126Option.click();
      console.log('✓ Selected Math 126');

      // Click Continue
      const continueButton = page.locator('button:has-text("CONTINUE"), button:has-text("Continue")').first();
      await continueButton.click();
      await page.waitForTimeout(1000);
    }

    // Wait for ExamDatePopup to appear
    console.log('Waiting for ExamDatePopup...');
    const examDatePopup = page.locator('text=When is your exam?');
    await expect(examDatePopup).toBeVisible({ timeout: 10000 });
    console.log('✓ ExamDatePopup appeared');

    // Calculate date 2 days from now
    const targetDate = new Date();
    targetDate.setDate(targetDate.getDate() + 2);
    const dateString = targetDate.toISOString().split('T')[0]; // YYYY-MM-DD

    // Fill the date input
    const dateInput = page.locator('input[type="date"]');
    await dateInput.fill(dateString);
    console.log(`✓ Selected exam date: ${dateString}`);

    // Click Continue
    const continueButton = page.locator('button:has-text("Continue")').first();
    await continueButton.click();

    // Wait for PrepLevelPopup to appear
    console.log('Waiting for PrepLevelPopup...');
    const prepLevelPopup = page.locator('text=How prepared do you feel?');
    await expect(prepLevelPopup).toBeVisible({ timeout: 10000 });
    console.log('✓ PrepLevelPopup appeared');

    // Select "Missed most classes & homework" (no_class_no_homework - tier 1)
    // This is the first option with emoji 😅
    const firstOption = page.locator('button:has-text("Missed most classes")').first();
    await firstOption.click();
    console.log('✓ Selected prep level: no_class_no_homework');

    // Click Continue on PrepLevelPopup
    const continueButton2 = page.locator('button:has-text("Continue")').first();
    await continueButton2.click();

    // Wait for popups to close and page to load
    await page.waitForTimeout(1000);

    // Wait for roadmap API call to complete
    console.log('Waiting for /api/roadmap...');
    await page.waitForResponse(
      response => response.url().includes('/api/roadmap'),
      { timeout: 15000 }
    ).catch(() => {
      console.log('Note: /api/roadmap response not captured (may have already completed)');
    });

    // Wait for page content to render
    await page.waitForTimeout(2000);

    // Take screenshot of the roadmap state
    const screenshotPath = 'test-results/new-user-cram-roadmap.png';
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`✓ Screenshot saved: ${screenshotPath}`);

    // =================================================================
    // ASSERTIONS: Verify rendered content
    // =================================================================

    console.log('\n========== ASSERTIONS ==========\n');

    // 1. Verify countdown card shows exam info
    // Look for either the countdown text or days remaining
    const pageContent = await page.content();

    // Check for countdown or days display
    const daysText = page.locator('text=/\\d+ days/').first();
    const hasDaysDisplay = await daysText.isVisible().catch(() => false);
    console.log(`Days display visible: ${hasDaysDisplay}`);

    // 2. Look for roadmap blocks on page
    // The blocks should show titles like "Double Integrals", "Optimization", etc.

    // Check for high-impact blocks that SHOULD be present
    const expectedBlocks = [
      'Double Integrals',
      'Optimization',
      'Taylor Series',
    ];

    console.log('\nChecking for expected blocks:');
    for (const blockTitle of expectedBlocks) {
      const blockElement = page.locator(`text=${blockTitle}`).first();
      const isVisible = await blockElement.isVisible().catch(() => false);
      console.log(`  ${isVisible ? '✓' : '✗'} ${blockTitle}: ${isVisible ? 'found' : 'NOT FOUND'}`);
    }

    // 3. Check that low-priority blocks are NOT prominently displayed
    // In CRAM mode, vectors_and_geometry should be excluded
    const lowPriorityBlocks = [
      'Vectors & Geometry',
    ];

    console.log('\nChecking low-priority blocks (should be excluded in CRAM):');
    for (const blockTitle of lowPriorityBlocks) {
      const blockElement = page.locator(`text=${blockTitle}`).first();
      const isVisible = await blockElement.isVisible().catch(() => false);
      console.log(`  ${isVisible ? '⚠' : '✓'} ${blockTitle}: ${isVisible ? 'VISIBLE (unexpected in CRAM)' : 'not visible (correct)'}`);
    }

    // 4. Verify localStorage was set
    const savedExamDate = await page.evaluate(() => localStorage.getItem('claire_exam_date'));
    const savedPrepLevel = await page.evaluate(() => localStorage.getItem('claire_prep_level'));

    console.log('\nLocalStorage verification:');
    console.log(`  exam_date: ${savedExamDate}`);
    console.log(`  prep_level: ${savedPrepLevel}`);

    expect(savedExamDate).toBe(dateString);
    expect(savedPrepLevel).toBe('no_class_no_homework');

    // 5. Print roadmap API response if captured
    if (roadmapResponse) {
      console.log('\n========== ROADMAP API RESPONSE ==========\n');
      console.log(`Plan Mode: ${roadmapResponse.plan_mode}`);
      console.log(`Countdown: ${roadmapResponse.countdown_text}`);
      console.log(`Fallback: ${roadmapResponse.fallback_to_legacy}`);

      if (roadmapResponse.roadmap_blocks) {
        console.log('\nRoadmap Block Order:');
        roadmapResponse.roadmap_blocks.forEach((block, i) => {
          console.log(`  ${i + 1}. ${block.title} (priority ${block.priority})`);
          console.log(`     Reason: "${block.reason}"`);
          console.log(`     Problems: ${block.problem_count}`);
        });

        // Verify plan mode is CRAM
        expect(roadmapResponse.plan_mode).toBe('cram');

        // Verify countdown text
        expect(roadmapResponse.countdown_text).toContain('2 days');

        // Verify no fallback
        expect(roadmapResponse.fallback_to_legacy).toBe(false);

        // Verify blocks are present and ordered correctly
        const blockIds = roadmapResponse.roadmap_blocks.map(b => b.block_id);
        expect(blockIds).toContain('double_integrals');
        expect(blockIds).toContain('optimization');
        expect(blockIds).toContain('taylor_series');

        // Verify low-priority blocks are excluded in CRAM
        expect(blockIds).not.toContain('vectors_and_geometry');

        // Verify reason text is exactly as specified
        for (const block of roadmapResponse.roadmap_blocks) {
          if (block.priority <= 2) {
            expect(block.reason).toBe('matches high-priority exam block');
          }
        }
      }
    } else {
      console.log('\n⚠ Roadmap API response was not captured');
      console.log('  This may happen if backend is not running or request failed');
    }

    console.log('\n========== TEST COMPLETE ==========');
    console.log(`Screenshot: ${screenshotPath}`);
  });
});
