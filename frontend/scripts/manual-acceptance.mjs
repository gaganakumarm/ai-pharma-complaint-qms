import path from 'node:path'

import { chromium } from 'playwright-core'

const samples = path.resolve('..', 'sample-data')
const browser = await chromium.launch({
  executablePath:
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
  headless: true,
})

try {
  const page = await browser.newPage()
  page.setDefaultTimeout(45_000)
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle' })
  const ledgerCount = async () =>
    page.evaluate(async () => {
      const response = await fetch(
        'http://localhost:8000/api/complaints?page=1&page_size=1',
      )
      return (await response.json()).total
    })

  const initialCount = await ledgerCount()
  await page
    .getByLabel('Choose a PDF or drag it here')
    .setInputFiles(path.join(samples, 'fictional-fdf-complaint.pdf'))
  await page.getByRole('button', { name: 'Process PDF' }).click()
  await page.getByText('Extracting selectable text').waitFor()
  await page.waitForFunction(
    () =>
      document.querySelector('input[name="batchLotNumber"]')?.value ===
      'AMX-FDF-2407',
  )
  const afterFdfProcessing = await ledgerCount()
  const fdfProductType = await page.getByLabel('Product Type').inputValue()
  const fdfBatch = await page.getByLabel(/Batch\/Lot Number/).inputValue()
  await page.getByLabel(/Complaint Category/).fill('Product discoloration')
  await page.getByText('Ready to Commit', { exact: true }).waitFor()
  await page.getByRole('button', { name: 'Commit to QMS Ledger' }).click()
  await page.getByText('COMMITTED', { exact: true }).waitFor()
  const complaintNumber = await page
    .getByText(/^CMP-\d{4}-\d{6}$/)
    .textContent()
  const committed = await page.evaluate(async (number) => {
    const response = await fetch(
      'http://localhost:8000/api/complaints?page=1&page_size=100',
    )
    const body = await response.json()
    return body.items.find((item) => item.complaint_number === number)
  }, complaintNumber)

  await page.getByRole('button', { name: 'Reset Form' }).click()
  await page
    .getByLabel('Choose a PDF or drag it here')
    .setInputFiles(path.join(samples, 'fictional-api-complaint.pdf'))
  await page.getByRole('button', { name: 'Process PDF' }).click()
  await page.waitForFunction(
    () =>
      document.querySelector('input[name="batchLotNumber"]')?.value ===
      'MET-API-77A',
  )
  const apiProductType = await page.getByLabel('Product Type').inputValue()
  const apiGrade = await page.getByLabel('Product Strength/Grade').inputValue()
  const apiBatch = await page.getByLabel(/Batch\/Lot Number/).inputValue()
  const apiQuantity = await page.getByLabel('Affected Quantity').inputValue()
  const afterApiProcessing = await ledgerCount()

  await page
    .getByLabel('Choose a PDF or drag it here')
    .setInputFiles(path.join(samples, 'fictional-textless-complaint.pdf'))
  await page.getByRole('button', { name: 'Process PDF' }).click()
  const textlessError = await page
    .getByRole('alert')
    .filter({ hasText: 'No readable text' })
    .textContent()
  const draftPreservedAfterTextless =
    (await page.getByLabel(/Batch\/Lot Number/).inputValue()) === 'MET-API-77A'

  await page.getByRole('button', { name: 'Reset Form' }).click()
  await page
    .getByLabel('Complaint text or email')
    .fill('Paracetamol 500 mg FDF batch TEXT-REG-1 had cracked tablets.')
  await page.getByRole('button', { name: 'Process Complaint' }).click()
  await page.waitForFunction(
    () =>
      document.querySelector('input[name="batchLotNumber"]')?.value ===
      'TEXT-REG-1',
  )

  console.log(
    JSON.stringify({
      initialCount,
      afterFdfProcessing,
      afterApiProcessing,
      automaticPersistencePrevented:
        initialCount === afterFdfProcessing &&
        afterApiProcessing === initialCount + 1,
      fdfProductType,
      fdfBatch,
      complaintNumber,
      complaintId: committed?.id,
      apiProductType,
      apiGrade,
      apiBatch,
      apiQuantity,
      textlessError,
      draftPreservedAfterTextless,
      textRegressionBatch: await page
        .getByLabel(/Batch\/Lot Number/)
        .inputValue(),
    }),
  )
} finally {
  await Promise.race([
    browser.close(),
    new Promise((resolve) => setTimeout(resolve, 5_000)),
  ])
}
process.exit(0)
