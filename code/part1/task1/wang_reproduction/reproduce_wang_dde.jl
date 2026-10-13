#!/usr/bin/env julia

# Offline reproduction of selected Wang et al. results from Eq. (1), Table 1,
# Table 2 and section 3.3. No fitted or invented parameter values are used.
using SHA
using Printf

const OUT = @__DIR__
const SOURCE = normpath(joinpath(@__DIR__, "..", "sources", "wang_2022_p53_time_delay.pdf"))

const bp = 0.9
const bm = 0.9
const b0 = 1.0
const b = 1.0
const ap = 2.0
const am = 1.0
const amp = 1.4
const apm = 1.0
const apr = 1.8
const a0 = 0.5
const a = 1.0
const A = 0.15       # section 3.3 / Fig. 6, not the Table 1 default A=0.1
const K = 1.0e-5
const HISTORY = fill(0.1, 5)

G(P) = (A - P - K + sqrt((A - P - K)^2 + 4A*K)) / (2A)

function rhs(v, delayed_pc)
    p53, mdm2, m, pc, per = v
    return (
        bp - amp*mdm2*p53 - ap*p53,
        bm*p53 - apm*per*mdm2 - am*mdm2,
        b0*G(per) - apr*p53*m - a0*m,
        b*m - a*pc,
        b*delayed_pc - a*per,
    )
end

"""Fixed-step RK4 method of steps with linear interpolation of Pc(t-tau)."""
function simulate(tau; duration=800.0, dt=0.005)
    tau < dt && tau != 0.0 && error("tau must be zero or at least one time step")
    n = round(Int, duration/dt)
    y = fill(0.1, 5, n + 1)
    function delayed_pc(i, stage)
        tau == 0.0 && return nothing
        target = ((i - 1) + stage)*dt - tau
        target <= 0.0 && return HISTORY[4]
        x = target/dt
        left = floor(Int, x) + 1
        fraction = x - floor(x)
        left >= i + 1 && error("delay interpolation requested an unknown future value")
        return (1 - fraction)*y[4, left] + fraction*y[4, left + 1]
    end
    for i in 1:n
        v = @view y[:, i]
        if tau == 0.0
            k1 = rhs(v, v[4])
            v2 = v .+ dt .* k1 ./ 2
            k2 = rhs(v2, v2[4])
            v3 = v .+ dt .* k2 ./ 2
            k3 = rhs(v3, v3[4])
            v4 = v .+ dt .* k3
            k4 = rhs(v4, v4[4])
        else
            k1 = rhs(v, delayed_pc(i, 0.0))
            k2 = rhs(v .+ dt .* k1 ./ 2, delayed_pc(i, 0.5))
            k3 = rhs(v .+ dt .* k2 ./ 2, delayed_pc(i, 0.5))
            k4 = rhs(v .+ dt .* k3, delayed_pc(i, 1.0))
        end
        y[:, i + 1] = v .+ dt .* (k1 .+ 2 .* k2 .+ 2 .* k3 .+ k4) ./ 6
    end
    return collect(0.0:dt:duration), y
end

function amplitude(t, values; start)
    i = searchsortedfirst(t, start)
    return maximum(@view values[i:end]) - minimum(@view values[i:end])
end

function window_amplitude(t, values; start, stop)
    first = searchsortedfirst(t, start)
    last = searchsortedlast(t, stop)
    return maximum(@view values[first:last]) - minimum(@view values[first:last])
end

function periods(t, values; start)
    first = searchsortedfirst(t, start)
    peak_times = Float64[]
    for i in max(first, 2):(length(values) - 1)
        if values[i - 1] < values[i] && values[i] >= values[i + 1]
            push!(peak_times, t[i])
        end
    end
    return diff(peak_times)
end

function xml_escape(value)
    replace(string(value), "&" => "&amp;", "<" => "&lt;", ">" => "&gt;", "\"" => "&quot;")
end

function polyline(t, v, x0, y0, width, height, xmin, xmax, ymin, ymax; stride=20)
    points = String[]
    for i in 1:stride:length(t)
        xmin <= t[i] <= xmax || continue
        x = x0 + width*(t[i] - xmin)/(xmax - xmin)
        y = y0 + height*(1 - (v[i] - ymin)/(ymax - ymin))
        push!(points, @sprintf("%.2f,%.2f", x, y))
    end
    return join(points, " ")
end

