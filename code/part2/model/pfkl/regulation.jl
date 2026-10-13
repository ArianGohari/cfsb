module PFKRegulation

using Catalyst, ModelingToolkit, OrdinaryDiffEqTsit5, SciMLBase
export RN, simulate, exact_phase, phase_parameters, steady_check

# M: relative PFKL mRNA, E: relative PFKL protein. Baseline is 1 for both.
# Time is measured in protein lifetimes; gamma is the mRNA/protein decay ratio.
const RN = @reaction_network PFKRegulationModule begin
    @species M(t) E(t)
    @parameters gamma d k
    gamma, 0 --> M
    gamma * d, M --> 0
    k, M --> M + E
    1.0, E --> 0
end

const TEMPLATE = ODEProblem(
    RN, [RN.M => 1., RN.E => 1.], (0., 1.),
    [RN.gamma => 1., RN.d => 1., RN.k => 1.],
)
const IDX = [
    only(findall(x -> isequal(x, getproperty(RN, s)), unknowns(TEMPLATE.f.sys)))
    for s in (:M, :E)
]

"""Return decay and translation multipliers for a chosen residual protein level q."""
function phase_parameters(mechanism, q)
    0 < q <= 1 || throw(ArgumentError("q must be in (0,1]"))
    if mechanism == "decay"
        return (1 / q, 1.)
    elseif mechanism == "translation"
        return (1., q)
    end
    throw(ArgumentError("unknown mechanism"))
end

"""Analytical solution during one phase with constant parameters."""
function exact_phase(t, u, gamma, d, k)
    lambda = gamma * d
    steady_mrna = 1 / d
    mrna0, protein0 = u
    # Equal decay rates need the limit of the difference quotient.
    coupling = if isapprox(lambda, 1.; atol=1e-14, rtol=0)
        t * exp(-t)
    else
        (exp(-lambda * t) - exp(-t)) / (1 - lambda)
    end
    [
        steady_mrna + (mrna0 - steady_mrna) * exp(-lambda * t),
        k * steady_mrna + (protein0 - k * steady_mrna) * exp(-t) +
            k * (mrna0 - steady_mrna) * coupling,
    ]
end

function phase(u, gamma, d, k, times; abstol=1e-11, reltol=1e-9)
    initial = copy(TEMPLATE.u0)
    initial[IDX] = u
    problem = remake(
        TEMPLATE; u0=initial, tspan=(0., last(times)),
        p=[RN.gamma => gamma, RN.d => d, RN.k => k],
    )
    solution = solve(problem, Tsit5(); saveat=times, abstol, reltol)
    @assert SciMLBase.successful_retcode(solution)
    [value[IDX] for value in solution.u]
end

function steady_check(gamma, d, k)
    u = copy(TEMPLATE.u0)
    u[IDX] = [1 / d, k / d]
    problem = remake(TEMPLATE; u0=u, p=[RN.gamma => gamma, RN.d => d, RN.k => k])
    derivative = zeros(length(u))
    problem.f(derivative, u, problem.p, 0.)
    maximum(abs.(derivative))
end

"""Simulate temporary repression followed by recovery under baseline parameters."""
function simulate(mechanism, q, gamma, duration; abstol=1e-11, reltol=1e-9)
    gamma > 0 && duration > 0 || throw(ArgumentError("positive rates and duration required"))
    d, k = phase_parameters(mechanism, q)
    on = collect(range(0., duration; length=51))
    off = collect(range(0., 20 / min(gamma, 1.); length=201))
    repressed = phase([1., 1.], gamma, d, k, on; abstol, reltol)
    recovery = phase(last(repressed), gamma, 1., 1., off; abstol, reltol)
    expected_on = [exact_phase(t, [1., 1.], gamma, d, k) for t in on]
    expected_off = [exact_phase(t, last(expected_on), gamma, 1., 1.) for t in off]
    error = maximum(
        maximum(abs.(a .- b))
        for (a, b) in zip(vcat(repressed, recovery), vcat(expected_on, expected_off))
    )
    @assert error < 1e-7
    @assert maximum(abs.(last(repressed) .- first(recovery))) < 1e-12

    states = vcat(repressed, recovery[2:end])
    times = vcat(on, duration .+ off[2:end])
    @assert all(all(-1e-9 .<= state .<= 1 + 1e-9) for state in states)
    @assert maximum(abs.(last(states) .- 1)) < 1e-6
    @assert steady_check(gamma, d, k) < 1e-12
    if q == 1
        @assert maximum(maximum(abs.(state .- 1)) for state in states) < 1e-10
    end
    (times=times, states=states, error=error, endpoint=last(repressed), d=d, k=k)
end

end
