using JSON3
include("regulation.jl")
using .PFKRegulation

function main()
    root = normpath(joinpath(@__DIR__, "../../../.."))
    out = joinpath(root, "output/part2/pfkl_regulation")
    mkpath(out)
    trajectories = []
    endpoints = []
    max_error = 0.
    tolerance_difference = 0.

    for mechanism in ["decay", "translation"],
        q in [.25, .5, .75, 1.], gamma in [.25, 1., 4.], duration in [.25, 1., 4.]

        scenario = simulate(mechanism, q, gamma, duration)
        max_error = max(max_error, scenario.error)
        for (time, state) in zip(scenario.times, scenario.states)
            push!(trajectories, (
                mechanism=mechanism, q=q, gamma=gamma, duration=duration,
                tau=time, mRNA=state[1], protein=state[2], activity_f0=state[2],
                activity_f50=.5 + .5 * state[2], activity_f90=.9 + .1 * state[2],
            ))
        end
        push!(endpoints, (
            mechanism=mechanism, q=q, gamma=gamma, duration=duration,
            mRNA_end=scenario.endpoint[1], protein_end=scenario.endpoint[2],
            protein_steady=q,
        ))
        if q == .5 && gamma == 1.
            tighter = simulate(mechanism, q, gamma, duration; abstol=1e-13, reltol=1e-11)
            difference = maximum(
                maximum(abs.(a .- b)) for (a, b) in zip(scenario.states, tighter.states)
            )
            tolerance_difference = max(tolerance_difference, difference)
        end
    end

    for (name, data) in [("trajectories.tsv", trajectories), ("endpoints.tsv", endpoints)]
        open(joinpath(out, name), "w") do io
            println(io, join(string.(keys(first(data))), '\t'))
            for row in data
                println(io, join(values(row), '\t'))
            end
        end
    end
    @assert tolerance_difference < 1e-7
    open(joinpath(out, "checks.json"), "w") do io
        JSON3.pretty(io, (
            cases=length(endpoints), max_analytic_error=max_error,
            tighter_tolerance_difference=tolerance_difference,
            checks=[
                "analytic phases incl repeated eigenvalue", "switch continuity",
                "off edge equilibrium", "nonnegative bounded states", "recovery", "stationary RHS",
            ],
            julia=string(VERSION),
            interpretation="Technical checks only; no biological validation or fitted human parameters.",
        ))
    end
    println(
        "Regulation scenarios: ", length(endpoints), "; analytic error ", max_error,
        "; tolerance difference ", tolerance_difference,
    )
end

main()
