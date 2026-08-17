import { z } from 'zod'

const requiredText = (label: string, maximum: number) =>
  z.string().trim().min(1, `${label} is required`).max(maximum)

export const complaintFormSchema = z.object({
  complaintSource: z.string().trim().max(255),
  customerName: requiredText('Customer name', 200),
  productType: z.enum(['API', 'FDF', 'UNKNOWN']),
  productName: requiredText('Product name', 200),
  productStrengthGrade: z.string().trim().max(100),
  batchLotNumber: requiredText('Batch/Lot number', 100),
  affectedQuantity: z.string().trim().max(100),
  manufacturingDate: z.string().trim().max(100),
  expiryRetestDate: z.string().trim().max(100),
  originatingSiteBlock: z.string().trim().max(200),
  impactedNonProductMaterials: z.string().trim().max(2000),
  complaintCategory: requiredText('Complaint category', 150),
  complaintDescription: requiredText('Complaint description', 5000),
  suggestedSeverity: z.union([
    z.literal(''),
    z.enum(['MINOR', 'MAJOR', 'CRITICAL']),
  ]),
  initialRiskAssessment: z.string().trim().max(5000),
  suggestedNextAction: z.string().trim().max(5000),
})

export type ComplaintFormValues = z.infer<typeof complaintFormSchema>
