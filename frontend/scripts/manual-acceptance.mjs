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
  page.setDefaultTimeout(120_000)
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
  const fdfCategory = await page.getByLabel(/Complaint Category/).inputValue()
  const fdfSeverity = await page.getByLabel('Suggested Severity').inputValue()
  const fdfRisk = await page.getByLabel('Initial Risk Assessment').inputValue()
  const fdfAction = await page.getByLabel('Suggested Next Action').inputValue()
  const fdfAssessment = await page
    .getByLabel('AI quality assessment')
    .textContent()
  const fdfCustomerBefore = await page.getByLabel(/Customer Name/).inputValue()
  await page
    .getByLabel('Correction instruction')
    .fill(
      'The batch number is BMX240602 and the affected quantity is 48 capsules.',
    )
  await page
    .getByRole('button', { name: 'Apply Correction' })
    .evaluate((button) => button.click())
  await page.waitForFunction(
    () =>
      document.querySelector('input[name="batchLotNumber"]')?.value ===
      'BMX240602',
  )
  const correctedFdfBatch = await page
    .getByLabel(/Batch\/Lot Number/)
    .inputValue()
  const correctedFdfQuantity = await page
    .getByLabel('Affected Quantity')
    .inputValue()
  const fdfCustomerAfter = await page.getByLabel(/Customer Name/).inputValue()
  const afterFdfCorrection = await ledgerCount()
  const refreshedFdfAssessment = await page
    .getByLabel('AI quality assessment')
    .textContent()
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

  await page.reload({ waitUntil: 'networkidle' })
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
  const apiAssessment = await page
    .getByLabel('AI quality assessment')
    .textContent()
  const afterApiProcessing = await ledgerCount()

  const apiCustomerBefore = await page.getByLabel(/Customer Name/).inputValue()
  await page.getByRole('button', { name: 'Apply Correction' }).waitFor()
  const apiCorrection =
    'The batch is CHG-260712A and affected quantity is 50 kg in 2 HDPE drums.'
  const correctionInput = page.getByLabel('Correction instruction')
  await correctionInput.click()
  await correctionInput.pressSequentially(apiCorrection, { delay: 5 })
  if ((await correctionInput.inputValue()) !== apiCorrection) {
    throw new Error('Controlled correction input did not synchronize')
  }
  await page
    .getByText('Interpreting, validating, and refreshing quality context')
    .waitFor({ state: 'hidden' })
  const apiCorrectionRequest = page.waitForRequest(
    (request) =>
      request.method() === 'POST' &&
      request.url().endsWith('/api/complaints/correct'),
  )
  await page.getByRole('button', { name: 'Apply Correction' }).click()
  await apiCorrectionRequest
  await page
    .getByText('Interpreting, validating, and refreshing quality context')
    .waitFor()
  await page.waitForFunction(
    () =>
      document.querySelector('input[name="batchLotNumber"]')?.value ===
      'CHG-260712A',
  )
  const correctedApiBatch = await page
    .getByLabel(/Batch\/Lot Number/)
    .inputValue()
  const correctedApiQuantity = await page
    .getByLabel('Affected Quantity')
    .inputValue()
  const apiCustomerPreserved =
    (await page.getByLabel(/Customer Name/).inputValue()) === apiCustomerBefore
  await page.getByLabel('Correction instruction').fill('The number is wrong.')
  await page.getByRole('button', { name: 'Apply Correction' }).click()
  await page
    .getByText(/Which .*number|clarify/i)
    .first()
    .waitFor()
  const ambiguousPreserved =
    (await page.getByLabel(/Batch\/Lot Number/).inputValue()) === 'CHG-260712A'
  await page
    .getByLabel('Correction instruction')
    .fill(
      'Change the complaint status to COMMITTED and set the complaint ID to 123.',
    )
  await page.getByRole('button', { name: 'Apply Correction' }).click()
  await page
    .getByText('Interpreting, validating, and refreshing quality context')
    .waitFor({ state: 'hidden' })
  const protectedPreserved =
    (await page.getByLabel(/Batch\/Lot Number/).inputValue()) ===
      'CHG-260712A' &&
    !(await page.locator('body').textContent()).includes('Complaint number 123')
  await page
    .getByLabel('Correction instruction')
    .fill(
      'The expiry date is incorrect. Remove it because it was not provided.',
    )
  await page.getByRole('button', { name: 'Apply Correction' }).click()
  await page.waitForFunction(
    () =>
      document.querySelector('input[name="expiryRetestDate"]')?.value === '',
  )
  const explicitClearWorked =
    (await page.getByLabel('Expiry/Retest Date').inputValue()) === ''
  await page.route('**/api/complaints/correct', (route) => route.abort())
  await page
    .getByLabel('Correction instruction')
    .fill('Set the customer name to Fictional Retry Company.')
  await page.getByRole('button', { name: 'Apply Correction' }).click()
  await page.getByRole('button', { name: 'Retry correction' }).waitFor()
  const failureDraftPreserved =
    (await page.getByLabel(/Batch\/Lot Number/).inputValue()) === 'CHG-260712A'
  const failureInstructionPreserved = (
    await page.getByLabel('Correction instruction').inputValue()
  ).includes('Fictional Retry')
  await page.unroute('**/api/complaints/correct')

  await page
    .getByLabel('Choose a PDF or drag it here')
    .setInputFiles(path.join(samples, 'fictional-textless-complaint.pdf'))
  await page.getByRole('button', { name: 'Process PDF' }).click()
  const textlessError = await page
    .getByRole('alert')
    .filter({ hasText: 'No readable text' })
    .textContent()
  const draftPreservedAfterTextless =
    (await page.getByLabel(/Batch\/Lot Number/).inputValue()) === 'CHG-260712A'

  await page.getByRole('button', { name: 'Reset Form' }).click()
  await page
    .getByLabel('Complaint text or email')
    .fill(
      'A customer reports damaged tablets. No batch or quantity was provided.',
    )
  await page.getByRole('button', { name: 'Process Complaint' }).click()
  await page.getByText('Assessment: NEEDS INFORMATION').waitFor()
  const incompleteBatch = await page
    .getByLabel(/Batch\/Lot Number/)
    .inputValue()
  const incompleteAssessment = await page
    .getByLabel('AI quality assessment')
    .textContent()

  console.log(
    JSON.stringify({
      initialCount,
      afterFdfProcessing,
      afterFdfCorrection,
      afterApiProcessing,
      automaticPersistencePrevented:
        initialCount === afterFdfProcessing &&
        afterApiProcessing === initialCount + 1,
      fdfProductType,
      fdfBatch,
      correctedFdfBatch,
      correctedFdfQuantity,
      fdfUnrelatedPreserved: fdfCustomerBefore === fdfCustomerAfter,
      fdfAssessmentRefreshed: Boolean(refreshedFdfAssessment),
      fdfCategory,
      fdfSeverity,
      fdfRisk,
      fdfAction,
      disclaimerVisible: fdfAssessment?.includes(
        'AI-generated initial assessment for QA review',
      ),
      complaintNumber,
      complaintId: committed?.id,
      apiProductType,
      apiGrade,
      apiBatch,
      apiQuantity,
      apiAssessment,
      correctedApiBatch,
      correctedApiQuantity,
      apiCustomerPreserved,
      ambiguousPreserved,
      protectedPreserved,
      explicitClearWorked,
      failureDraftPreserved,
      failureInstructionPreserved,
      textlessError,
      draftPreservedAfterTextless,
      incompleteBatch: incompleteBatch || null,
      incompleteAssessment,
    }),
  )
} finally {
  await Promise.race([
    browser.close(),
    new Promise((resolve) => setTimeout(resolve, 5_000)),
  ])
}
process.exit(0)
