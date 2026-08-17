import { chromium } from 'playwright-core'

const browser = await chromium.launch({
  executablePath:
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
  headless: true,
})

try {
  const page = await browser.newPage()
  page.setDefaultTimeout(30_000)
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle' })
  const initialStatus = await page.getByRole('status').textContent()
  await page
    .getByLabel('Complaint text or email')
    .fill('Apollo Pharmacy reports cracked Paracetamol 500 mg tablets, batch FDF-42.')
  await page.getByRole('button', { name: 'Process Complaint' }).click()
  await page.getByLabel(/Product Name/).waitFor()
  await page.getByLabel(/Product Name/).waitFor({ state: 'visible' })
  await page.waitForFunction(
    () => document.querySelector('input[name="productName"]')?.value === 'Paracetamol',
  )
  const extractedProductType = await page.getByLabel('Product Type').inputValue()
  const extractedBatch = await page.getByLabel(/Batch\/Lot Number/).inputValue()
  const affectedQuantity = await page.getByLabel('Affected Quantity').inputValue()
  await page.getByLabel(/Complaint Category/).fill('Product quality')
  await page.getByText('Ready to Commit', { exact: true }).waitFor()
  const readyStatus = await page.getByRole('status').textContent()
  const commitButton = page.getByRole('button', {
    name: 'Commit to QMS Ledger',
  })
  await commitButton.click()
  await page.getByText('COMMITTED', { exact: true }).waitFor()
  const complaintNumber = await page
    .getByText(/^CMP-\d{4}-\d{6}$/)
    .textContent()
  const duplicateSubmissionPrevented = await commitButton.isDisabled()
  console.log(
    JSON.stringify({
      initialStatus,
      readyStatus,
      finalStatus: 'COMMITTED',
      complaintNumber,
      extractedProductType,
      extractedBatch,
      affectedQuantity: affectedQuantity || null,
      duplicateSubmissionPrevented,
    }),
  )
} finally {
  await Promise.race([
    browser.close(),
    new Promise((resolve) => setTimeout(resolve, 5_000)),
  ])
}
process.exit(0)
