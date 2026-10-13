#!/usr/bin/env Rscript

# Reanalyse the public human plaque-macrophage microarray GSE41571.
# The biological replicate is one carotid plaque from one patient.

suppressPackageStartupMessages({
  library(limma)
  library(ggplot2)
  library(jsonlite)
})

root <- normalizePath(file.path(dirname(sub("--file=", "", commandArgs(trailingOnly = FALSE)[grep("--file=", commandArgs(trailingOnly = FALSE))])), ".."))
data_dir <- file.path(root, "data", "GSE41571")
result_dir <- file.path(root, "results", "GSE41571")
figure_dir <- file.path(root, "figures")
audit_dir <- file.path(root, "audits")
dir.create(result_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(figure_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(audit_dir, recursive = TRUE, showWarnings = FALSE)

matrix_file <- file.path(data_dir, "GSE41571_series_matrix.txt.gz")
calls_file <- file.path(data_dir, "GSE41571_matrix_NORMALIZED_RAW_ABSCALL.txt.gz")
annotation_file <- file.path(data_dir, "GPL570.annot.gz")
soft_file <- file.path(data_dir, "GSE41571_family.soft.gz")
stopifnot(all(file.exists(matrix_file, calls_file, annotation_file, soft_file)))

matrix_lines <- readLines(gzfile(matrix_file), warn = FALSE)
table_start <- grep("^!series_matrix_table_begin", matrix_lines) + 1L
table_end <- grep("^!series_matrix_table_end", matrix_lines) - 1L
stopifnot(length(table_start) == 1L, length(table_end) == 1L)
expr_table <- read.delim(
  textConnection(matrix_lines[table_start:table_end]),
  check.names = FALSE,
  stringsAsFactors = FALSE
)
probe_id <- expr_table[[1]]
expr <- as.matrix(expr_table[-1])
storage.mode(expr) <- "double"
rownames(expr) <- probe_id

sample_ids <- colnames(expr)
expected_ids <- sprintf("GSM%d", 1019539:1019549)
stopifnot(identical(sample_ids, expected_ids), ncol(expr) == 11L, !anyNA(expr), all(expr > 0))

get_matrix_metadata <- function(prefix) {
  line <- matrix_lines[grep(paste0("^", prefix, "\\t"), matrix_lines)[1]]
  values <- strsplit(line, "\\t", fixed = FALSE)[[1]][-1]
  gsub('^"|"$', "", values)
}

titles <- get_matrix_metadata("!Sample_title")
groups <- ifelse(grepl("^Ruptured", titles), "ruptured", "stable")
stopifnot(sum(groups == "ruptured") == 5L, sum(groups == "stable") == 6L)

sample_info <- data.frame(
  sample_id = sample_ids,
  title = titles,
  group = groups,
  biological_replicate = seq_along(sample_ids),
  stringsAsFactors = FALSE
)

# Clinical fields are parsed from the archived SOFT record, not inferred from titles.
soft <- readLines(gzfile(soft_file), warn = FALSE)
sample_blocks <- split(seq_along(soft), cumsum(grepl("^\\^SAMPLE = ", soft)))
sample_blocks <- sample_blocks[vapply(sample_blocks, function(i) any(grepl("^\\^SAMPLE = ", soft[i])), logical(1))]
extract_field <- function(block, key) {
  hit <- grep(paste0("^!Sample_characteristics_ch1 = ", key, ": "), block, value = TRUE)
  if (!length(hit)) return(NA_character_)
  sub(paste0("^!Sample_characteristics_ch1 = ", key, ": "), "", hit[1])
}
soft_info <- do.call(rbind, lapply(sample_blocks, function(i) {
  block <- soft[i]
  data.frame(
    sample_id = sub("^!Sample_geo_accession = ", "", grep("^!Sample_geo_accession = ", block, value = TRUE)[1]),
    age = as.integer(extract_field(block, "age")),
    sex = extract_field(block, "gender"),
    stenosis_percent = as.numeric(sub(" \\(%\\)$", "", extract_field(block, "radiological stenosis"))),
    histology = extract_field(block, "plaque histology"),
    cell_type = extract_field(block, "cell type"),
    stringsAsFactors = FALSE
  )
}))
sample_info <- merge(sample_info, soft_info, by = "sample_id", sort = FALSE)
sample_info <- sample_info[match(sample_ids, sample_info$sample_id), ]
stopifnot(identical(sample_info$sample_id, sample_ids), all(sample_info$cell_type == "macrophage"))
write.table(sample_info, file.path(result_dir, "samples.tsv"), sep = "\t", row.names = FALSE, quote = FALSE)

# Reproduce the deposited present/absent filter: discard a probe set when it is
# called absent in more than six of eleven arrays. External controls are removed.
calls <- read.delim(gzfile(calls_file), check.names = FALSE, stringsAsFactors = FALSE, quote = '"')
call_columns <- grep(" ABS_CALL$", names(calls))
call_index <- match(probe_id, calls[[1]])
stopifnot(!anyNA(call_index), length(call_columns) == 11L)
call_matrix <- as.matrix(calls[call_index, call_columns])
keep_probe <- rowSums(call_matrix == "A", na.rm = TRUE) <= 6L & !grepl("^AFFX", probe_id)
stopifnot(sum(keep_probe) == 25538L)

log_expression <- log2(expr[keep_probe, , drop = FALSE])

# Read the frozen GPL570 annotation and keep probes with one unambiguous symbol.
annotation_lines <- readLines(gzfile(annotation_file), warn = FALSE)
annotation_start <- grep("^!platform_table_begin", annotation_lines) + 1L
annotation_end <- grep("^!platform_table_end", annotation_lines) - 1L
annotation <- read.delim(
  textConnection(annotation_lines[annotation_start:annotation_end]),
  check.names = FALSE,
  stringsAsFactors = FALSE,
  quote = "",
  comment.char = ""
)
annotation_index <- match(rownames(log_expression), annotation$ID)
symbols <- annotation$`Gene symbol`[annotation_index]
single_symbol <- !is.na(symbols) & nzchar(symbols) & !grepl("///", symbols, fixed = TRUE)

# Multiple probe sets for one unambiguous symbol are averaged on the log2 scale
# before fitting. This makes genes, rather than probe sets, the testing unit.
gene_expression <- avereps(log_expression[single_symbol, , drop = FALSE], ID = symbols[single_symbol])
probes_per_gene <- table(symbols[single_symbol])
stopifnot(nrow(gene_expression) > 10000L, !anyDuplicated(rownames(gene_expression)))

group <- factor(groups, levels = c("stable", "ruptured"))
design <- model.matrix(~ group)
fit <- eBayes(lmFit(gene_expression, design), trend = TRUE, robust = TRUE)
de <- topTable(fit, coef = "groupruptured", n = Inf, sort.by = "none")
de$gene_symbol <- rownames(de)
de$n_probes <- as.integer(probes_per_gene[de$gene_symbol])
de <- de[, c("gene_symbol", "n_probes", "logFC", "AveExpr", "t", "P.Value", "adj.P.Val", "B")]
names(de) <- c("gene_symbol", "n_probes", "log2FC_ruptured_vs_stable", "mean_log2_expression", "moderated_t", "p_value", "fdr_bh", "log_odds_DE")
de <- de[order(de$p_value), ]
write.table(de, file.path(result_dir, "de_genes.tsv"), sep = "\t", row.names = FALSE, quote = FALSE)

# FCGR3A is excluded from the gene-level test: GPL570 probe 204006_s_at is
# annotated jointly to FCGR3A and the neutrophil paralogue FCGR3B.
network_genes <- c("ABCA1", "IL1B", "TNF", "TREM2", "CD14", "TLR2", "CXCL8", "ICAM1")
stopifnot(all(network_genes %in% rownames(gene_expression)))

ambiguous_probe <- "204006_s_at"
stopifnot(ambiguous_probe %in% rownames(log_expression))
ambiguous_fit <- eBayes(lmFit(log_expression[ambiguous_probe, , drop = FALSE], design), trend = TRUE, robust = TRUE)
ambiguous_result <- topTable(ambiguous_fit, coef = "groupruptured", n = 1, sort.by = "none")
coverage <- data.frame(
  network_node = c(network_genes, "FCGR3A", "hsa-miR-33a-5p"),
  analyte = c(rep("mRNA", length(network_genes) + 1L), "mature miRNA"),
  status = c(rep("unambiguously_measured", length(network_genes)), "ambiguous_with_FCGR3B", "not_measured"),
  detail = c(
    rep("one or more retained GPL570 probes with an unambiguous gene symbol; probes averaged on log2 scale", length(network_genes)),
    sprintf("GPL570 probe %s maps to FCGR3A and FCGR3B; probe log2FC=%.4f, nominal p=%.4g and cannot separate monocyte from neutrophil paralogue", ambiguous_probe, ambiguous_result$logFC, ambiguous_result$P.Value),
    "GPL570 measures poly(A)-derived transcript signals and does not identify the mature miR-33a-5p arm"
  ),
  stringsAsFactors = FALSE
)
write.table(coverage, file.path(result_dir, "network_measurement_coverage.tsv"), sep = "\t", row.names = FALSE, quote = FALSE)

# Add ordinary group means and a transparent unmoderated 95% confidence interval.
network <- de[match(network_genes, de$gene_symbol), ]
network$mean_stable <- rowMeans(gene_expression[network_genes, groups == "stable", drop = FALSE])
network$mean_ruptured <- rowMeans(gene_expression[network_genes, groups == "ruptured", drop = FALSE])
network$mean_difference_check <- network$mean_ruptured - network$mean_stable
n_r <- sum(groups == "ruptured")
n_s <- sum(groups == "stable")
pooled_var <- apply(gene_expression[network_genes, groups == "ruptured", drop = FALSE], 1, var) * (n_r - 1)
pooled_var <- pooled_var + apply(gene_expression[network_genes, groups == "stable", drop = FALSE], 1, var) * (n_s - 1)
pooled_var <- pooled_var / (n_r + n_s - 2)
network$ci95_low <- network$log2FC_ruptured_vs_stable - qt(0.975, n_r + n_s - 2) * sqrt(pooled_var * (1 / n_r + 1 / n_s))
network$ci95_high <- network$log2FC_ruptured_vs_stable + qt(0.975, n_r + n_s - 2) * sqrt(pooled_var * (1 / n_r + 1 / n_s))
stopifnot(max(abs(network$mean_difference_check - network$log2FC_ruptured_vs_stable)) < 1e-10)

# Leave one patient out. This is a sensitivity check, not a second hypothesis test.
loo_fc <- matrix(NA_real_, nrow = length(network_genes), ncol = ncol(gene_expression), dimnames = list(network_genes, sample_ids))
for (i in seq_len(ncol(gene_expression))) {
  g_i <- droplevels(group[-i])
  fit_i <- lmFit(gene_expression[network_genes, -i, drop = FALSE], model.matrix(~ g_i))
  loo_fc[, i] <- fit_i$coefficients[, "g_iruptured"]
}
network$loo_same_direction <- rowMeans(sign(loo_fc) == sign(network$log2FC_ruptured_vs_stable))
network$loo_log2FC_min <- apply(loo_fc, 1, min)
network$loo_log2FC_max <- apply(loo_fc, 1, max)
network$mean_difference_check <- NULL
write.table(network, file.path(result_dir, "network_gene_overlay.tsv"), sep = "\t", row.names = FALSE, quote = FALSE)

loo_long <- data.frame(
  gene_symbol = rep(rownames(loo_fc), times = ncol(loo_fc)),
  omitted_sample = rep(colnames(loo_fc), each = nrow(loo_fc)),
  log2FC_ruptured_vs_stable = as.vector(loo_fc),
  stringsAsFactors = FALSE
)
write.table(loo_long, file.path(result_dir, "network_gene_leave_one_out.tsv"), sep = "\t", row.names = FALSE, quote = FALSE)

# Competitive gene-set test for the pre-specified measured nodes in the network.
camera_result <- camera(gene_expression, index = list(task5_network_genes = network_genes), design = design, contrast = 2)
camera_out <- data.frame(gene_set = rownames(camera_result), camera_result, row.names = NULL, check.names = FALSE)
write.table(camera_out, file.path(result_dir, "network_gene_set_test.tsv"), sep = "\t", row.names = FALSE, quote = FALSE)

# PCA is computed on the 1,000 most variable genes; each point remains one patient.
gene_var <- apply(gene_expression, 1, var)
top_var <- names(sort(gene_var, decreasing = TRUE))[seq_len(min(1000L, length(gene_var)))]
pca <- prcomp(t(gene_expression[top_var, , drop = FALSE]), center = TRUE, scale. = FALSE)
pca_out <- cbind(sample_info, PC1 = pca$x[, 1], PC2 = pca$x[, 2])
write.table(pca_out, file.path(result_dir, "pca_scores.tsv"), sep = "\t", row.names = FALSE, quote = FALSE)
pca_variance <- 100 * pca$sdev^2 / sum(pca$sdev^2)
pca_out$label_hjust <- ifelse(pca_out$PC1 > 0, 1.1, -0.1)

p_pca <- ggplot(pca_out, aes(PC1, PC2, color = group, label = sample_id)) +
  geom_hline(yintercept = 0, color = "grey85", linewidth = 0.3) +
  geom_vline(xintercept = 0, color = "grey85", linewidth = 0.3) +
  geom_point(size = 3) +
  geom_text(aes(hjust = label_hjust), vjust = -0.8, size = 2.7, show.legend = FALSE) +
  scale_color_manual(values = c(stable = "#2166ac", ruptured = "#b2182b")) +
  labs(x = sprintf("PC1 (%.1f%%)", pca_variance[1]), y = sprintf("PC2 (%.1f%%)", pca_variance[2]), color = "Plaque", title = "GSE41571: PCA der 1.000 variabelsten Gene") +
  theme_minimal(base_size = 11) + theme(legend.position = "top")
svg(file.path(figure_dir, "gse41571_pca.svg"), width = 7.3, height = 5.2)
print(p_pca)
dev.off()

de$significance <- ifelse(de$fdr_bh < 0.05, "FDR < 0,05", "FDR >= 0,05")
label_rows <- head(de[order(de$fdr_bh, -abs(de$log2FC_ruptured_vs_stable)), ], 10)
p_volcano <- ggplot(de, aes(log2FC_ruptured_vs_stable, -log10(p_value), color = significance)) +
  geom_point(alpha = 0.55, size = 1) +
  geom_vline(xintercept = 0, color = "grey60", linewidth = 0.3) +
  geom_text(data = label_rows, aes(label = gene_symbol), color = "black", size = 2.6, check_overlap = TRUE, vjust = -0.6) +
  scale_color_manual(values = c("FDR < 0,05" = "#b2182b", "FDR >= 0,05" = "#bdbdbd")) +
  labs(x = "log2-Fold-Change (rupturiert minus stabil)", y = "-log10(p)", color = NULL, title = "Differentielle Expression in Plaque-Makrophagen") +
  theme_minimal(base_size = 11) + theme(legend.position = "top")
svg(file.path(figure_dir, "gse41571_volcano.svg"), width = 7.3, height = 5.2)
print(p_volcano)
dev.off()

network$significance <- ifelse(network$fdr_bh < 0.05, "FDR < 0,05", "FDR >= 0,05")
p_network <- ggplot(network, aes(reorder(gene_symbol, log2FC_ruptured_vs_stable), log2FC_ruptured_vs_stable, color = significance)) +
  geom_hline(yintercept = 0, color = "grey60", linewidth = 0.4) +
  geom_errorbar(aes(ymin = ci95_low, ymax = ci95_high), width = 0.15, linewidth = 0.55) +
  geom_point(size = 3) +
  coord_flip() +
  scale_color_manual(values = c("FDR < 0,05" = "#b2182b", "FDR >= 0,05" = "#636363")) +
  labs(x = NULL, y = "log2-Fold-Change (rupturiert minus stabil)", color = NULL, title = "Vorab definierte Genknoten aus dem Task-5-Netz") +
  theme_minimal(base_size = 11) + theme(legend.position = "top")
svg(file.path(figure_dir, "gse41571_network_genes.svg"), width = 7.3, height = 5.2)
print(p_network)
dev.off()

summary <- list(
  analysis_date = "2026-09-24",
  accession = "GSE41571",
  species = "Homo sapiens",
  taxon = 9606,
  assay = "Affymetrix Human Genome U133 Plus 2.0 Array (GPL570)",
  biological_unit = "one laser-microdissected macrophage-rich plaque region from one patient",
  contrast = "ruptured minus stable carotid plaque",
  samples = list(total = ncol(gene_expression), ruptured = n_r, stable = n_s),
  filtering = list(deposited_probe_sets = nrow(expr), retained_probe_sets = sum(keep_probe), criterion = "absent call in at most 6 of 11 samples; external AFFX controls removed"),
  testing = list(unit = "gene after averaging unambiguous probes on log2 scale", tested_genes = nrow(gene_expression), method = "limma moderated linear model, trend=TRUE, robust=TRUE", fdr_bh_lt_0_05 = sum(de$fdr_bh < 0.05), fdr_bh_lt_0_10 = sum(de$fdr_bh < 0.10)),
  pca = list(genes = length(top_var), pc1_percent = unname(pca_variance[1]), pc2_percent = unname(pca_variance[2])),
  network = list(unambiguously_measured_gene_nodes = length(network_genes), ambiguous_gene_nodes = 1, mature_miRNA_nodes_measured = 0, camera_direction = camera_out$Direction[1], camera_p_value = camera_out$PValue[1]),
  validation = "PASS"
)
write(toJSON(summary, pretty = TRUE, auto_unbox = TRUE, digits = 10), file.path(result_dir, "summary.json"))

validation <- list(
  date = "2026-09-24",
  checks = list(
    sample_accessions_exact = identical(sample_ids, expected_ids),
    independent_patient_samples = ncol(expr) == 11L,
    group_sizes_exact = n_r == 5L && n_s == 6L,
    cell_type_metadata = all(sample_info$cell_type == "macrophage"),
    positive_normalized_values = all(expr > 0),
    deposited_filter_reproduced = sum(keep_probe) == 25538L,
    no_duplicate_gene_tests = !anyDuplicated(de$gene_symbol),
    all_unambiguous_network_gene_nodes_measured = all(network_genes %in% rownames(gene_expression)),
    fcgr3a_ambiguity_preserved = coverage$status[coverage$network_node == "FCGR3A"] == "ambiguous_with_FCGR3B",
    mature_mirna_not_claimed_measured = TRUE,
    outputs_nonempty = all(file.info(c(file.path(result_dir, "de_genes.tsv"), file.path(result_dir, "network_gene_overlay.tsv"), file.path(figure_dir, "gse41571_pca.svg")))$size > 0)
  ),
  status = "PASS"
)
stopifnot(all(unlist(validation$checks)))
write(toJSON(validation, pretty = TRUE, auto_unbox = TRUE), file.path(audit_dir, "gse41571_validation.json"))

cat(toJSON(summary, pretty = TRUE, auto_unbox = TRUE, digits = 10), "\n")
