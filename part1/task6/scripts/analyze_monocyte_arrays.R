#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(limma)
  library(jsonlite)
})

args <- commandArgs(trailingOnly = TRUE)
root <- if (length(args)) normalizePath(args[[1]]) else normalizePath(file.path(dirname(sub("^--file=", "", commandArgs()[grep("^--file=", commandArgs())])), ".."))
sources <- file.path(root, "sources")
out <- file.path(root, "analysis")
figures <- file.path(root, "figures")
dir.create(out, showWarnings = FALSE)
dir.create(figures, showWarnings = FALSE)

read_geo_matrix <- function(path) {
  lines <- readLines(gzfile(path), warn = FALSE)
  begin <- match("!series_matrix_table_begin", lines)
  end <- match("!series_matrix_table_end", lines)
  stopifnot(!is.na(begin), !is.na(end), end > begin)
  table <- read.delim(
    text = paste(lines[(begin + 1):(end - 1)], collapse = "\n"),
    check.names = FALSE, quote = "\"", stringsAsFactors = FALSE
  )
  ids <- table[[1]]
  matrix <- as.matrix(table[-1])
  storage.mode(matrix) <- "double"
  rownames(matrix) <- ids
  meta_value <- function(key) {
    hit <- lines[startsWith(lines, paste0(key, "\t"))]
    stopifnot(length(hit) == 1)
    values <- strsplit(hit, "\t", fixed = TRUE)[[1]][-1]
    gsub('^"|"$', "", values)
  }
  list(
    matrix = matrix,
    accession = meta_value("!Sample_geo_accession"),
    title = meta_value("!Sample_title"),
    platform = unique(meta_value("!Sample_platform_id")),
    processing = unique(meta_value("!Sample_data_processing"))
  )
}

read_annotation <- function(path) {
  lines <- readLines(gzfile(path), warn = FALSE)
  begin <- match("!platform_table_begin", lines)
  end <- match("!platform_table_end", lines)
  stopifnot(!is.na(begin), !is.na(end), end > begin)
  read.delim(
    text = paste(lines[(begin + 1):(end - 1)], collapse = "\n"),
    check.names = FALSE, quote = "", stringsAsFactors = FALSE,
    comment.char = "", fill = TRUE
  )
}

write_tsv <- function(x, path) {
  write.table(x, path, sep = "\t", row.names = FALSE, quote = FALSE, na = "")
}

make_samples <- function(geo, species) {
  title <- geo$title
  if (species == "mouse") {
    group <- ifelse(grepl("Gr1hi", title), "classical", "nonclassical")
    pair <- sub(".* ", "", title)
    biological_unit <- "pool of five mice"
    series <- "GSE17256"
  } else {
    group <- ifelse(grepl("CD16-", title, fixed = TRUE), "classical", "nonclassical")
    pair <- sub(".* ", "", title)
    biological_unit <- "human donor"
    series <- "GSE18565"
  }
  data.frame(
    series = series, species = species, sample = geo$accession, title = title,
    group = group, pair = pair, biological_unit = biological_unit,
    stringsAsFactors = FALSE
  )
}

fit_matrix <- function(expr, samples) {
  stopifnot(identical(colnames(expr), samples$sample))
  samples$pair <- factor(samples$pair)
  samples$group <- factor(samples$group, levels = c("nonclassical", "classical"))
  design <- model.matrix(~ pair + group, samples)
  coefficient <- match("groupclassical", colnames(design))
  stopifnot(!is.na(coefficient))
  fit <- eBayes(lmFit(expr, design), trend = TRUE)
  result <- topTable(fit, coef = coefficient, number = Inf, sort.by = "none")
  se <- fit$stdev.unscaled[, coefficient] * sqrt(fit$s2.post)
  critical <- qt(0.975, df = fit$df.total)
  result$ci_low <- fit$coefficients[, coefficient] - critical * se
  result$ci_high <- fit$coefficients[, coefficient] + critical * se
  result$feature <- rownames(result)
  result$residual_df <- fit$df.residual
  result[, c("feature", "logFC", "ci_low", "ci_high", "AveExpr", "t", "P.Value", "adj.P.Val", "B", "residual_df")]
}

fit_unpaired_matrix <- function(expr, samples) {
  stopifnot(identical(colnames(expr), samples$sample))
  samples$group <- factor(samples$group, levels = c("nonclassical", "classical"))
  design <- model.matrix(~ group, samples)
  coefficient <- match("groupclassical", colnames(design))
  fit <- eBayes(lmFit(expr, design), trend = TRUE)
  result <- topTable(fit, coef = coefficient, number = Inf, sort.by = "none")
  data.frame(feature = rownames(result), logFC = result$logFC, P.Value = result$P.Value, stringsAsFactors = FALSE)
}

