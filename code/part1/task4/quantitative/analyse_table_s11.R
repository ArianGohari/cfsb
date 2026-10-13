#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(readxl)
  library(limma)
  library(jsonlite)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3) {
  stop("Usage: analyse_table_s11.R <normalized.xlsx> <protein_table.xlsx> <output_dir>")
}

normalized_path <- args[[1]]
protein_path <- args[[2]]
output_dir <- args[[3]]
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

normalized <- read_excel(normalized_path, sheet = "Caco2_norm_file", .name_repair = "minimal")
protein_table <- read_excel(protein_path, sheet = "Proteins", .name_repair = "minimal")

names(normalized)[[1]] <- "accession"
sample_names <- names(normalized)[-1]
expected_names <- c(
  "R2_Caco2_Mock_U1", "R2_Caco2_SARS-CoV-2_T1",
  "R2_Caco2_Mock_U2", "R2_Caco2_SARS-CoV-2_T2",
  "R2_Caco2_Mock_U3", "R2_Caco2_SARS-CoV-2_T3"
)
stopifnot(identical(sample_names, expected_names))
stopifnot(!anyDuplicated(normalized$accession), !anyNA(normalized$accession))

samples <- data.frame(
  sample = sample_names,
  condition = rep(c("mock", "treated"), 3),
  replicate_label = rep(1:3, each = 2),
  stringsAsFactors = FALSE
)
write.table(samples, file.path(output_dir, "sample_metadata.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)

matrix_values <- as.matrix(normalized[, -1])
storage.mode(matrix_values) <- "numeric"
rownames(matrix_values) <- normalized$accession
stopifnot(all(is.finite(matrix_values)))

annotations <- data.frame(
  accession = as.character(protein_table[["Accession"]]),
  gene_symbol = as.character(protein_table[["Gene Symbol"]]),
  description = as.character(protein_table[["Description"]]),
  stringsAsFactors = FALSE
)
annotations <- annotations[!duplicated(annotations$accession), ]
match_index <- match(rownames(matrix_values), annotations$accession)
annotation_out <- annotations[match_index, ]
annotation_out$accession <- rownames(matrix_values)

condition <- factor(samples$condition, levels = c("mock", "treated"))
primary_design <- model.matrix(~condition)
primary_fit <- eBayes(lmFit(matrix_values, primary_design), robust = TRUE)
primary <- topTable(primary_fit, coef = "conditiontreated", number = Inf, sort.by = "none")

paired_design <- model.matrix(~factor(samples$replicate_label) + condition)
paired_fit <- eBayes(lmFit(matrix_values, paired_design), robust = TRUE)
paired <- topTable(paired_fit, coef = "conditiontreated", number = Inf, sort.by = "none")

result <- data.frame(
  accession = rownames(primary),
  gene_symbol = annotation_out$gene_symbol,
  description = annotation_out$description,
  difference_normalized = primary$logFC,
  average_normalized = primary$AveExpr,
  moderated_t = primary$t,
  p_value = primary$P.Value,
  fdr_bh = primary$adj.P.Val,
  log_odds = primary$B,
  paired_difference_normalized = paired$logFC,
  paired_p_value = paired$P.Value,
  paired_fdr_bh = paired$adj.P.Val,
  stringsAsFactors = FALSE
)
write.table(result, file.path(output_dir, "table_s11_differential.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)

sensitivity <- data.frame(
  model = c("primary_unpaired_robust_limma", "sensitivity_paired_robust_limma"),
  residual_df = c(primary_fit$df.residual[[1]], paired_fit$df.residual[[1]]),
  proteins = c(nrow(primary), nrow(paired)),
  fdr_bh_lt_0_05 = c(sum(primary$adj.P.Val < 0.05), sum(paired$adj.P.Val < 0.05)),
  fdr_bh_lt_0_10 = c(sum(primary$adj.P.Val < 0.10), sum(paired$adj.P.Val < 0.10)),
  stringsAsFactors = FALSE
)
write.table(sensitivity, file.path(output_dir, "sensitivity_summary.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)

svg(file.path(output_dir, "table_s11_volcano.svg"), width = 8, height = 5.2)
plot(
  result$difference_normalized,
  -log10(pmax(result$fdr_bh, .Machine$double.xmin)),
  pch = 16,
  cex = 0.42,
  col = ifelse(result$fdr_bh < 0.05, "#A61C3C", "#6E7781"),
  xlab = "Differenz der gelieferten normalisierten Werte (T minus U)",
  ylab = "-log10(BH-FDR)",
  main = "Table S11: unpaariges limma-Modell"
)
abline(v = 0, lty = 2, col = "#555555")
abline(h = -log10(0.05), lty = 2, col = "#555555")
legend("topright", legend = c("BH-FDR < 0,05", "sonstige"), pch = 16, col = c("#A61C3C", "#6E7781"), bty = "n")
dev.off()

png(file.path(output_dir, "table_s11_volcano.png"), width = 1440, height = 936, res = 180)
plot(
  result$difference_normalized,
  -log10(pmax(result$fdr_bh, .Machine$double.xmin)),
  pch = 16,
  cex = 0.42,
  col = ifelse(result$fdr_bh < 0.05, "#A61C3C", "#6E7781"),
  xlab = "Differenz der gelieferten normalisierten Werte (T minus U)",
  ylab = "-log10(BH-FDR)",
  main = "Table S11: unpaariges limma-Modell"
)
abline(v = 0, lty = 2, col = "#555555")
abline(h = -log10(0.05), lty = 2, col = "#555555")
legend("topright", legend = c("BH-FDR < 0,05", "sonstige"), pch = 16, col = c("#A61C3C", "#6E7781"), bty = "n")
dev.off()

summary <- list(
  analysis_date = as.character(Sys.Date()),
  input = list(
    normalized_table = basename(normalized_path),
    protein_annotation_table = basename(protein_path),
    proteins = nrow(result),
    exact_accession_matches = sum(!is.na(match_index)),
    samples = nrow(samples),
    sample_headers = sample_names
  ),
  primary_model = list(
    description = "unpaired robust limma; supplied normalized values; T minus U",
    rationale = "The worksheet labels three U/T replicates but does not document paired biological subjects. The unpaired model is therefore primary.",
    fdr_bh_lt_0_05 = sum(result$fdr_bh < 0.05),
    fdr_bh_lt_0_10 = sum(result$fdr_bh < 0.10)
  ),
  sensitivity_model = list(
    description = "paired robust limma with replicate label as blocking term; sensitivity only",
    fdr_bh_lt_0_05 = sum(result$paired_fdr_bh < 0.05),
    fdr_bh_lt_0_10 = sum(result$paired_fdr_bh < 0.10)
  ),
  limitations = c(
    "The workbook provides normalized values and headers, but no subject-level pairing metadata.",
    "Differences are reported on the supplied normalized scale; they are not called fold changes.",
    "The calculation is a secondary analysis of Table S11 and does not recreate the publication's full preprocessing pipeline."
  )
)
write(toJSON(summary, pretty = TRUE, auto_unbox = TRUE), file.path(output_dir, "table_s11_summary.json"))
cat(toJSON(summary, auto_unbox = TRUE), "\n")
