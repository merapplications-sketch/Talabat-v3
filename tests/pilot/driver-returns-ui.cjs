const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium, webkit, devices } = require('playwright');
const runtime = JSON.parse(fs.readFileSync(path.join(__dirname, '.runtime.json')));
const { order } = JSON.parse(fs.readFileSync(path.join(__dirname, '.runtime-return-ui.json')));
const engine = process.env.RETURN_BROWSER;
const profile = engine === 'webkit' ? 'iPhone 13' : 'Pixel 7';
const result = { source: process.env.GITHUB_SHA, live: false, engine, profile, physical: false, checks: [] };

async function login(browser, role, account = role) {
  const context = await browser.newContext({ ...devices[profile], locale: 'en-US' });
  await context.route('**/*', route => new URL(route.request().url()).hostname === '127.0.0.1'
    ? route.continue() : route.abort());
  const page = await context.newPage();
  await page.goto('http://127.0.0.1:8080/' + role + '.html?lang=en');
  await page.locator('#tlb-em').fill(runtime.accounts[account].email);
  await page.locator('#tlb-pw').fill(runtime.accounts[account].password);
  await page.locator('#tlb-go').click();
  await page.waitForFunction(id => TLB.order(id)?.status === 'pickedup', order);
  return page;
}

const dialog = page => page.getByRole('dialog', { name: 'Order return #' + order });
const action = (page, name) => dialog(page).locator('[data-return-action="' + name + '"]');

(async () => {
  const browser = await ({ chromium, webkit })[engine].launch();
  try {
    const driver = await login(browser, 'driver', 'driver1');
    const customer = await login(browser, 'customer');
    const merchant = await login(browser, 'merchant');
    await driver.locator('[data-return-order="' + order + '"]').click();
    await dialog(driver).getByLabel('Payment evidence reference').fill('SYNTHETIC DRIVER PAYMENT');
    await dialog(driver).getByLabel('Amount actually paid from your own funds (TJS)').fill('47');
    await action(driver, 'depart').click();
    await dialog(driver).getByText('Courier departure recorded.').waitFor();

    await customer.evaluate(id => { S.tid = id; S.v = 'track'; render(); }, order);
    await customer.locator('[data-return-order="' + order + '"]').click();
    await action(customer, 'cancel').click();
    await dialog(customer).getByText('Waiting for the restaurant to receive the meal.').waitFor();
    assert.equal(await dialog(customer).locator('[data-return-claim]').count(), 0);
    result.checks.push('customer cancellation and redacted return status');

    await merchant.getByRole('button', { name: 'Find an order return' }).click();
    await merchant.getByLabel('Order number').fill(String(order));
    await merchant.getByRole('button', { name: 'Open', exact: true }).click();
    await dialog(merchant).getByLabel('Meal handover evidence reference').fill('SYNTHETIC HANDOVER');
    await action(merchant, 'receive').click();
    await dialog(merchant).getByLabel('Refund evidence reference').fill('SYNTHETIC PARTIAL REFUND');
    await dialog(merchant).getByLabel('Refund amount (TJS)').fill('20');
    await action(merchant, 'report_refund').click();
    await dialog(merchant).getByText(/Awaiting courier confirmation/).waitFor();
    assert.equal(await dialog(merchant).locator('[data-return-claim]').getAttribute('data-return-claim'), '47');
    result.checks.push('meal receipt and unconfirmed refund do not reduce claim');

    await dialog(driver).getByRole('button', { name: 'Refresh', exact: true }).click();
    await action(driver, 'confirm_refund').waitFor();
    let confirmationWrites = 0;
    await driver.route('**/rpc/order_return_action', async route => {
      confirmationWrites++;
      const response = await route.fetch();
      assert.equal(response.status(), 200);
      await route.abort('connectionreset');
    });
    await action(driver, 'confirm_refund').click();
    await dialog(driver).locator('[data-return-claim="27"]').waitFor();
    await dialog(driver).getByText('Outbound delivery due from platform · 15.00 TJS').waitFor();
    assert.equal(confirmationWrites, 1);
    result.checks.push('lost reply recovered by reading; partial claim and platform delivery distinct');
    for (const page of [driver, customer, merchant]) {
      assert(await dialog(page).evaluate(el => {
        const bounds = el.getBoundingClientRect();
        return bounds.left >= 0 && bounds.right <= innerWidth && el.scrollWidth <= el.clientWidth + 1;
      }));
    }
    result.checks.push('all three return panels fit mobile viewport');
    result.pass = true;
  } catch (error) {
    result.pass = false;
    result.error = String(error.message || error).slice(0, 500);
    process.exitCode = 1;
  } finally {
    await browser.close();
    fs.writeFileSync(path.join(__dirname, 'result-driver-returns-ui-' + engine + '.json'),
      JSON.stringify(result, null, 2));
    console.log(result.pass ? 'PASS ' + profile + ' return workflow' : 'FAIL ' + result.error);
  }
})().catch(error => { console.error(error.message); process.exitCode = 1; });