collapse_genes <- function(expr, annotation, symbols) {
  stopifnot(identical(rownames(expr), annotation$ID))
  rows <- lapply(symbols, function(symbol) {
    idx <- which(trimws(annotation[["Gene symbol"]]) == symbol)
    if (!length(idx)) return(rep(NA_real_, ncol(expr)))
    colMeans(expr[idx, , drop = FALSE])
  })
  matrix <- do.call(rbind, rows)
  rownames(matrix) <- symbols
  colnames(matrix) <- colnames(expr)
  matrix
}

program_scores <- function(gene_expr, programs) {
  scores <- sapply(names(programs), function(program) {
    present <- intersect(programs[[program]], rownames(gene_expr))
    present <- present[rowSums(is.na(gene_expr[present, , drop = FALSE])) == 0]
    stopifnot(length(present) > 0)
    z <- t(scale(t(gene_expr[present, , drop = FALSE])))
    colMeans(z, na.rm = TRUE)
  })
  t(scores)
}

mouse_geo <- read_geo_matrix(file.path(sources, "GSE17256_series_matrix.txt.gz"))
human_geo <- read_geo_matrix(file.path(sources, "GSE18565_series_matrix.txt.gz"))
mouse_anno <- read_annotation(file.path(sources, "GPL1261.annot.gz"))
human_anno <- read_annotation(file.path(sources, "GPL570.annot.gz"))
stopifnot(mouse_geo$platform == "GPL1261", human_geo$platform == "GPL570")
stopifnot(all(mouse_geo$matrix > 0), all(human_geo$matrix > 0))

mouse_samples <- make_samples(mouse_geo, "mouse")
human_samples <- make_samples(human_geo, "human")
samples <- rbind(mouse_samples, human_samples)
write_tsv(samples, file.path(out, "sample_metadata.tsv"))

# GEO stores the authors' GC-RMA values on the linear scale. The model uses
# log2 expression, and the paired block follows the replicate number in the
# sample title (same pool/donor contributes both sorted subsets).
mouse_expr <- log2(mouse_geo$matrix)
human_expr <- log2(human_geo$matrix)
colnames(mouse_expr) <- mouse_geo$accession
colnames(human_expr) <- human_geo$accession
mouse_anno <- mouse_anno[match(rownames(mouse_expr), mouse_anno$ID), , drop = FALSE]
human_anno <- human_anno[match(rownames(human_expr), human_anno$ID), , drop = FALSE]
stopifnot(!anyNA(mouse_anno$ID), !anyNA(human_anno$ID))
stopifnot(identical(rownames(mouse_expr), mouse_anno$ID))
stopifnot(identical(rownames(human_expr), human_anno$ID))

mouse_probe <- fit_matrix(mouse_expr, mouse_samples)
human_probe <- fit_matrix(human_expr, human_samples)
write.table(mouse_probe, gzfile(file.path(out, "mouse_probe_differential.tsv.gz")), sep = "\t", row.names = FALSE, quote = FALSE)
write.table(human_probe, gzfile(file.path(out, "human_probe_differential.tsv.gz")), sep = "\t", row.names = FALSE, quote = FALSE)

mouse_programs <- list(
  network_efflux = c("Abca1", "Abcg1"),
  network_recruitment = c("Ccr2", "Ccr5", "Cx3cr1"),
  network_il1b = c("Il1b"),
  classical_monocyte = c("Ccr2", "Ly6c2", "S100a8", "S100a9", "Lyz2", "Sell"),
  patrolling_monocyte = c("Cx3cr1", "Nr4a1", "Lst1", "Itgam"),
  lipid_macrophage = c("Trem2", "Lpl", "Apoe", "Abca1", "Abcg1", "Cd68"),
  neutrophil_granule = c("S100a8", "S100a9", "Lcn2", "Camp", "Elane", "Mpo", "Cxcr2", "Retnlg")
)
human_programs <- lapply(mouse_programs, toupper)
mouse_symbols <- unique(c("Abca1", "Abcg1", "Ccr2", "Ccr5", "Cx3cr1", "Il1b", unlist(mouse_programs)))
human_symbols <- unique(c("ABCA1", "ABCG1", "CCR2", "CCR5", "CX3CR1", "IL1B", unlist(human_programs)))
mouse_genes <- collapse_genes(mouse_expr, mouse_anno, mouse_symbols)
human_genes <- collapse_genes(human_expr, human_anno, human_symbols)
stopifnot(!anyNA(mouse_genes[c("Abca1", "Abcg1", "Ccr2", "Ccr5", "Cx3cr1", "Il1b"), ]))
stopifnot(!anyNA(human_genes[c("ABCA1", "ABCG1", "CCR2", "CCR5", "CX3CR1", "IL1B"), ]))
mouse_genes <- mouse_genes[rowSums(is.na(mouse_genes)) == 0, , drop = FALSE]
human_genes <- human_genes[rowSums(is.na(human_genes)) == 0, , drop = FALSE]

