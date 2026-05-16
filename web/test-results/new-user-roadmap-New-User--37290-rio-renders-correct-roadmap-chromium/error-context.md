# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: new-user-roadmap.spec.js >> New User Roadmap Flow >> 2-day cram scenario renders correct roadmap
- Location: e2e/new-user-roadmap.spec.js:34:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('text=When is your exam?')
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 10000ms
  - waiting for locator('text=When is your exam?')

```

```yaml
- banner:
  - button "Go back":
    - img
- main:
  - heading "Set your target" [level=2]
  - paragraph: We'll adapt practice intensity
  - button "🎯 Pass the class Focus on key concepts"
  - button "⭐ 3.5+ Above average performance"
  - button "🏆 4.0 / Mastery Complete understanding"
  - button "CONTINUE" [disabled]
```

# Test source

```ts
  1   | // @ts-check
  2   | import { test, expect } from '@playwright/test';
  3   | 
  4   | /**
  5   |  * E2E Test: New User Roadmap Flow
  6   |  *
  7   |  * Simulates a completely new anonymous user:
  8   |  * 1. Clear localStorage (no preferences)
  9   |  * 2. Navigate to dashboard
  10  |  * 3. ExamDatePopup appears -> select today + 2 days
  11  |  * 4. PrepLevelPopup appears -> select "no_class_no_homework" (tier 1)
  12  |  * 5. Wait for /api/student-preferences (may fail for anonymous, that's OK)
  13  |  * 6. Wait for /api/roadmap to return
  14  |  * 7. Assert page renders: countdown, plan mode, roadmap blocks
  15  |  * 8. Take screenshot
  16  |  *
  17  |  * Expected for 2-day CRAM scenario:
  18  |  * - Plan mode: CRAM
  19  |  * - Countdown: "2 days left - high-impact topics only"
  20  |  * - Blocks: Double Integrals, Optimization, Taylor Series, Partial Derivatives
  21  |  * - NOT: vectors_and_geometry (excluded in CRAM)
  22  |  * - Reason: "matches high-priority exam block"
  23  |  */
  24  | 
  25  | test.describe('New User Roadmap Flow', () => {
  26  |   test.beforeEach(async ({ page }) => {
  27  |     // Clear all localStorage before each test
  28  |     await page.goto('/');
  29  |     await page.evaluate(() => {
  30  |       localStorage.clear();
  31  |     });
  32  |   });
  33  | 
  34  |   test('2-day cram scenario renders correct roadmap', async ({ page }) => {
  35  |     // Track API calls
  36  |     let roadmapResponse = null;
  37  |     let preferencesCallMade = false;
  38  | 
  39  |     // Listen for API calls
  40  |     page.on('request', request => {
  41  |       if (request.url().includes('/api/student-preferences')) {
  42  |         preferencesCallMade = true;
  43  |       }
  44  |     });
  45  | 
  46  |     page.on('response', async response => {
  47  |       if (response.url().includes('/api/roadmap')) {
  48  |         try {
  49  |           roadmapResponse = await response.json();
  50  |         } catch (e) {
  51  |           console.log('Failed to parse roadmap response');
  52  |         }
  53  |       }
  54  |     });
  55  | 
  56  |     // Navigate to dashboard
  57  |     await page.goto('/dashboard');
  58  | 
  59  |     // Handle course selection if it appears
  60  |     const courseSelection = page.locator('text=What\'s your current course?');
  61  |     if (await courseSelection.isVisible({ timeout: 3000 }).catch(() => false)) {
  62  |       console.log('Course selection screen detected');
  63  |       // Select Math 126
  64  |       const math126Option = page.locator('text=Math 126').first();
  65  |       await math126Option.click();
  66  |       console.log('✓ Selected Math 126');
  67  | 
  68  |       // Click Continue
  69  |       const continueButton = page.locator('button:has-text("CONTINUE"), button:has-text("Continue")').first();
  70  |       await continueButton.click();
  71  |       await page.waitForTimeout(1000);
  72  |     }
  73  | 
  74  |     // Wait for ExamDatePopup to appear
  75  |     console.log('Waiting for ExamDatePopup...');
  76  |     const examDatePopup = page.locator('text=When is your exam?');
> 77  |     await expect(examDatePopup).toBeVisible({ timeout: 10000 });
      |                                 ^ Error: expect(locator).toBeVisible() failed
  78  |     console.log('✓ ExamDatePopup appeared');
  79  | 
  80  |     // Calculate date 2 days from now
  81  |     const targetDate = new Date();
  82  |     targetDate.setDate(targetDate.getDate() + 2);
  83  |     const dateString = targetDate.toISOString().split('T')[0]; // YYYY-MM-DD
  84  | 
  85  |     // Fill the date input
  86  |     const dateInput = page.locator('input[type="date"]');
  87  |     await dateInput.fill(dateString);
  88  |     console.log(`✓ Selected exam date: ${dateString}`);
  89  | 
  90  |     // Click Continue
  91  |     const continueButton = page.locator('button:has-text("Continue")').first();
  92  |     await continueButton.click();
  93  | 
  94  |     // Wait for PrepLevelPopup to appear
  95  |     console.log('Waiting for PrepLevelPopup...');
  96  |     const prepLevelPopup = page.locator('text=How prepared do you feel?');
  97  |     await expect(prepLevelPopup).toBeVisible({ timeout: 10000 });
  98  |     console.log('✓ PrepLevelPopup appeared');
  99  | 
  100 |     // Select "Missed most classes & homework" (no_class_no_homework - tier 1)
  101 |     // This is the first option with emoji 😅
  102 |     const firstOption = page.locator('button:has-text("Missed most classes")').first();
  103 |     await firstOption.click();
  104 |     console.log('✓ Selected prep level: no_class_no_homework');
  105 | 
  106 |     // Click Continue on PrepLevelPopup
  107 |     const continueButton2 = page.locator('button:has-text("Continue")').first();
  108 |     await continueButton2.click();
  109 | 
  110 |     // Wait for popups to close and page to load
  111 |     await page.waitForTimeout(1000);
  112 | 
  113 |     // Wait for roadmap API call to complete
  114 |     console.log('Waiting for /api/roadmap...');
  115 |     await page.waitForResponse(
  116 |       response => response.url().includes('/api/roadmap'),
  117 |       { timeout: 15000 }
  118 |     ).catch(() => {
  119 |       console.log('Note: /api/roadmap response not captured (may have already completed)');
  120 |     });
  121 | 
  122 |     // Wait for page content to render
  123 |     await page.waitForTimeout(2000);
  124 | 
  125 |     // Take screenshot of the roadmap state
  126 |     const screenshotPath = 'test-results/new-user-cram-roadmap.png';
  127 |     await page.screenshot({ path: screenshotPath, fullPage: true });
  128 |     console.log(`✓ Screenshot saved: ${screenshotPath}`);
  129 | 
  130 |     // =================================================================
  131 |     // ASSERTIONS: Verify rendered content
  132 |     // =================================================================
  133 | 
  134 |     console.log('\n========== ASSERTIONS ==========\n');
  135 | 
  136 |     // 1. Verify countdown card shows exam info
  137 |     // Look for either the countdown text or days remaining
  138 |     const pageContent = await page.content();
  139 | 
  140 |     // Check for countdown or days display
  141 |     const daysText = page.locator('text=/\\d+ days/').first();
  142 |     const hasDaysDisplay = await daysText.isVisible().catch(() => false);
  143 |     console.log(`Days display visible: ${hasDaysDisplay}`);
  144 | 
  145 |     // 2. Look for roadmap blocks on page
  146 |     // The blocks should show titles like "Double Integrals", "Optimization", etc.
  147 | 
  148 |     // Check for high-impact blocks that SHOULD be present
  149 |     const expectedBlocks = [
  150 |       'Double Integrals',
  151 |       'Optimization',
  152 |       'Taylor Series',
  153 |     ];
  154 | 
  155 |     console.log('\nChecking for expected blocks:');
  156 |     for (const blockTitle of expectedBlocks) {
  157 |       const blockElement = page.locator(`text=${blockTitle}`).first();
  158 |       const isVisible = await blockElement.isVisible().catch(() => false);
  159 |       console.log(`  ${isVisible ? '✓' : '✗'} ${blockTitle}: ${isVisible ? 'found' : 'NOT FOUND'}`);
  160 |     }
  161 | 
  162 |     // 3. Check that low-priority blocks are NOT prominently displayed
  163 |     // In CRAM mode, vectors_and_geometry should be excluded
  164 |     const lowPriorityBlocks = [
  165 |       'Vectors & Geometry',
  166 |     ];
  167 | 
  168 |     console.log('\nChecking low-priority blocks (should be excluded in CRAM):');
  169 |     for (const blockTitle of lowPriorityBlocks) {
  170 |       const blockElement = page.locator(`text=${blockTitle}`).first();
  171 |       const isVisible = await blockElement.isVisible().catch(() => false);
  172 |       console.log(`  ${isVisible ? '⚠' : '✓'} ${blockTitle}: ${isVisible ? 'VISIBLE (unexpected in CRAM)' : 'not visible (correct)'}`);
  173 |     }
  174 | 
  175 |     // 4. Verify localStorage was set
  176 |     const savedExamDate = await page.evaluate(() => localStorage.getItem('claire_exam_date'));
  177 |     const savedPrepLevel = await page.evaluate(() => localStorage.getItem('claire_prep_level'));
```