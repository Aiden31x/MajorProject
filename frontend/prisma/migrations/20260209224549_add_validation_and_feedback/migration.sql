-- CreateTable
CREATE TABLE "validation_results" (
    "id" TEXT NOT NULL,
    "clauseText" TEXT NOT NULL,
    "clauseCategory" TEXT NOT NULL,
    "riskScore" DOUBLE PRECISION NOT NULL,
    "status" TEXT NOT NULL,
    "confidence" DOUBLE PRECISION NOT NULL,
    "issues" JSONB NOT NULL,
    "documentSource" TEXT,
    "timestamp" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "validationTimeMs" DOUBLE PRECISION,

    CONSTRAINT "validation_results_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "feedback" (
    "id" TEXT NOT NULL,
    "validation_result_id" TEXT NOT NULL,
    "thumbsUp" BOOLEAN NOT NULL,
    "followUpReason" TEXT,
    "additionalComments" TEXT,
    "tags" JSONB NOT NULL,
    "agentDecision" TEXT NOT NULL,
    "userAcceptedClause" BOOLEAN,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "feedback_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "validation_results_status_timestamp_idx" ON "validation_results"("status", "timestamp");

-- CreateIndex
CREATE INDEX "validation_results_clauseCategory_timestamp_idx" ON "validation_results"("clauseCategory", "timestamp");

-- CreateIndex
CREATE UNIQUE INDEX "feedback_validation_result_id_key" ON "feedback"("validation_result_id");

-- CreateIndex
CREATE INDEX "feedback_thumbsUp_created_at_idx" ON "feedback"("thumbsUp", "created_at");

-- CreateIndex
CREATE INDEX "feedback_agentDecision_created_at_idx" ON "feedback"("agentDecision", "created_at");

-- AddForeignKey
ALTER TABLE "feedback" ADD CONSTRAINT "feedback_validation_result_id_fkey" FOREIGN KEY ("validation_result_id") REFERENCES "validation_results"("id") ON DELETE CASCADE ON UPDATE CASCADE;