mouse_gene_fit <- fit_matrix(mouse_genes, mouse_samples)
human_gene_fit <- fit_matrix(human_genes, human_samples)
mouse_gene_fit$species <- "mouse"
human_gene_fit$species <- "human"
gene_results <- rbind(mouse_gene_fit, human_gene_fit)
gene_results$selected_adj_p <- ave(gene_results$P.Value, gene_results$species, FUN = function(x) p.adjust(x, method = "BH"))
gene_results <- gene_results[, c("species", setdiff(names(gene_results), "species"))]
write_tsv(gene_results, file.path(out, "selected_gene_results.tsv"))

mouse_scores <- program_scores(mouse_genes, mouse_programs)
human_scores <- program_scores(human_genes, human_programs)
mouse_score_fit <- fit_matrix(mouse_scores, mouse_samples)
human_score_fit <- fit_matrix(human_scores, human_samples)
mouse_score_fit$species <- "mouse"
human_score_fit$species <- "human"
program_tests <- rbind(mouse_score_fit, human_score_fit)
program_tests$program_adj_p <- ave(program_tests$P.Value, program_tests$species, FUN = function(x) p.adjust(x, method = "BH"))
program_tests <- program_tests[, c("species", setdiff(names(program_tests), "species"))]
write_tsv(program_tests, file.path(out, "program_tests.tsv"))

make_sensitivity <- function(primary, unpaired, species, level) {
  unpaired <- unpaired[match(primary$feature, unpaired$feature), ]
  data.frame(
    species = species, level = level, feature = primary$feature,
    paired_logFC = primary$logFC, paired_p = primary$P.Value,
    unpaired_logFC = unpaired$logFC, unpaired_p = unpaired$P.Value,
    direction_stable = sign(primary$logFC) == sign(unpaired$logFC),
    stringsAsFactors = FALSE
  )
}
sensitivity <- rbind(
  make_sensitivity(mouse_gene_fit, fit_unpaired_matrix(mouse_genes, mouse_samples), "mouse", "gene"),
  make_sensitivity(human_gene_fit, fit_unpaired_matrix(human_genes, human_samples), "human", "gene"),
  make_sensitivity(mouse_score_fit, fit_unpaired_matrix(mouse_scores, mouse_samples), "mouse", "program"),
  make_sensitivity(human_score_fit, fit_unpaired_matrix(human_scores, human_samples), "human", "program")
)
write_tsv(sensitivity, file.path(out, "paired_unpaired_sensitivity.tsv"))

score_rows <- function(scores, sample_table, species) {
  data.frame(
    species = species,
    sample = rep(sample_table$sample, each = nrow(scores)),
    group = rep(sample_table$group, each = nrow(scores)),
    pair = rep(sample_table$pair, each = nrow(scores)),
    program = rep(rownames(scores), times = ncol(scores)),
    score = as.vector(scores), stringsAsFactors = FALSE
  )
}
score_table <- rbind(score_rows(mouse_scores, mouse_samples, "mouse"), score_rows(human_scores, human_samples, "human"))
write_tsv(score_table, file.path(out, "program_scores.tsv"))

orthologs <- read.delim(file.path(out, "ortholog_pairs.tsv"), stringsAsFactors = FALSE)
mouse_index <- match(orthologs$mouse_symbol, mouse_gene_fit$feature)
human_index <- match(orthologs$human_symbol, human_gene_fit$feature)
available <- !is.na(mouse_index) & !is.na(human_index)
orthologs <- orthologs[available, , drop = FALSE]
mouse_lookup <- mouse_gene_fit[mouse_index[available], ]
human_lookup <- human_gene_fit[human_index[available], ]
stopifnot(!anyNA(mouse_lookup$logFC), !anyNA(human_lookup$logFC), nrow(orthologs) >= 12)
ortholog_results <- cbind(
  orthologs,
  mouse_log2fc = mouse_lookup$logFC,
  mouse_p = mouse_lookup$P.Value,
  human_log2fc = human_lookup$logFC,
  human_p = human_lookup$P.Value
)
ortholog_results$direction_concordant <- sign(ortholog_results$mouse_log2fc) == sign(ortholog_results$human_log2fc)
write_tsv(ortholog_results, file.path(out, "ortholog_concordance.tsv"))
rho_test <- suppressWarnings(cor.test(ortholog_results$mouse_log2fc, ortholog_results$human_log2fc, method = "spearman", exact = FALSE))

