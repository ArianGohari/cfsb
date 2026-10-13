using SBMLToolkit, OrdinaryDiffEq, Plots

# Die Modellzeiteinheit ist eine Stunde.
file = joinpath(@__DIR__, "sbml", "BIOMD0000000170_url.xml")
sys = SBMLToolkit.readSBML(file, SBMLToolkit.ODESystemImporter())
prob = ODEProblem(sys, [], (0.0, 240.0), [])
# Die drei Zuweisungsregeln erzeugen algebraische Gleichungen (Massenmatrix).
sol = solve(prob, Rodas5P(); reltol=1e-8, abstol=1e-10, saveat=0.1)
@assert sol.t[end] == 240.0 "Simulation hat die Endzeit nicht erreicht: $(sol.retcode)"
@assert all(u -> all(isfinite, u), sol.u) "Simulation enthält nicht-endliche Werte"

# SBMLToolkit liefert Stoffmengen; die SBML-Stoffmengeneinheit ist nmol.
fig = plot(sol; idxs=[getproperty(sys, Symbol("y$i")) for i in 1:7],
    xlabel="Zeit (h)", ylabel="Stoffmenge (nmol)",
    label=["Per2/Cry-mRNA" "PER2/CRY Cyt." "PER2/CRY Kern" "Bmal1-mRNA" "BMAL1 Cyt." "BMAL1 Kern" "BMAL1 aktiv"],
    title="Weimann2004: circadianer Oszillator")
savefig(fig, joinpath(@__DIR__, "Weimann2004_simulation.svg"))
display(fig)
