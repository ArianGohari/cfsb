# Summer Term 2026 - Computational (Food) Systems Biology

Institut für Informatik  
Praktische Informatik und Bioinformatik  
Prof. Dr. Ralf Zimmer  
Dr. Evi Sinn, Chuqiao Pan

> [Handwritten note at the top right of page 1, uncertain transcription: "Adrien bolovi Milde (Zwiebel)".]

## Assignments 2026 Project

### Systems models for interpreting system-wide experimental data and for checking out myths and facts about nutrition studies and (personalized) nutrition recommendations / diets

**Working period:** Four weeks (1.7.-30.7.2026)  
Hand-in anytime per moodle  
Please hand-in only reproducible results, answers, figures, tables, simulations, ...  
**Due July 30, 2026**  
**Written and oral exam:** Thu, 30.7.2026, 10-12

## Comprehensive systems models for interpreting large scale high-throughput data on nutrition and nutrition studies

The project will use (the) method discussed in the lecture to investigate whether there are systems biology methods, data and models for your favourite food or food ingredient.

## Part I

Tasks 1-3 apply dynamical systems models to make or validate precise quantitative biological predictions.

Many papers use systems models to support biological hypotheses and provide additional evidence. Often only a sketch (from a textbook or paper is given). Then the system has to be derived from the sketch. Parameters need to be specified, or learned from some data, or extracted from appropriate databases (maybe different versions for diverse contexts), or modifications need to be made to ready-made available systems models.

The solution of such models (and the visualisation of the results) depends on 1.) the specification of the model (i.e. are all rate constants and dependencies specified such that a (system of) ODE(s) can be fully stated and solved via integration, or is a partial model given such that only a crude partial simulation is possible) 2.) modelling choices (is a continuous time-resolved behaviour wanted, or the states in predefined discrete steps, the final states in a number of discrete conditions, the final outcome after convergence, the steady-state-behaviour, attractors, oscillations, ...) 3.) the methodological framework: ODE solvers, numerical solutions, stochastic simulation, Petri net semantics.

Simulations and solutions of dynamical systems models produce visualisations to provide additional evidence for biological hypotheses. But major problems are uncertain parameters, robustness of models and results, reproducibility of outcomes, and missing factors and incomplete models.