svg(file.path(figures, "quantitative_results.svg"), width = 11.5, height = 4.4, pointsize = 10)
layout(matrix(1:3, nrow = 1), widths = c(1, 1.1, 1.15))
par(mar = c(5, 4, 2.5, 1), las = 1)
network <- c("Abca1", "Abcg1", "Ccr2", "Ccr5", "Cx3cr1", "Il1b")
net <- mouse_gene_fit[match(network, mouse_gene_fit$feature), ]
ylim <- range(c(net$ci_low, net$ci_high))
plot(seq_along(network), net$logFC, ylim = ylim, pch = 19, xaxt = "n", xlab = "", ylab = "log2 fold change", main = "Maus: Ly6C-hi vs. Ly6C-lo")
arrows(seq_along(network), net$ci_low, seq_along(network), net$ci_high, angle = 90, code = 3, length = 0.04)
abline(h = 0, col = "grey50", lty = 2)
axis(1, seq_along(network), network, las = 2)

mouse_program_fit <- program_tests[program_tests$species == "mouse", ]
ord <- order(mouse_program_fit$logFC)
cols <- ifelse(mouse_program_fit$program_adj_p[ord] < 0.05, "#a63603", "#636363")
program_labels <- c(
  network_efflux = "Efflux", network_recruitment = "Rekrutierung", network_il1b = "IL-1beta",
  classical_monocyte = "klassische Monozyten", patrolling_monocyte = "patrouillierende Monozyten",
  lipid_macrophage = "Lipid-Makrophagen", neutrophil_granule = "Neutrophilen-Granula"
)
par(mar = c(4, 9, 2.5, 1), las = 1)
barplot(mouse_program_fit$logFC[ord], names.arg = program_labels[mouse_program_fit$feature[ord]], horiz = TRUE, col = cols, border = NA, xlab = "score difference", main = "Maus: vorab definierte Programme")
abline(v = 0, col = "grey40")

par(mar = c(4, 4, 2.5, 1), las = 1)
plot(ortholog_results$mouse_log2fc, ortholog_results$human_log2fc, pch = 19, col = "#2b6f92", xlab = "Maus log2 FC", ylab = "Mensch log2 FC", main = sprintf("%d Orthologpaare: rho = %.2f", nrow(ortholog_results), unname(rho_test$estimate)))
abline(h = 0, v = 0, col = "grey65", lty = 2)
text(ortholog_results$mouse_log2fc, ortholog_results$human_log2fc, labels = ortholog_results$mouse_symbol, pos = 3, cex = 0.65)
dev.off()

summary <- list(
  generated_on = "2026-09-24",
  contrast = "classical minus nonclassical monocytes",
  mouse = list(samples = nrow(mouse_samples), biological_replicates_per_group = 4, residual_df = unique(mouse_probe$residual_df), probe_discoveries_fdr_0_05 = sum(mouse_probe$adj.P.Val < 0.05)),
  human = list(samples = nrow(human_samples), biological_replicates_per_group = 3, residual_df = unique(human_probe$residual_df), probe_discoveries_fdr_0_05 = sum(human_probe$adj.P.Val < 0.05)),
  ortholog_comparison = list(n = nrow(ortholog_results), spearman_rho = unname(rho_test$estimate), p_value = rho_test$p.value, direction_concordant = sum(ortholog_results$direction_concordant)),
  paired_unpaired_sensitivity = list(features = nrow(sensitivity), direction_stable = sum(sensitivity$direction_stable)),
  interpretation_limit = "Subset contrasts in blood monocytes; no disease contrast and no cell-fraction estimate."
)
write_json(summary, file.path(out, "summary.json"), pretty = TRUE, auto_unbox = TRUE, digits = 10)
writeLines(trimws(capture.output(sessionInfo()), which = "right"), file.path(out, "session_info.txt"))
cat(toJSON(summary, pretty = TRUE, auto_unbox = TRUE), "\n")
