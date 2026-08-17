import { chromium } from 'playwright-core'

const browser = await chromium.launch({
  executablePath:
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
  headless: true,
})

try {
  const page = await browser.newPage()
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle' })
  const initialStatus = await page.getByRole('status').textContent()
  await page.getByLabel(/Customer Name/).fill('UI Acceptance Hospital')
  await page.getByLabel(/Product Name/).fill('Ibuprofen 200 mg')
  await page.getByLabel(/Batch\/Lot Number/).fill('LOT-UI-001')
  await page.getByLabel(/Complaint Category/).fill('Product quality')
  await page
    .getByLabel(/Complaint Description/)
    .fill('Tablet discoloration observed during acceptance review.')
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
      duplicateSubmissionPrevented,
    }),
  )
} finally {
  await browser.close()
}