There are many databases around which collect prepared models in various formats (e.g. BioModels, https://www.ebi.ac.uk/biomodels). There are also many tools, which allow to specify reaction systems, both general (e.g. matlab, octave) or special (e.g. Gepasi, Copasi, CellDesigner, ...) modelling tools.

## Applications of dynamical systems

### Task 1 Circadian clocks and cancer

Several papers and reviews have been published to propose a close connection between key circadian clock genes (such as CLK:BMAL1, Per2) and key cancer genes (e.g. p53 and MDM2). Both, circadian rhythms and cancer checkpoint regulation are well-studied processes with a wide variety of models and experimental evidence. Surprisingly, there is also mounting evidence close interconnection of the two processes via key well-known molecular factors.

This project reviews the models and the interconnections, resolves the chain of experimental data and facts and theoretical models, and tries to reproduce certain hypotheses and claims.

(a) Start with the review [^1] and summarize the facts.

(b) Several network and dynamical models are proposed or reviewed in the paper. Discuss the models and whether there are conflicting hypotheses.

(c) The authors of the review have published several papers about the topic

- Selfridge JM, Gotoh T, Schiffhauer S, et al. Chronotherapy: Intuitive, Sound, Founded ... But Not Broadly Applied. Drugs. 2016;76(16):1507-1521. doi:10.1007/s40265-016-0646-4
- Liu J, Zou X, Gotoh T, et al. Distinct control of PERIOD2 degradation and circadian rhythms by the oncoprotein and ubiquitin ligase MDM2. Sci Signal. 2018;11(556):eaau0715. Published 2018 Nov 13. doi:10.1126/scisignal.aau0715
- Gotoh T, Vila-Caballer M, Liu J, Schiffhauer S, Finkielstein CV. Association of the circadian factor Period 2 to p53 influences p53's function in DNA-damage signaling. Mol Biol Cell. 2015;26(2):359-372. doi:10.1091/mbc.E14-05-0994
- Gotoh T, Vila-Caballer M, Santos CS, Liu J, Yang J, Finkielstein CV. The circadian factor Period 2 modulates p53 stability and transcriptional activity in unstressed cells. Mol Biol Cell. 2014;25(19):3081-3093. doi:10.1091/mbc.E14-05-0993

Review the progression of findings and models.

(d) The paper reviews the findings concerning the interconnection of circadian rhythms and cancer. Sketch the historical findings and facts about this connection from the published literature in addition to the publications from the Finkielstein lab. Who and which paper claims of ahs the priority for certain facts. Have the facts been reproduced or falsified later on?

(e) The paper [^2] proposes a (new?) time-delayed model about circadian and cancer processes and the relation between Per2 and p53 in particular. What is the new contribution of this paper?

(f) What is known about the pathways in pathway databases such as BioModels, KEGG, or ConsensusPathDB? Anything about the connection of the two processes?

(g) To obtain complete information about the facts and relations of participating genes and proteins in the pathways a systematic text mining could be considered. This involves prescreening of relevant publications and, then, a systematic information extraction from the papers.

### Task 2 Parameter estimation of dynamical models

Typically, models obtained from the literature are not fully parametrized. In addition the actual parameters might depend on the respective condition and cellular context.

The paper [^3] claims to obtain a reasonable parametrisation of large-scale mechanistic models via a highly efficient computational method. Explain the setup and the used method. Why does it achieve and guarantee a 10.000-fold speedup? For what purpose can the resulting model be used? What are the predicted outcomes and what are the evidences for their validity.

The publication ([^4] employs the method to predict drug responses for cancer treatment including combination therapies. Discuss the approach and the results.

### Task 3 Petri Netze, PNFL, SBML, BioModels

SBML (https://sbml.org) is "a free and open interchange format for computer models of biological processes. SBML is useful for models of metabolism, cell signalling, and more" and constitutes a whole toolset of libraries, tools, editors, simulators, etc. including APIs and language bindings for several programming environments including python.

The BioModels resource (https://www.ebi.ac.uk/biomodels/) at EMBL-EBI provides thousands of curated and non-curated models, mainly based on ODEs from a variety of research, papers, and pathways. BioModels aims to provide a comprehensive collection of "existing literature-based physiologically and pharmaceutically relevant mechanistic models in standard formats. Our mission is to provide the systems modelling community with reproducible, high-quality, freely-accessible models published in the scientific literature."

Petri Nets in particular PNFL system are our implementation of pathway models. Yo have already build your own PNFL framework (based on our templates). You can use standard (SBM) models or PNFL to generate and construct pathway models to check for possible miRNA regulation. YOu can alo build on the modells collected in our OPNFL knowledge base. Please ask the tutors for more information on the PNFL collection and its usage.

Otherwise, you can start from scratch and

(a) Install SBML and make use of SBML tools and the access to BioModels.

(b) make a statistic about the models and pathways! Which pathway is covered by the most models? Which model touches on the most pathways.

(c) Checkout the key proteins from Task 1. Are there models containing these proteins? Can the models contribute to the hypotheses and claims of Task 1?

## Comprehensive systems models

The following projects try to build as comprehensive and as detailed as possible models of specific cellular systems for further use in model analysis (FBA, invariants) and interpretation of high throughput transcriptomic and proteomic data.

The goal is to produce useful network models for the respective purposes, but also to investigate methods to obtain such models from databases and literature (beyond manual collection and curation). This involves information extraction methods and data structures to represent such models.

For various purposes different types of information and networks need to be represented: (a) metabolic networks (enzymes transforming sets of substrates into sets of products) (b) regulatory networks (TF - target gene interactions) (c) signalling cascades (signal transmission via protein interactions or protein modifications (e.g. phosphorylations). In addition to these three major types, there are also specialised networks such as miRNA-target interactions, protein complexes, phosphorylations, epigenetic modifications, binding sites, splicing, ...

The most simple type of network are interaction networks, where interactions represent some connection between the two objects (typically of unknown function and unknown interaction type not to speak of dynamics). A very common rudimentary type are sets of objects somehow belonging to a certain class of genes/proteins, which probably belong to or contribute in some way to a common function or pathway (e.g. gene ontology (GO) sets and similar gene set definitions and databases). The common use of these 'ontology' or 'functional' sets (Molecular Function (MF), Biological Process (BP), Cellular Component (CC)) is to compute for expression data some enriched sets with the idea that the represented process is somehow regulated in the investigated system (over-representation analysis (ORA), gene set enrichment analysis (GSEA)). The identified sets should be more meaningful and interpretable than long lists of individual objects and, at the same time, more robust against fluctuations and noise in the data and sensitivities of the data analysis.

For this purpose a number of functional sets and ontologies have been defined and collected in databases. This includes the Gene Ontology (GO) with its three subdivisions ML/BP/CC, pathway databases such as KEGG, Reactome, WikiPathways, and also collections of ontology-based or experimentally derived sets of molecular/gene/protein/disease biomarkers database (such as MsigDB, GenSigDB, ...) which are indicative for certain cell-types, cellular states, diseases ...

Typically set and pathways definitions are not immediately appropriate for the problem and data at hand. Moreover the definitions are not context-specific, i.e. not tailored for a specific cell types, cell state, tissue or disease type. E.g. only rarely it is known or annotated that certain interactions or regulations occur only in specific contexts but not in others. Of course any knowledge on this context-specificity is essential for the use of systems models to explain experimental data or even for doing straight-forward validation checks with the use of the systems models. This applies even more for pathway data and hampers the usefulness of pathway and network enrichment methods (e.g. gene graph enrichment analysis (GGEA)).

One particular important context is the model systems, i.e. it is not clear whether and to which extent data and models from animals or cell-lines or sorted cells or single-cells can be transferred to the real human situation, say in patients.

Often different data types (e.g. sequencing data (expression, translation, regulation), mass spec data, binding data, epigenomics data) need to be integrated and be interpreted with the help of systems models and networks and functional classes.

Often different stages of a system (developmental stages, disease progression, time series after treatment, infection, perturbation...).

Moreover, different systems have been measured, e.g. 'bulk' data from tissues, data from sorted cells (ideally just one cell type or one cell type in one particular state), single cell data, ...

Sometimes spatial information is available which can be combined with microscopy and physiological data.

Very often, experiments are performed on model systems as experimentation with human cells or patients is not possible. Therefore, wild-type, genetically modified or knock-out animals are used for data generation. Large-scale experiments are mostly done on cell-lines, which are more homogeneous and much easier and cheaper to work with.

All of these issues could be addressed, but should certainly be kept in mind in collecting systems model data on various systems. In the following, projects will review the resources for the respective systems, collect network data from the available resources, curate the derived data, and prepare 'systems models' for the interpretation of experimental high-throughput data and the visualisation of results.

### Task 4 Human cell lines

As an example of a human cell line, this project investigates the human colon epithelial carcinoma cell line **Caco-2** for the interpretation of COVID-19 / SARS-CoV-2 proteomics data. Here general information and systems models should be derived, but maybe also distinguished context-specific information on the **Caco-2** cell line in contrast to other human cell lines.

### Task 5 Human Macrophages, monocytes, neutrophils

For the interpretation of SFB1123 data on atherosclerosis and coronary artery diseases (CAD) systems models and information on artery plaque and the involved cell-types are required. The project focusses on one of the most prominent cell types, i.e. macrophages which play an important rule in the disease aetiology and progression. Several data types have been measured, bulk data, sorted cell data, cell-type data, single cell data, miRNA data, mass spec data, microscopy pictures, and spatially resolved data. microRNAs are important post-translational regulators, which are hypothesed to play an important role in various disease processes. Specialised resources on miRNA and their targets have been compiled.

### Task 6 Mouse Macrophages, monocytes, neutrophils

Repeat Task 5 for the respective mouse cells and tissues. In particular, it is interesting to investigate specific differences and similarities between the mouse and human systems.

## Part II

If methods could not be used, e.g. detailed deterministic dynamics, it should be discussed what the issues with the practical application are (the interaction might not be known, the actual parameters of the dynamics have not or cannot be measured, the necessary data to fit the (parameters of the) model is not available, etc.)

In particular one would like to check the (differential) effect of food intake on the gene and protein expression tpattern of your favourite cell type, i.e. on macrophages, monocytes, or neutrophils looked at in Part I.

In the lecture we discussed quite many nutrition "hypotheses" and diet recommendations, which could be investigated with our systems biology methods. Maybe, you select a application scenario from the recent collection of studies reviewed in Spektrum der Wissenschaft (2025, see also the link in moodle or the web-page).[^5]

But, in principle, you could also choose your favourite food, such as wheat (celiac disease), leguminoses (pea, beans, ... as new protein source), potato, tomato, onion, coffee, tea ... But, as a starting point have a look at the mentioned study reports and studies ... or at the books mentioned in the lecture[^6] or the references mentioned therein[^7].

In Part I you worked on building (systems) models and collected available facts, network data and hypotheses for specific cellular systems. Now, you should search for interesting target systems (models) which could be influenced via food ingredients and the effect of which could be measured with transcriptomics or proteomics methods. The main focus lies on miRNA regulatory systems and the proposed pipeline for food systems biology analyses, also as miRNA and other non-coding RNA molecules are interesting players in the developing new research field of RNA medicine[^8].

In this project these models and networks will/should be used to analyse, interpret and validate high throughput transcriptomics and proteomics data. They will serve to generate hypotheses which could (eventually, when data is available)) will be checked against the data. You have to search for relevant data, there is lots of data sets available, but maybe not that easy to identify via the available metadata. In principle, most datasets are available in processed form (counts via the recount3 database[^9]. A particular focus is to analyse miRNA:target networks effecting gene expression due to regulated human miRNAs or miRNAs taken up via the food. First, you have to collect miRNA for your food in question either from miRNA databases, from genomic resources or from the literature (reviews such as [^10], [^11]) or literature on specific plants or fungi (see/search PubMed!) or from specific food-related databases (i.e. the dietary miRNA DB [^12]).

The goal is to produce useful network models for the respective purposes, but also to investigate methods to obtain such models from databases and literature (beyond manual collection and curation). This involves information extraction methods and data structures to represent such models.

For various purposes different types of information and networks need to be represented: (a) metabolic networks (enzymes transforming sets of substrates into sets of products) (b) regulatory networks (TF - target gene interactions) (c) signalling cascades (signal transmission via protein interactions or protein modifications (e.g. phosphorylations). In addition to these three major types, there are also specialised networks such as miRNA-target interactions, protein complexes, phosphorylations, epigenetic modifications, binding sites, splicing, ... In particular, in the Part 2 we focus on miRNA:target (and if possible TF:target) networks and the effects on mRNA/gene/transcript expression (RNASeq measurements).

The most simple type of network are interaction networks, where interactions represent some connection between the two objects (typically of unknown function and of unknown interaction type, and, most often of unknown dynamics). A very common rudimentary type are sets of objects somehow belonging to a certain class of genes/proteins, which probably belong to or contribute in some way to a common function or pathway (e.g. gene ontology (GO) sets and similar gene set definitions and databases). The common use of these 'ontology' or 'functional' sets (Molecular Function (MF), Biological Process (BP), Cellular Component (CC)) is to compute, for expression data, some enriched sets with the idea that the represented process is somehow regulated in the investigated system (given some or several types of multi-omics data via over-representation analysis (ORA) or gene set enrichment analysis (GSEA)). The identified sets should be more meaningful and interpretable than long lists of individual objects and, at the same time, more robust against fluctuations and noise in the data and sensitivities of the data analysis.

For this purpose a number of functional sets and ontologies have been defined and collected in databases. This includes the Gene Ontology (GO) with its three subdivisions ML/BP/CC, pathway databases such as KEGG, Reactome, WikiPathways, and also collections of ontology-based or experimentally derived sets of molecular/gene/protein/disease biomarkers database (such as MsigDB, GenSigDB, ...), which are indicative for certain cell-types, cellular states, diseases ... Many and quite comprehensive (meta-)databases on interaction and regulatory relations are available: we learned about the GIN database[^13] and its conversion into Petri nets[^14]. In addition, many long-term maintained databases are available as resources (Yeastract, ISMARA, BioGrid, ConsensusPathDB[^15], Pathway Commons[^16]), several of them including extensive documentation on formats (SBML, BioPAX), workflows, and analysis/visualization tools[^17].

Typically, set and pathways definitions are not immediately appropriate for the problem and data at hand. Moreover, the definitions are not context-specific, i.e. not tailored for specific cell types, cell states, tissues or disease types. E.g. only rarely it is known or annotated that certain interactions or regulations occur only in specific contexts but not in others. Here proprietary project data comes into play which have to be analysed in the context of additional public data and systems knowledge. Of course any knowledge on this context-specificity is essential for the use of systems models to explain experimental data or even for doing straight-forward validation checks with the use of the systems models. This applies even more for pathway data and (sometimes) hampers the usefulness of pathway and network enrichment methods (e.g. gene graph enrichment analysis (GGEA) and, on the other hand, makes them the more necessary).

One particular important context are the "model" systems (typically animals serving as model for the human case). I.e. it is not clear whether and to which extent data and models from animals or cell-lines or sorted cells or single-cells can be transferred to the real human situation, say in patients or healthy humans.

For the (differential) analysis of such multi-omics data lots of tools have been developed also in our research group such as Fuzzifier, Flowsets, EmpireS, Ideas, ...

Often different multi-omics data types (e.g. sequencing (expression, translation, regulation), mass spec/proteomics, binding, and epigenomics data) need to be integrated and be interpreted with the help of systems models and networks and functional classes.

- Often different stages of a system (developmental stages, disease progression, time series after treatment, infection, perturbation...) can and need to be modeled via differential analysis along the series.
- Moreover, different systems have been measured, e.g. 'bulk' data from tissues, data from sorted cells (ideally just one cell type or one cell type in one particular state), single cell data, ...
- Sometimes spatial information is available, which can be combined with microscopy and physiological data.
- Very often, experiments are performed on model systems as experimentation with human cells or patients is not possible. Therefore, genetically modified and knock-out animals are used for data generation. Large-scale experiments are mostly done on cell-lines, which are more homogeneous and much easier and cheaper to work with.

All of these issues could be addressed, but should certainly be kept in mind in collecting systems model data on various systems. In the following, projects will review the resources for the respective systems, collect network data from the available resources, curate the derived data, and prepare 'systems models' for the interpretation of experimental high-throughput data and the visualisation of results.

## References and footnotes

[^1]: Zou Xianlin, Kim Dae Wook, Gotoh Tetsuya, Liu Jingjing, Kim Jae Kyoung, Finkielstein Carla V., A Systems Biology Approach Identifies Hidden Regulatory Connections Between the Circadian and Cell-Cycle Checkpoints. *Frontiers in Physiology*, 11, 327, 16.4.2020, https://doi.org/10.3389/fphys.2020.00327

[^2]: Wang C, Liu H, Miao Z, Zhou J. Circadian Rhythm Regulated by Tumor Suppressor p53 and Time Delay in Unstressed Cells. *IEEE/ACM Trans Comput Biol Bioinform.* 2022 May-Jun;19(3):1523-1530. doi: 10.1109/TCBB.2020.3040368. Epub 2022 Jun 3. PMID: 33232245.

[^3]: Fabian Fröhlich, Thomas Kessler, Daniel Weindl, Alexey Shadrin, Leonard Schmiester, Hendrik Hache, Artur Muradyan, Moritz Schütte, Ji-Hyun Lim, Matthias Heinig, Fabian J. Theis, Hans Lehrach, Christoph Wierling, Bodo Lange, Jan Hasenauer, Efficient Parameter Estimation Enables the Prediction of Drug Response Using a Mechanistic Pan-Cancer Pathway Model, *Cell Systems*, Volume 7, Issue 6, 2018, Pages 567-579.e6.

[^4]: Schmucker R, Farina G, Faeder J, Fröhlich F, Saglam AS, Sandholm T (2021), Combination treatment optimization using a pan-cancer pathway model. *PLoS Comput Biol.* 17(12):e1009689. https://doi.org/10.1371/journal.pcbi.1009689

[^5]: https://syncandshare.lrz.de/getlink/fiBrqhuRYNfdS7g8MLcibb/Spektrum-Kompakt-17-2025.pdff

[^6]: M Greger, *How not to age*, Pan Macmillan, 2023; B. Kast, *Der Ernährungskompass*, Penguin, 2022; T. Spector, *Die Wahrheit über unser Essen*, DuMont, 2022

[^7]: nutritionfacts.org/book/how-not-to-age/citations

[^8]: E. Grabar and U. Bahnsen, *Das Ende aller Leiden. Wie RNA-Therapien die Behandlung von Krebs, Herzkrankheiten und Infektionen revolutionieren*, Quadriga, 2022

[^9]: https://rna.recount.bio/

[^10]: DeLucas M, Sanchez J, Palou A, Serra F. The Impact of Diet on miRNA Regulation and Its Implications for Health: A Systematic Review. *Nutrients.* 2024 Mar 7;16(6):770. doi: 10.3390/nu16060770. PMID: 38542682; PMCID: PMC10975402.

[^11]: Lin Zhang, Ting Chen, Yulong Yin, Chen-Yu Zhang, Yong-Liang Zhang, Dietary microRNA, A Novel Functional Component of Food, *Advances in Nutrition*, Volume 10, Issue 4, 2019, Pages 711-721, https://doi.org/10.1093/advances/nmy127.

[^12]: Chiang K, Shu J, Zempleni J, Cui J. Dietary MicroRNA Database (DMD): An Archive Database and Analytic Tool for Food-Borne microRNAs. *PLoS One.* 2015 Jun 1;10(6):e0128089. doi: 10.1371/journal.pone.0128089. PMID: 26030752; PMCID: PMC4451068.

[^13]: Chang X, Yan S, Zhang Y, Zhang Y, Li L, Gao Z, Lin X, Chi X. GINv2.0: a comprehensive topological network integrating molecular interactions from multiple knowledge bases. *NPJ Syst Biol Appl.* 2024 Jan 13;10(1):4. doi: 10.1038/s41540-024-00330-y. PMID: 38218959; PMCID: PMC10787761.

[^14]: Lin X, Chang X, Zhang Y, Gao Z, Chi X. Automatic construction of Petri net models for computational simulations of molecular interaction network. *NPJ Syst Biol Appl.* 2024 Nov 9;10(1):131. doi: 10.1038/s41540-024-00464-z. PMID: 39521772; PMCID: PMC11550427.

[^15]: http://cpdb.molgen.mpg.de/: (2020 counts!, please update to 2025!) unique physical entities: 172,559 unique interactions: 660,318 gene regulations: 17,447 protein interactions: 448,725 genetic interactions: 4,793 biochemical reactions: 23,487 drug-target interactions: 165,866 pathways: 5,436

[^16]: Rodchenkov, I, et al., Pathway Commons 2019 Update: integration, analysis and exploration of pathway data, *Nucleic Acids Research*, Volume 48, Issue D1, p. D489-D497, https://doi.org/10.1093, https://www.pathwaycommons.org/, Version 12 (2020, please update to 2025!): 5,772 Pathways - 2,424,055 Interactions - 22 Databases.

[^17]: https://www.pathwaycommons.org/guide/
