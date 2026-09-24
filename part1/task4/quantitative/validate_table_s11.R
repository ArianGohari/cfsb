#!/usr/bin/env Rscript

suppressPackageStartupMessages(library(jsonlite))

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1) stop("Usage: validate_table_s11.R <output_dir>")
output_dir <- args[[1]]
required <- c(
  "sample_metadata.tsv", "table_s11_differential.tsv", "sensitivity_summary.tsv",
  "table_s11_volcano.svg", "table_s11_volcano.png", "table_s11_summary.json"
)
stopifnot(all(file.exists(file.path(output_dir, required))))

samples <- read.delim(file.path(output_dir, "sample_metadata.tsv"), check.names = FALSE)
results <- read.delim(file.path(output_dir, "table_s11_differential.tsv"), check.names = FALSE)
sensitivity <- read.delim(file.path(output_dir, "sensitivity_summary.tsv"), check.names = FALSE)
summary <- fromJSON(file.path(output_dir, "table_s11_summary.json"))

stopifnot(nrow(samples) == 6, identical(as.character(samples$condition), rep(c("mock", "treated"), 3)))
stopifnot(nrow(results) == 8768, !anyDuplicated(results$accession), all(is.finite(results$difference_normalized)))
stopifnot(nrow(sensitivity) == 2, sensitivity$fdr_bh_lt_0_05[[1]] == sum(results$fdr_bh < 0.05))
stopifnot(summary$input$exact_accession_matches == 8759)
svg_text <- readChar(file.path(output_dir, "table_s11_volcano.svg"), file.info(file.path(output_dir, "table_s11_volcano.svg"))$size)
stopifnot(grepl("<svg", svg_text, fixed = TRUE))
cat("PASS: Table S11 analysis outputs are internally consistent\n")