function write_svg(path, zero_t, zero_y, long_t, long_y, scan)
    open(path, "w") do io
        write(io, """<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="760" viewBox="0 0 1100 760">
<rect width="1100" height="760" fill="white"/>
<style>text{font-family:Arial,sans-serif;fill:#222}.axis{stroke:#222;stroke-width:1}.grid{stroke:#ddd;stroke-width:1}.trace{fill:none;stroke:#2b6cb0;stroke-width:2}.points{fill:#c53030}.threshold{stroke:#c53030;stroke-width:2;stroke-dasharray:7 5}</style>
<text x="550" y="30" text-anchor="middle" font-size="21">Wang-DDE: Reproduktion ausgewählter Resultate</text>
<text x="70" y="62" font-size="16">A  PER2 ohne Verzögerung (A=0,15)</text>
<line class="axis" x1="70" y1="260" x2="1030" y2="260"/><line class="axis" x1="70" y1="80" x2="70" y2="260"/>
<polyline class="trace" points="$(polyline(zero_t, vec(zero_y[5,:]), 70,80,960,180,0,100,0.08,0.16;stride=10))"/>
<text x="70" y="300" font-size="16">B  PER2 bei Gesamtverzögerung 9 h</text>
<line class="axis" x1="70" y1="500" x2="1030" y2="500"/><line class="axis" x1="70" y1="320" x2="70" y2="500"/>
<polyline class="trace" points="$(polyline(long_t, vec(long_y[5,:]), 70,320,960,180,700,800,0,0.9;stride=10))"/>
<text x="70" y="540" font-size="16">C  Späte Peak-to-Peak-Amplitude nahe der Hopf-Schwelle</text>
<line class="axis" x1="70" y1="710" x2="1030" y2="710"/><line class="axis" x1="70" y1="560" x2="70" y2="710"/>
""")
        xmin, xmax, ymax = 0.125, 0.15, maximum(row.amplitude for row in scan)*1.1
        threshold_x = 70 + 960*(0.1396-xmin)/(xmax-xmin)
        write(io, @sprintf("<line class=\"threshold\" x1=\"%.2f\" y1=\"560\" x2=\"%.2f\" y2=\"710\"/>", threshold_x, threshold_x))
        for row in scan
            xmin <= row.tau <= xmax || continue
            x = 70 + 960*(row.tau-xmin)/(xmax-xmin)
            y = 560 + 150*(1-row.amplitude/ymax)
            write(io, @sprintf("<circle class=\"points\" cx=\"%.2f\" cy=\"%.2f\" r=\"5\"/>", x, y))
        end
        write(io, """<text x="1030" y="735" text-anchor="end" font-size="13">Verzögerung τ (h)</text>
<text x="82" y="580" font-size="12">gestrichelt: publiziertes τ₀=0,1396 h</text>
<text x="550" y="755" text-anchor="middle" font-size="12">RK4, dt=0,005 h; publizierte Gleichungen und Parameter; numerische Reproduktion</text>
</svg>
""")
    end
end

delays = [0.0, 0.13, 0.1390, 0.1395, 0.1400, 0.1410, 0.15]
scan = NamedTuple[]
for tau in delays
    duration = tau == 0.0 ? 800.0 : 5000.0
    t, y = simulate(tau; duration=duration)
    start = duration - 1000.0 < 0 ? duration/2 : duration - 1000.0
    late = amplitude(t, vec(y[5,:]); start=start)
    previous = duration >= 2000 ? window_amplitude(t, vec(y[5,:]); start=duration-2000, stop=duration-1000) : late
    push!(scan, (tau=tau, amplitude=late, previous_amplitude=previous,
        late_to_previous=previous == 0 ? 1.0 : late/previous, final=vec(y[:,end])))
end

zero_t, zero_y = simulate(0.0; duration=100.0)
long_t, long_y = simulate(9.0; duration=800.0)
late_periods = periods(long_t, vec(long_y[5,:]); start=400.0)
mean_period = sum(late_periods)/length(late_periods)

open(joinpath(OUT, "delay_scan.csv"), "w") do io
    println(io, "tau_h,previous_per2_amplitude,late_per2_amplitude,late_to_previous,final_p53,final_mdm2,final_per2_mrna,final_per2_cyt,final_per2_nuc")
    for row in scan
        @printf(io, "%.4f,%.10f,%.10f,%.10f,%.10f,%.10f,%.10f,%.10f,%.10f\n",
            row.tau, row.previous_amplitude, row.amplitude, row.late_to_previous, row.final...)
    end
end

open(joinpath(OUT, "tau9_timeseries.csv"), "w") do io
    println(io, "time_h,per2_nuclear")
    for i in 1:20:length(long_t)
        @printf(io, "%.4f,%.10f\n", long_t[i], long_y[5,i])
    end
end

write_svg(joinpath(OUT, "wang_dde_reproduction.svg"), zero_t, zero_y, long_t, long_y, scan)

equilibrium = scan[1].final
result = """{
  "source_pdf": "sources/wang_2022_p53_time_delay.pdf",
  "source_sha256": "$(bytes2hex(sha256(read(SOURCE))))",
  "model": "Wang et al. Eq. (1); total delay assigned to nuclear PER2 import as in Table 2",
  "solver": "fixed-step classical RK4 method of steps with linear delayed-state interpolation",
  "dt_h": 0.005,
  "activator_A": 0.15,
  "published_tau0_h": 0.1396,
  "numerical_transition_bracket_h": [0.1395, 0.1400],
  "equilibrium_tau0": [$(join((@sprintf("%.10f", x) for x in equilibrium), ", "))],
  "published_equilibrium": [0.3725, 0.2973, 0.1276, 0.1276, 0.1276],
  "tau9_mean_period_h": $(@sprintf("%.6f", mean_period)),
  "tau9_period_count": $(length(late_periods)),
  "limitations": [
    "This reproduces selected deterministic model outputs, not experimental measurements.",
    "The bifurcation threshold is bracketed by long simulations; continuation and eigenvalue calculations from the paper were not reimplemented.",
    "The split among tau1, tau2 and tau3 is not identifiable from the reported total-delay analysis; Table 2 places the total delay in the nuclear-import equation."
  ]
}
"""
write(joinpath(OUT, "results.json"), result)

@printf("equilibrium = [%s]\n", join((@sprintf("%.6f", x) for x in equilibrium), ", "))
@printf("transition bracket = [0.1395, 0.1400] h; published 0.1396 h\n")
@printf("tau=9 h mean late period = %.4f h (%d intervals)\n", mean_period, length(late_periods))
